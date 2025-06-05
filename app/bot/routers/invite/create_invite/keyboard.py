from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def select_invite_accept_keyboard(servers, selected_ids, admin_selected):
    builder = InlineKeyboardBuilder()
    admin_text = "✅ Accept Admin" if admin_selected else "Accept Admin"
    builder.row(
        InlineKeyboardButton(text=admin_text, callback_data="accept_admin")
    )
    if not admin_selected and servers:
        builder.row(
            InlineKeyboardButton(
                text="Accept All",
                callback_data="accept_all_servers"
            )
        )
    if not admin_selected:
        server_buttons = []
        for server in servers:
            checked = "✅ " if server.id in selected_ids else ""
            server_buttons.append(
                InlineKeyboardButton(
                    text=f"{checked}{server.name}",
                    callback_data=f"accept_server_{server.id}"
                )
            )
        for i in range(0, len(server_buttons), 3):
            builder.row(*server_buttons[i:i+3])
    builder.row(
        InlineKeyboardButton(text="Create", callback_data="invite_create_confirm"),
        InlineKeyboardButton(text="Cancel", callback_data="invite_create_cancel"),
    )
    return builder.as_markup()