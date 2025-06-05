from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def select_server_for_settings_keyboard(servers):
    builder = InlineKeyboardBuilder()
    for server in servers:
        builder.button(
            text=f"{server.name}",
            callback_data=f"settings_server_{server.id}"
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data="back_to_server_manager"
        )
    )
    return builder.as_markup()

def server_settings_menu_keyboard(server_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Add",
        callback_data=f"add_adapter_{server_id}"
    )
    builder.button(
        text="Delete",
        callback_data=f"delete_adapter_{server_id}"
    )
    builder.button(
        text="Update",
        callback_data=f"update_adapter_{server_id}"
    )
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data="settings_server_menu"
        )
    )
    return builder.as_markup()