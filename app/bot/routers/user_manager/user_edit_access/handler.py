import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.db import get_all_users, get_all_servers, get_user_by_id, get_servers_for_user
from app.db.crud import add_user_server_access, remove_user_server_access
from app.db import AsyncSessionLocal
from app.bot.filters.is_admin import IsAdmin
from .fsm import EditAccessState
from .keyboard import users_select_keyboard, rights_select_keyboard
from app.bot.routers.user_manager.handler import show_user_manager_menu
from app.bot.tasks.user_sync import sync_all_users_on_servers
    
logger = logging.getLogger("edit_access")
router = Router()

def get_rights_text(user, servers, selected_server_ids, is_admin, access_all):
    text = "<b>Select access for the user:</b>\n"
    if is_admin:
        text += "<b>Admin</b> will have access to all servers.\n"
    elif access_all:
        text += "User will have access to all servers.\n"
    elif selected_server_ids:
        names = [f"<b>{s.name}</b>" for s in servers if s.id in selected_server_ids]
        text += "User will have access to: " + (", ".join(names) if names else "None") + "\n"
    else:
        text += "No servers selected.\n"
    text += "\nℹ️ <i>If you remove all access, all peers for this user will be deleted.</i>"
    return text

@router.callback_query(IsAdmin(), F.data == "user_manager_edit_access")
async def edit_access_start(callback: CallbackQuery, state: FSMContext):
    users = await get_all_users()
    await state.clear()
    await state.set_state(EditAccessState.select_user)
    await callback.message.edit_text(
        "Select a user to edit access:",
        reply_markup=users_select_keyboard(users, callback.from_user.id),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), StateFilter(EditAccessState.select_user), F.data.startswith("edit_access_select_"))
async def edit_access_select_user(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("edit_access_select_", ""))
    user = await get_user_by_id(user_id)
    if user.tg_id == callback.from_user.id:
        await callback.answer("You cannot edit your own access.", show_alert=True)
        return
    servers = await get_all_servers()
    servers_for_user = await get_servers_for_user(user_id)
    is_admin = getattr(user, "is_admin", False)
    access_all = len(servers_for_user) == len(servers)
    await state.set_state(EditAccessState.select_rights)
    await state.update_data(
        edit_user_id=user_id,
        is_admin=is_admin,
        selected_servers=servers_for_user if not is_admin else [],
        access_all=access_all
    )
    await callback.message.edit_text(
        get_rights_text(user, servers, servers_for_user, is_admin, access_all),
        reply_markup=rights_select_keyboard(servers, servers_for_user, is_admin, access_all, is_admin),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), StateFilter(EditAccessState.select_user), F.data == "edit_access_back")
async def edit_access_back_to_manager(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    # Всегда запрашиваем свежие данные и новую сессию
    from app.bot.routers.user_manager.handler import show_user_manager_menu
    import aiohttp
    async with aiohttp.ClientSession() as session:
        await show_user_manager_menu(callback, session=session)

@router.callback_query(IsAdmin(), StateFilter(EditAccessState.select_rights), F.data == "edit_access_toggle_admin")
async def edit_access_toggle_admin(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    is_admin = not data.get("is_admin", False)
    servers = await get_all_servers()
    user = await get_user_by_id(data["edit_user_id"])
    selected_servers = data.get("selected_servers", [])
    access_all = data.get("access_all", False)
    await state.update_data(is_admin=is_admin)
    await callback.message.edit_text(
        get_rights_text(user, servers, selected_servers, is_admin, access_all),
        reply_markup=rights_select_keyboard(servers, selected_servers, is_admin, access_all, is_admin),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), StateFilter(EditAccessState.select_rights), F.data == "edit_access_toggle_all")
async def edit_access_toggle_all(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    servers = await get_all_servers()
    user = await get_user_by_id(data["edit_user_id"])
    is_admin = data.get("is_admin", False)
    access_all = not data.get("access_all", False)
    selected_servers = [s.id for s in servers] if access_all else []
    await state.update_data(access_all=access_all, selected_servers=selected_servers)
    await callback.message.edit_text(
        get_rights_text(user, servers, selected_servers, is_admin, access_all),
        reply_markup=rights_select_keyboard(servers, selected_servers, is_admin, access_all, is_admin),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), StateFilter(EditAccessState.select_rights), F.data.startswith("edit_access_toggle_server_"))
async def edit_access_toggle_server(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    servers = await get_all_servers()
    user = await get_user_by_id(data["edit_user_id"])
    is_admin = data.get("is_admin", False)
    access_all = data.get("access_all", False)
    server_id = int(callback.data.replace("edit_access_toggle_server_", ""))
    selected = set(data.get("selected_servers", []))
    if server_id in selected:
        selected.remove(server_id)
    else:
        selected.add(server_id)
    await state.update_data(selected_servers=list(selected), access_all=(len(selected) == len(servers)))
    await callback.message.edit_text(
        get_rights_text(user, servers, list(selected), is_admin, len(selected) == len(servers)),
        reply_markup=rights_select_keyboard(servers, list(selected), is_admin, len(selected) == len(servers), is_admin),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), StateFilter(EditAccessState.select_rights), F.data == "edit_access_confirm")
async def edit_access_confirm(callback: CallbackQuery, state: FSMContext):
    from app.db.models import UserServerAccess
    from sqlalchemy import delete
    import aiohttp
    data = await state.get_data()
    user_id = data["edit_user_id"]
    is_admin = data.get("is_admin", False)
    selected_servers = data.get("selected_servers", [])
    access_all = data.get("access_all", False)
    servers = await get_all_servers()
    user = await get_user_by_id(user_id)
    changed = False
    if user.is_admin != is_admin:
        async with AsyncSessionLocal() as session:
            db_user = await session.get(type(user), user_id)
            db_user.is_admin = is_admin
            await session.commit()
        changed = True
        logger.info(f"User {user_id} admin status changed to {is_admin} by {callback.from_user.id}")
    if is_admin:
        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(UserServerAccess).where(UserServerAccess.user_id == user_id)
            )
            for server in servers:
                access = UserServerAccess(user_id=user_id, server_id=server.id)
                session.add(access)
            await session.commit()
        logger.info(f"User {user_id} granted access to all servers by {callback.from_user.id}")
        changed = True
    else:
        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(UserServerAccess).where(UserServerAccess.user_id == user_id)
            )
            for server_id in selected_servers:
                access = UserServerAccess(user_id=user_id, server_id=server_id)
                session.add(access)
            await session.commit()
        logger.info(f"User {user_id} access set to servers {selected_servers} by {callback.from_user.id}")
        changed = True
    await state.clear()

    async with aiohttp.ClientSession() as session:
        await sync_all_users_on_servers(session)
        if changed:
            await callback.answer("✅ User updated!")
        else:
            await callback.answer("No changes made.")
        await show_user_manager_menu(callback, session=session)

@router.callback_query(IsAdmin(), StateFilter(EditAccessState.select_rights), F.data == "edit_access_cancel")
async def edit_access_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from app.bot.routers.user_manager.handler import show_user_manager_menu
    import aiohttp
    async with aiohttp.ClientSession() as session:
        await show_user_manager_menu(callback, session=session)