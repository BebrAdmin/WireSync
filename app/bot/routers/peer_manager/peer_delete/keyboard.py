from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def peers_delete_list_keyboard(peers, server_id):
    builder = InlineKeyboardBuilder()
    for idx, _ in enumerate(peers, 1):
        builder.button(
            text=f"Peer {idx}",
            callback_data=f"peer_delete_select_{server_id}_{idx-1}"
        )
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=f"peer_delete_back_{server_id}"
        )
    )
    return builder.as_markup()

def peer_delete_confirm_keyboard(server_id, idx):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Confirm",
            callback_data=f"peer_delete_confirm_{server_id}_{idx}"
        ),
        InlineKeyboardButton(
            text="Cancel",
            callback_data=f"peer_delete_cancel_{server_id}"
        )
    )
    return builder.as_markup()