from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_active_invites, get_user_by_tg_id, get_all_servers
from .keyboard import invite_manager_menu_keyboard
import logging

logger = logging.getLogger("invite_manager")

router = Router()

def active_invites_text(invites, servers_dict):
    if not invites:
        return "No active invites."
    lines = []
    for invite in invites:
        server_ids = invite.server_ids or []
        if server_ids:
            names = [servers_dict.get(sid, str(sid)) for sid in server_ids]
            servers_str = "/".join(names)
        else:
            servers_str = "no servers"
        lines.append(f"🔹 <code>{invite.code}</code> ({servers_str})\n")
    return "\n".join(lines)

@router.callback_query(F.data == "invite_manager_menu")
async def show_invite_manager_menu(callback: CallbackQuery):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to access Invite Manager without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return

    invites = await get_active_invites()
    servers = await get_all_servers()
    servers_dict = {s.id: s.name for s in servers}
    logger.info(f"Admin {callback.from_user.id} opened Invite Manager")
    await callback.message.edit_text(
        f"Active invites:\n{active_invites_text(invites, servers_dict)}",
        reply_markup=invite_manager_menu_keyboard(),
        parse_mode="HTML"
    )