from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def server_register_custom_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Apply", callback_data="server_register_apply")
    builder.button(text="Reset", callback_data="server_register_reset")
    builder.button(text="Cancel", callback_data="server_register_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()

def server_register_select_users_keyboard(users, selected_ids, users_info=None):
    builder = InlineKeyboardBuilder()
    unique_users = list(dict.fromkeys(users))  
    users_info = users_info or {}

    user_buttons = []
    for user_id in unique_users:
        checked = "✅ " if user_id in selected_ids else ""
        display_name = users_info.get(user_id) or str(user_id)
        user_buttons.append(
            InlineKeyboardButton(
                text=f"{checked}{display_name}",
                callback_data=f"server_register_user_{user_id}"
            )
        )

    if unique_users:
        builder.row(
            InlineKeyboardButton(text="Accept All", callback_data="server_register_accept_all")
        )

    for i in range(0, len(user_buttons), 3):
        builder.row(*user_buttons[i:i+3])

    builder.row(
        InlineKeyboardButton(text="Apply", callback_data="server_register_users_apply"),
        InlineKeyboardButton(text="Cancel", callback_data="server_register_cancel"),
    )
    return builder.as_markup()

def server_register_no_users_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Apply", callback_data="server_register_users_apply"),
        InlineKeyboardButton(text="Cancel", callback_data="server_register_cancel"),
    )
    return builder.as_markup()

def server_register_post_add_keyboard(server_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="Yes", callback_data=f"server_register_configure_yes_{server_id}")
    builder.button(text="No", callback_data="server_register_configure_no")
    builder.adjust(2)
    return builder.as_markup()