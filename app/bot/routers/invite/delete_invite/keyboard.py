from aiogram.utils.keyboard import InlineKeyboardBuilder

def delete_invite_keyboard(invites):
    builder = InlineKeyboardBuilder()
    for invite in invites:
        builder.button(
            text=invite.code,
            callback_data=f"delete_invite_{invite.id}"
        )
    builder.button(
        text="⬅️ Back",
        callback_data="invite_manager_menu"
    )
    builder.adjust(1)
    return builder.as_markup()