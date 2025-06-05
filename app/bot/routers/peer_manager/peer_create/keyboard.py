from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def interfaces_keyboard(server_id, interfaces):
    builder = InlineKeyboardBuilder()
    for interface in interfaces:
        builder.button(
            text=interface.get("DisplayName") or interface.get("Identifier"),
            callback_data=f"peer_create_interface_{server_id}_{interface['Identifier']}"
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=f"peer_create_back_{server_id}"
        )
    )
    return builder.as_markup()

def confirm_create_peer_keyboard(server_id, interface_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Confirm",
            callback_data=f"peer_create_confirm_{server_id}_{interface_id}"
        ),
        InlineKeyboardButton(
            text="Cancel",
            callback_data=f"peer_create_back_{server_id}"
        )
    )
    return builder.as_markup()