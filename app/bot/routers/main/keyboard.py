from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="My Connections",
        callback_data="peer_manager_menu"
    )
    if is_admin:
        builder.button(
            text="🖥️ Server Manager",
            callback_data="server_manager"
        )
        builder.button(
            text="🔑 Invite Manager",
            callback_data="invite_manager_menu"
        )
        builder.adjust(1, 2)
    else:
        builder.adjust(1)
    return builder.as_markup()