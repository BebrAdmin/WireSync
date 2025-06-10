from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def servers_list_keyboard(servers, add_back=False):
    builder = InlineKeyboardBuilder()
    for server in servers:
        builder.button(
            text=server.name,
            callback_data=f"peer_manager_server_{server.id}"
        )
    builder.adjust(1)
    if add_back:
        builder.button(
            text="⬅️ Back",
            callback_data="main_menu"
        )
        builder.adjust(1)
    return builder.as_markup()

def peers_list_keyboard(peers, server_id, can_create=True):
    builder = InlineKeyboardBuilder()
    if can_create:
        builder.row(
            InlineKeyboardButton(
                text="Create Peer",
                callback_data=f"peer_manager_create_{server_id}"
            ),
            InlineKeyboardButton(
                text="Delete Peer",
                callback_data=f"peer_manager_delete_{server_id}"
            )
        )
    peer_buttons = []
    for idx, peer in enumerate(peers, 1):
        peer_buttons.append(
            InlineKeyboardButton(
                text=f"Peer {idx}",
                callback_data=f"peer_manager_peer_{server_id}_{peer['Identifier']}"
            )
        )
    for i in range(0, len(peer_buttons), 3):
        builder.row(*peer_buttons[i:i+3])
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data="peer_manager_menu"
        )
    )
    return builder.as_markup()