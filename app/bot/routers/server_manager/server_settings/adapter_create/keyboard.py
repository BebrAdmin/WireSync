from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def adapter_create_confirm_keyboard(server_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Create Default",
            callback_data=f"adapter_create_confirm_{server_id}"
        ),
        InlineKeyboardButton(
            text="Cancel",
            callback_data=f"adapter_create_cancel_{server_id}"
        ),
    )
    return builder.as_markup()

def adapter_create_custom_keyboard(server_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Create Adapter",
            callback_data=f"adapter_create_custom_confirm_{server_id}"
        ),
        InlineKeyboardButton(
            text="Reset to Default",
            callback_data=f"adapter_create_reset_{server_id}"
        ),
        InlineKeyboardButton(
            text="Cancel",
            callback_data=f"adapter_create_cancel_{server_id}"
        ),
    )
    return builder.as_markup()