from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def invite_manager_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Create Invite", callback_data="invite_create_menu"),
        InlineKeyboardButton(text="Delete Invite", callback_data="invite_delete_menu"),
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")
    )
    return builder.as_markup()

