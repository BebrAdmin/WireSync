from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def users_select_keyboard(users, current_admin_tg_id):
    builder = InlineKeyboardBuilder()
    row = []
    for user in users:
        if str(user.tg_id) == str(current_admin_tg_id):
            continue
        row.append(
            InlineKeyboardButton(
                text=user.tg_name or user.email or str(user.tg_id),
                callback_data=f"user_delete_select_{user.id}"
            )
        )
        if len(row) == 3:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data="user_delete_back"
        )
    )
    return builder.as_markup()

def confirm_delete_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Confirm Delete",
            callback_data="user_delete_confirm"
        ),
        InlineKeyboardButton(
            text="Cancel",
            callback_data="user_delete_cancel"
        )
    )
    return builder.as_markup()