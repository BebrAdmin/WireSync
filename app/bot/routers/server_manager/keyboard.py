from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def server_manager_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔄 Synchronize",
            callback_data="sync_servers"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Add Server",
            callback_data="register_server"
        ),
        InlineKeyboardButton(
            text="Delete Server",
            callback_data="delete_server_menu"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Interface Settings",
            callback_data="settings_server_menu"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data="back_to_main"
        )
    )
    return builder.as_markup()