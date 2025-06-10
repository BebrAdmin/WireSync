import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.db import get_all_users, get_user_by_id, get_servers_for_user, get_all_servers
from app.db import AsyncSessionLocal
from app.bot.filters.is_admin import IsAdmin
from .fsm import DeleteUserState
from .keyboard import users_select_keyboard, confirm_delete_keyboard
from app.bot.routers.user_manager.handler import show_user_manager_menu
from app.bot.tasks.user_sync import sync_all_users_on_servers

logger = logging.getLogger("user_delete")
router = Router()

async def get_delete_text(user_id):
    user = await get_user_by_id(user_id)
    user_server_ids = await get_servers_for_user(user.id)
    all_servers = await get_all_servers()
    servers_text = (
        ", ".join([f"{s.name}" for s in all_servers if s.id in user_server_ids])
        if user_server_ids else "-"
    )
    phone = getattr(user, "phone", None) or "-"
    user_info = (
        f"ID: {user.tg_id}\n"
        f"Email: {user.email or '-'}\n"
        f"Phone: {phone}\n"
        f"Access to servers: {servers_text}"
    )
    text = (
        "<b>Are you sure you want to delete this user?</b>\n"
        f"<blockquote>{user_info}</blockquote>\n"
        "\nℹ️ <i>All user data and peers will be removed!</i>"
    )
    return text

@router.callback_query(IsAdmin(), F.data == "user_manager_delete_user")
async def user_delete_start(callback: CallbackQuery, state: FSMContext):
    users = await get_all_users()
    await state.clear()
    await state.set_state(DeleteUserState.select_user)
    await callback.message.edit_text(
        "Select a user to delete:",
        reply_markup=users_select_keyboard(users, callback.from_user.id),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), StateFilter(DeleteUserState.select_user), F.data.startswith("user_delete_select_"))
async def user_delete_select_user(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("user_delete_select_", ""))
    user = await get_user_by_id(user_id)
    if user.tg_id == callback.from_user.id:
        await callback.answer("You cannot delete yourself.", show_alert=True)
        return
    await state.set_state(DeleteUserState.confirm)
    await state.update_data(delete_user_id=user_id)
    text = await get_delete_text(user_id)
    await callback.message.edit_text(
        text,
        reply_markup=confirm_delete_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), StateFilter(DeleteUserState.select_user), F.data == "user_delete_back")
async def user_delete_back_to_manager(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    import aiohttp
    async with aiohttp.ClientSession() as session:
        await show_user_manager_menu(callback, session=session)

@router.callback_query(IsAdmin(), StateFilter(DeleteUserState.confirm), F.data == "user_delete_cancel")
async def user_delete_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    import aiohttp
    async with aiohttp.ClientSession() as session:
        await show_user_manager_menu(callback, session=session)

@router.callback_query(IsAdmin(), StateFilter(DeleteUserState.confirm), F.data == "user_delete_confirm")
async def user_delete_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["delete_user_id"]
    from app.db.models import User, UserServerAccess, ServerAPIData, Invite
    from sqlalchemy import delete
    import aiohttp

    async with AsyncSessionLocal() as session:
        await session.execute(delete(UserServerAccess).where(UserServerAccess.user_id == user_id))
        await session.execute(delete(ServerAPIData).where(ServerAPIData.user_id == user_id))
        await session.execute(delete(Invite).where(Invite.used_by == user_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
        logger.info(f"User {user_id} was deleted by admin {callback.from_user.id}")

    await state.clear()
    async with aiohttp.ClientSession() as session:
        await sync_all_users_on_servers(session)
        await callback.answer("✅ User deleted successfully!")
        await show_user_manager_menu(callback, session=session)