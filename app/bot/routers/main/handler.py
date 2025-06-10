from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from .keyboard import main_menu_keyboard
from app.db import get_user_by_tg_id
from app.bot.filters.is_admin import IsAdmin
from app.bot.filters.is_registered import IsRegistered

router = Router()

@router.callback_query(IsRegistered(), F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    user = await get_user_by_tg_id(callback.from_user.id)
    is_admin = bool(user and getattr(user, "is_admin", False))
    await callback.message.edit_text(
        "Main Menu:",
        reply_markup=main_menu_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )