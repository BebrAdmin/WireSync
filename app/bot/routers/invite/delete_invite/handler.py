import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_active_invites, get_user_by_tg_id, delete_invite
from .keyboard import delete_invite_keyboard
from app.bot.routers.invite.handler import show_invite_manager_menu

logger = logging.getLogger("invite_delete")

router = Router()

@router.callback_query(F.data == "invite_delete_menu")
async def show_delete_invite_menu(callback: CallbackQuery):
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user or not getattr(user, "is_admin", False):
        logger.warning(f"User {callback.from_user.id} tried to access Delete Invite without admin rights")
        await callback.answer("Access denied. Admins only.", show_alert=True)
        return

    invites = await get_active_invites()
    logger.info(f"Admin {callback.from_user.id} opened Delete Invite menu")
    await callback.message.edit_text(
        "Select an invite code to delete:",
        reply_markup=delete_invite_keyboard(invites)
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
    await callback.answer("Invite deleted!")
    await show_invite_manager_menu(callback)