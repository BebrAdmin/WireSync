from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def server_manager_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔄 Синхронизировать",
            callback_data="sync_servers"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📝 Регистрация сервера",
            callback_data="register_server"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Удалить сервер",
            callback_data="delete_server_menu"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Настройка сервера",
            callback_data="settings_server_menu"
        )
    )    
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_to_main"
        )
    )
    return builder.as_markup()