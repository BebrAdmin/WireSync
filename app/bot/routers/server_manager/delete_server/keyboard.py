from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def delete_server_keyboard(servers):
    builder = InlineKeyboardBuilder()
    for server in servers:
        builder.button(
            text=f"{server.name}",
            callback_data=f"delete_server_{server.id}"
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_server_manager"))
    return builder.as_markup()

def confirm_delete_keyboard(server_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="Confirm", callback_data=f"confirm_delete_{server_id}")
    builder.button(text="Cancel", callback_data="delete_server_menu")
    builder.adjust(2)
    return builder.as_markup()