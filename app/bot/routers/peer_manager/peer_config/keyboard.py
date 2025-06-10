from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def peer_menu_keyboard(server_id, peer_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Get Config File",
            callback_data=f"peer_config_file_{server_id}_{peer_id}"
        ),
        InlineKeyboardButton(
            text="Get QR Code",
            callback_data=f"peer_config_qr_{server_id}_{peer_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=f"peer_config_back_{server_id}"
        )
    )
    return builder.as_markup()

def peer_config_close_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Close",
            callback_data="peer_config_close"
        )
    )
    return builder.as_markup()