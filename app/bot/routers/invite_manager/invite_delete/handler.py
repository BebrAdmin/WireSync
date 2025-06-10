import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_active_invites, get_user_by_tg_id, get_all_servers, delete_invite
from .keyboard import delete_invite_keyboard
from app.bot.routers.invite_manager.handler import show_invite_manager_menu

logger = logging.getLogger("invite_delete")

router = Router()

def numbered_invites_text(invites, servers_dict):
    if not invites:
        return "<i>No active invites.</i>"
    lines = []
    for idx, invite in enumerate(invites, 1):
        if getattr(invite, "is_admin", False):
            servers_str = "<i>(admin)</i>"
        else:
            server_ids = invite.server_ids or []
            if server_ids:
                names = [servers_dict.get(sid, str(sid)) for sid in server_ids]
                servers_str = "<i>(" + ", ".join(names) + ")</i>"
            else:
                servers_str = "<i>(no servers)</i>"
        lines.append(
            f"[{idx}] <code>{invite.code}</code> {servers_str}"
        )
    return "\n".join(lines)

@router.callback_query(F.data == "invite_delete_menu")
async def show_delete_invite_menu(callback: CallbackQuery):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to access Delete Invite without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return

    invites = await get_active_invites()
    servers = await get_all_servers()
    servers_dict = {s.id: s.name for s in servers}
    logger.info(f"Admin {callback.from_user.id} opened Delete Invite menu")
    await callback.message.edit_text(
        "<b>Select an invite code to delete:</b>\n\n"
        f"{numbered_invites_text(invites, servers_dict)}",
        reply_markup=delete_invite_keyboard(invites),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("delete_invite_"))
async def delete_invite_handler(callback: CallbackQuery):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to delete invite without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return

    invite_id = int(callback.data.replace("delete_invite_", ""))
    await delete_invite(invite_id)
    logger.info(f"Admin {callback.from_user.id} deleted invite {invite_id}")
    await callback.answer("✅Invite deleted!")
    await show_delete_invite_menu(callback)