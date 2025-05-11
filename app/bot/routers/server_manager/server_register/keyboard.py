from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="to_server_manager")
    )
    return builder.as_markup()

def confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Синхронизировать", callback_data="sync_server"),
        InlineKeyboardButton(text="✏️ Изменить", callback_data="restart_register"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="to_server_manager"),
    )
    return builder.as_markup()