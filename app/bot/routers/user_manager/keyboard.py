from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def users_manager_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Edit Access",
            callback_data="user_manager_edit_access"
        ),
        InlineKeyboardButton(
            text="Delete User",
            callback_data="user_manager_delete_user"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data="user_manager_back"
        )
    )
    return builder.as_markup()