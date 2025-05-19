from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def select_servers_keyboard(servers, selected_ids):
    builder = InlineKeyboardBuilder()
    for server in servers:
        checked = "✅ " if server.id in selected_ids else ""
        builder.button(
            text=f"{checked}{server.name}",
            callback_data=f"accept_server_{server.id}"
        )
    if servers:
        builder.adjust(3)
        builder.row(
            InlineKeyboardButton(text="Accept All", callback_data="accept_all_servers")
        )
    builder.row(
        InlineKeyboardButton(text="Create", callback_data="invite_create_confirm"),
        InlineKeyboardButton(text="Cancel", callback_data="invite_create_cancel"),
    )
    return builder.as_markup()