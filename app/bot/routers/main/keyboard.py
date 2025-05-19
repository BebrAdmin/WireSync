from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Мои подключения",
        callback_data="peer_manager_menu"
    )
    if is_admin:
        builder.row(
            InlineKeyboardButton(
                text="🖥️ Server Manager",
                callback_data="server_manager"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔑 Invite Manager",
                callback_data="invite_manager_menu"
            )
        )
    return builder.as_markup()
