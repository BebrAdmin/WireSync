from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def delete_invite_keyboard(invites):
    builder = InlineKeyboardBuilder()
    for idx, invite in enumerate(invites, 1):
        builder.button(
            text=f"[{idx}]",
            callback_data=f"delete_invite_{invite.id}"
        )
    if invites:
        builder.adjust(3)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data="invite_manager_menu"
        )
    )
    return builder.as_markup()