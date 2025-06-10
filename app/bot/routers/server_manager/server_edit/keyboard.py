from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def server_edit_custom_keyboard(server_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="Apply", callback_data=f"server_edit_apply_{server_id}")
    builder.button(text="Reset", callback_data="server_edit_reset")
    builder.button(text="Cancel", callback_data="server_edit_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()

def edit_server_select_keyboard(servers):
    builder = InlineKeyboardBuilder()
    for server in servers:
        builder.button(
            text=server.name,
            callback_data=f"server_edit_{server.id}"
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data="server_manager"
        )
    )
    return builder.as_markup()