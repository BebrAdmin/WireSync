from aiogram.utils.keyboard import InlineKeyboardBuilder

def adapter_update_custom_keyboard(server_id, iface_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Apply",
        callback_data=f"adapter_update_custom_confirm_{server_id}_{iface_id}"
    )
    builder.button(
        text="Reset",
        callback_data=f"adapter_update_reset_{server_id}_{iface_id}"
    )
    builder.button(
        text="Cancel",
        callback_data=f"adapter_update_cancel_{server_id}"
    )
    builder.adjust(2, 1)
    return builder.as_markup()

def adapter_update_select_keyboard(server_id, interfaces):
    builder = InlineKeyboardBuilder()
    for iface in interfaces:
        name = iface.get("DisplayName") or "—"
        identifier = iface.get("Identifier") or "—"
        builder.button(
            text=f"{name} [{identifier}]",
            callback_data=f"adapter_update_{server_id}_{identifier}"
        )
    builder.button(
        text="⬅️ Back",
        callback_data=f"settings_server_{server_id}"
    )
    builder.adjust(1)
    return builder.as_markup()