import logging
import random
import string
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.db import get_all_servers, create_invite, get_invite_by_code, get_user_by_tg_id
from .keyboard import select_invite_accept_keyboard
from .fsm import CreateInviteState
from app.bot.routers.invite_manager.handler import show_invite_manager_menu

logger = logging.getLogger("invite_create")

router = Router()

def generate_invite_code():
    chars = string.ascii_letters
    while True:
        code = ''.join(random.choices(chars, k=12)) + '-' + ''.join(random.choices(chars, k=12))
        return code

def get_accept_text(servers, selected_ids, admin_selected):
    if not servers:
        return (
            "<b>No connected servers available.</b>\n"
            "You can still create an invite code (it will not grant access to any server).\n\n"
            "ℹ️ <i>Admins always have access to all servers.</i>"
        )
    text = "<b>Select access for the invite code:</b>\n"
    if admin_selected:
        text += "<b>Admin will have access to all servers.</b>\n"
    else:
        if selected_ids:
            names = [s.name for s in servers if s.id in selected_ids]
            text += "<b>Selected servers:</b> " + (", ".join(names) if names else "None") + "\n"
        else:
            text += "<b>No servers selected.</b>\n"
    text += "\nℹ️ <i>Admins always have access to all servers.</i>"
    return text

@router.callback_query(F.data == "invite_create_menu")
async def start_create_invite(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to access Create Invite without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return
    await state.set_state(CreateInviteState.select_servers)
    servers = await get_all_servers()
    await state.update_data(selected_servers=[], admin_selected=False)
    text = get_accept_text(servers, [], False)
    markup = select_invite_accept_keyboard(servers, [], False)
    await callback.message.edit_text(
        text,
        reply_markup=markup,
        parse_mode="HTML"
    )

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data == "accept_admin")
async def toggle_accept_admin(callback: CallbackQuery, state: FSMContext):
    servers = await get_all_servers()
    data = await state.get_data()
    admin_selected = not data.get("admin_selected", False)
    selected_servers = [s.id for s in servers] if admin_selected else []
    await state.update_data(admin_selected=admin_selected, selected_servers=selected_servers)
    text = get_accept_text(servers, selected_servers, admin_selected)
    markup = select_invite_accept_keyboard(servers, selected_servers, admin_selected)
    if callback.message.text == text and callback.message.reply_markup == markup:
        return
    await callback.message.edit_text(
        text,
        reply_markup=markup,
        parse_mode="HTML"
    )

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data == "accept_all_servers")
async def toggle_accept_all_servers(callback: CallbackQuery, state: FSMContext):
    servers = await get_all_servers()
    data = await state.get_data()
    admin_selected = data.get("admin_selected", False)
    if admin_selected or not servers:
        return
    selected_servers = set(data.get("selected_servers", []))
    all_ids = set(s.id for s in servers)
    if selected_servers == all_ids:
        new_selected = []
    else:
        new_selected = list(all_ids)
    await state.update_data(selected_servers=new_selected)
    text = get_accept_text(servers, new_selected, admin_selected)
    markup = select_invite_accept_keyboard(servers, new_selected, admin_selected)
    if callback.message.text == text and callback.message.reply_markup == markup:
        return
    await callback.message.edit_text(
        text,
        reply_markup=markup,
        parse_mode="HTML"
    )

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data.startswith("accept_server_"))
async def toggle_server(callback: CallbackQuery, state: FSMContext):
    servers = await get_all_servers()
    data = await state.get_data()
    admin_selected = data.get("admin_selected", False)
    if admin_selected:
        return
    server_id = int(callback.data.replace("accept_server_", ""))
    selected = set(data.get("selected_servers", []))
    if server_id in selected:
        selected.remove(server_id)
    else:
        selected.add(server_id)
    await state.update_data(selected_servers=list(selected))
    text = get_accept_text(servers, list(selected), admin_selected)
    markup = select_invite_accept_keyboard(servers, list(selected), admin_selected)
    if callback.message.text == text and callback.message.reply_markup == markup:
        return
    await callback.message.edit_text(
        text,
        reply_markup=markup,
        parse_mode="HTML"
    )

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data == "invite_create_confirm")
async def confirm_create_invite(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to confirm invite creation without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return
    data = await state.get_data()
    servers = await get_all_servers()
    admin_selected = data.get("admin_selected", False)
    selected = data.get("selected_servers", [])
    if admin_selected:
        selected = [s.id for s in servers]
    for _ in range(10):
        code = generate_invite_code()
        if not await get_invite_by_code(code):
            break
    else:
        logger.error("Failed to generate unique invite code after 10 attempts")
        await callback.answer("Failed to generate invite code.", show_alert=True)
        return
    invite = await create_invite(code, selected, is_admin=admin_selected, admin_tg_id=callback.from_user.id)
    short_code = f"{code[:6]}... (len={len(code)})"
    logger.info(f"Invite code {short_code} created by admin {callback.from_user.id} for servers {selected}, is_admin={admin_selected}")
    await state.clear()
    await callback.answer("✅ Invite code created!")
    await show_invite_manager_menu(callback)

@router.callback_query(StateFilter(CreateInviteState.select_servers), F.data == "invite_create_cancel")
async def cancel_create_invite(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    logger.info(f"Admin {callback.from_user.id} cancelled invite creation")
    await show_invite_manager_menu(callback)