from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def rights_select_keyboard(servers, selected_server_ids, is_admin, access_all, user_is_admin):
    builder = InlineKeyboardBuilder()
    admin_text = "✅ Admin" if is_admin else "Admin"
    builder.row(
        InlineKeyboardButton(
            text=admin_text,
            callback_data="edit_access_toggle_admin"
        )
    )
    if not is_admin and servers:
        builder.row(
            InlineKeyboardButton(
                text=("✅ Access All" if access_all else "Access All"),
                callback_data="edit_access_toggle_all"
            )
        )
    if not is_admin:
        server_buttons = []
        for server in servers:
            checked = "✅ " if server.id in selected_server_ids else ""
            server_buttons.append(
                InlineKeyboardButton(
                    text=f"{checked}{server.name}",
                    callback_data=f"edit_access_toggle_server_{server.id}"
                )
            )
        for i in range(0, len(server_buttons), 3):
            builder.row(*server_buttons[i:i+3])
    builder.row(
        InlineKeyboardButton(
            text="Confirm",
            callback_data="edit_access_confirm"
        ),
        InlineKeyboardButton(
            text="Cancel",
            callback_data="edit_access_cancel"
        )
    )
    return builder.as_markup()

def users_select_keyboard(users, current_admin_tg_id):
    builder = InlineKeyboardBuilder()
    row = []
    for user in users:
        if str(user.tg_id) == str(current_admin_tg_id):
            continue
        row.append(
            InlineKeyboardButton(
                text=user.tg_name or user.email or str(user.tg_id),
                callback_data=f"edit_access_select_{user.id}"
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
            callback_data="edit_access_back"
        )
    )
    return builder.as_markup()