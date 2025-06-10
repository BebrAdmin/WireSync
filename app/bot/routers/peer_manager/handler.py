import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_all_servers, get_server_by_id, get_server_api_data_by_server_id_and_tg_id
from .keyboard import (
    servers_list_keyboard,
    peers_list_keyboard,
)
from app.wireguard_api.provisioning import get_user_peer_info
from app.bot.routers.main.keyboard import main_menu_keyboard
from app.db import get_user_by_tg_id
from app.bot.filters.is_registered import IsRegistered

logger = logging.getLogger("peer_manager")

router = Router()

@router.callback_query(IsRegistered(), F.data == "peer_manager_menu")
async def show_peer_manager_menu(callback: CallbackQuery, session):
    servers = await get_all_servers()
    logger.info(f"User {callback.from_user.id} opened peer manager menu")
    await callback.message.edit_text(
        "Select a server to manage your connections:",
        reply_markup=servers_list_keyboard(servers, add_back=True),
        parse_mode="HTML"
    )

@router.callback_query(IsRegistered(), F.data.startswith("peer_manager_server_"))
async def show_peers_for_server(callback: CallbackQuery, session, server_id=None):
    if server_id is None:
        server_id = int(callback.data.replace("peer_manager_server_", ""))
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        logger.warning(f"User {callback.from_user.id} tried to access unavailable server {server_id}")
        await callback.answer("Server is not available", show_alert=True)
        return

    try:
        user_info = await get_user_peer_info(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            user_id=api_data.api_login
        )
        peers = user_info.get("Peers", [])
        logger.info(f"User {callback.from_user.id} viewing peers for server {server_id}")

        if peers:
            peers_text = "<blockquote>"
            for idx, peer in enumerate(peers, 1):
                display_name = peer.get("DisplayName") or peer.get("Identifier") or f"Peer {idx}"
                interface = peer.get("InterfaceIdentifier", "—")
                peers_text += f"[{idx}] <b>{display_name}</b>\nInterface: <code>{interface}</code>"
                if idx != len(peers):
                    peers_text += "\n\n"
            peers_text += "</blockquote>"
        else:
            peers_text = "<blockquote>No peers found for this server.</blockquote>"

        await callback.message.edit_text(
            f"Peers for server: <b>{server.name}</b>\n{peers_text}",
            reply_markup=peers_list_keyboard(peers, server_id, can_create=True),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to get peers for server {server_id}: {e}")
        await callback.answer("Server is not available", show_alert=True)