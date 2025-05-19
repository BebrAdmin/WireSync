import logging
import random
import string
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.db import get_all_servers, create_invite, get_invite_by_code, get_user_by_tg_id
from .keyboard import select_servers_keyboard
from .fsm import CreateInviteState

logger = logging.getLogger("invite_create")

router = Router()

def generate_invite_code():
    chars = string.ascii_letters
    while True:
        code = ''.join(random.choices(chars, k=12)) + '-' + ''.join(random.choices(chars, k=12))
        return code

@router.callback_query(F.data == "invite_create_menu")
async def start_create_invite(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to access Create Invite without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return

    servers = await get_all_servers()
    await state.set_state(CreateInviteState.select_servers)
    await state.update_data(selected_servers=[])
    logger.info(f"Admin {callback.from_user.id} started invite creation")
    if not servers:
        await callback.message.edit_text(
            "No connected servers available.\nYou can still create an invite code (it will not grant access to any server).",
            reply_markup=select_servers_keyboard([], [])
        )
        return
    await callback.message.edit_text(
        "Select servers for the invite code:",
        reply_markup=select_servers_keyboard(servers, [])
    )

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data.startswith("accept_server_"))
async def toggle_server(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to select server without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return

    server_id = int(callback.data.replace("accept_server_", ""))
    data = await state.get_data()
    selected = set(data.get("selected_servers", []))
    if server_id in selected:
        selected.remove(server_id)
        logger.info(f"Server {server_id} unchecked for invite by admin {callback.from_user.id}")
        await callback.answer("Server unchecked.")
    else:
        selected.add(server_id)
        logger.info(f"Server {server_id} checked for invite by admin {callback.from_user.id}")
        await callback.answer("Server checked.")
    servers = await get_all_servers()
    await state.update_data(selected_servers=list(selected))
    await callback.message.edit_reply_markup(
        reply_markup=select_servers_keyboard(servers, list(selected))
    )

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data == "accept_all_servers")
async def accept_all_servers(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to select all servers without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return

    servers = await get_all_servers()
    all_ids = [s.id for s in servers]
    await state.update_data(selected_servers=all_ids)
    logger.info(f"Admin {callback.from_user.id} selected all servers for invite")
    await callback.answer("All servers selected.")
    await callback.message.edit_reply_markup(
        reply_markup=select_servers_keyboard(servers, all_ids)
    )

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data == "invite_create_cancel")
async def cancel_create_invite(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    logger.info(f"Admin {callback.from_user.id} cancelled invite creation")
    await callback.answer("Invite creation cancelled.")
    from app.bot.routers.invite.handler import show_invite_manager_menu
    await show_invite_manager_menu(callback)

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data == "invite_create_confirm")
async def confirm_create_invite(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to confirm invite creation without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return

    data = await state.get_data()
    selected = data.get("selected_servers", [])
    if selected is None:
        selected = []
    for _ in range(10):
        code = generate_invite_code()
        if not await get_invite_by_code(code):
            break
    else:
        logger.error("Failed to generate unique invite code after 10 attempts")
        await callback.answer("Failed to generate invite code.", show_alert=True)
        return
    invite = await create_invite(code, selected)
    logger.info(f"Invite code {code} created by admin {callback.from_user.id} for servers {selected}")
    await state.clear()
    await callback.answer("✅Invite code created!")
    from app.bot.routers.invite.handler import show_invite_manager_menu
    await show_invite_manager_menu(callback)