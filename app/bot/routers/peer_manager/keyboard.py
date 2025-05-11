from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def servers_list_keyboard(servers):
    builder = InlineKeyboardBuilder()
    for server in servers:
        builder.button(
            text=server.name,
            callback_data=f"peer_manager_server_{server.id}"
        )
    builder.adjust(1)
    return builder.as_markup()

def peers_list_keyboard(peers, server_id, interface_id=None):
    builder = InlineKeyboardBuilder()
    for peer in peers:
        builder.button(
            text=peer.get("Identifier", "Peer"),
            callback_data=f"peer_manager_peer_{server_id}_{peer['Identifier']}"
        )
    if interface_id:
        builder.button(
            text="➕ Создать пир",
            callback_data=f"peer_manager_create_{server_id}_{interface_id}"
        )
    builder.button(
        text="⬅️ Назад",
        callback_data="peer_manager_menu"
    )
    builder.adjust(1)
    return builder.as_markup()

def interfaces_list_keyboard(interfaces, server_id):
    builder = InlineKeyboardBuilder()
    for iface in interfaces:
        name = iface.get("DisplayName") or iface.get("Identifier") or "—"
        builder.button(
            text=name,
            callback_data=f"peer_manager_interface_{server_id}_{iface['Identifier']}"
        )
    builder.button(
        text="⬅️ Назад",
        callback_data="peer_manager_menu"
    )
    builder.adjust(1)
    return builder.as_markup()

