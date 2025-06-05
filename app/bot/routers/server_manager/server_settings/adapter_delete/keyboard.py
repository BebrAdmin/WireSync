from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def adapter_delete_select_keyboard(server_id, interfaces):
    builder = InlineKeyboardBuilder()
    for iface in interfaces:
        name = iface.get("DisplayName") or "—"
        identifier = iface.get("Identifier") or "—"
        builder.button(
            text=f"{name} [{identifier}]",
            callback_data=f"delete_adapter_select_{server_id}_{identifier}"
        )
    builder.button(
        text="⬅️ Back",
        callback_data=f"delete_adapter_cancel_{server_id}"
    )
    builder.adjust(1)
    return builder.as_markup()

def adapter_delete_confirm_keyboard(server_id, iface_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Confirm",
        callback_data=f"delete_adapter_confirm_{server_id}_{iface_id}"
    )
    builder.button(
        text="Cancel",
        callback_data=f"delete_adapter_cancel_{server_id}"
    )
    builder.adjust(2)
    return builder.as_markup()