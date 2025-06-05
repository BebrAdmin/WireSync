import logging
import json
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.db import (
    get_server_by_id,
    get_server_api_data_by_server_id_and_tg_id,
    get_admin_api_data_for_server,
)
from app.wireguard_api.provisioning import get_user_peer_info
from app.wireguard_api.peers import get_peer_by_id, delete_peer_by_id
from .keyboard import peers_delete_list_keyboard, peer_delete_confirm_keyboard
from app.bot.filters.is_registered import IsRegistered

router = Router()
logger = logging.getLogger("peer_delete")

def is_admin(api_data):
    return getattr(api_data, "is_admin", False) or getattr(api_data, "is_admin", None) is True

@router.callback_query(IsRegistered(), F.data.startswith("peer_manager_delete_"))
async def show_peers_for_delete(callback: CallbackQuery, session: dict, state: FSMContext):
    try:
        server_id = int(callback.data.split("_")[-1])
        server = await get_server_by_id(server_id)
        user_api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
        if not user_api_data:
            await callback.answer("No access to server.", show_alert=True)
            from app.bot.routers.peer_manager.handler import show_peer_manager_menu
            await show_peer_manager_menu(callback, session)
            return
        user_info = await get_user_peer_info(
            session,
            api_url=server.api_url,
            api_user=user_api_data.api_login,
            api_pass=user_api_data.api_password,
            user_id=user_api_data.api_login
        )
        peers = user_info.get("Peers", [])
        if not peers:
            await callback.answer("No peers found for this server.", show_alert=True)
            from app.bot.routers.peer_manager.handler import show_peers_for_server
            await show_peers_for_server(callback, session, server_id=server_id)
            return
        await state.update_data(peers_delete_list=peers)
        peers_text = "<blockquote>"
        for idx, peer in enumerate(peers, 1):
            display_name = peer.get("DisplayName") or peer.get("Identifier") or f"Peer {idx}"
            interface = peer.get("InterfaceIdentifier", "—")
            peers_text += f"[{idx}] <b>{display_name}</b>\nInterface: <code>{interface}</code>"
            if idx != len(peers):
                peers_text += "\n\n"
        peers_text += "</blockquote>"

        await callback.message.edit_text(
            f"Delete peer: <b>{server.name}</b>\n{peers_text}\n\nSelect a peer to delete.",
            reply_markup=peers_delete_list_keyboard(peers, server_id),
            parse_mode="HTML"
        )
    except Exception:
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)

@router.callback_query(IsRegistered(), F.data.startswith("peer_delete_select_"))
async def show_peer_delete_confirm(callback: CallbackQuery, session: dict, state: FSMContext):
    try:
        _, _, _, server_id, idx = callback.data.split("_")
        server_id = int(server_id)
        idx = int(idx)
        data = await state.get_data()
        peers = data.get("peers_delete_list", [])
        if idx >= len(peers):
            await callback.answer("Peer not found.", show_alert=True)
            return
        peer = peers[idx]
        server = await get_server_by_id(server_id)
        user_api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
        peer_data = await get_peer_by_id(
            session,
            api_url=server.api_url,
            api_user=user_api_data.api_login,
            api_pass=user_api_data.api_password,
            peer_id=peer["Identifier"]
        )
        important_fields = [
            "DisplayName", "Identifier", "InterfaceIdentifier", "AllowedIPs",
            "Addresses", "PublicKey", "Endpoint"
        ]
        peer_short = {k: peer_data.get(k) for k in important_fields if k in peer_data}
        peer_json = json.dumps(peer_short, indent=2)
        text = (
            f"Peer info: <b>{server.name}</b>\n"
            f"<blockquote><pre>{peer_json}</pre></blockquote>\n"
            "\nAre you sure you want to delete this peer?"
        )
        await callback.message.edit_text(
            text,
            reply_markup=peer_delete_confirm_keyboard(server_id, idx),
            parse_mode="HTML"
        )
    except Exception:
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)

@router.callback_query(IsRegistered(), F.data.startswith("peer_delete_confirm_"))
async def do_peer_delete(callback: CallbackQuery, session: dict, state: FSMContext):
    _, _, _, server_id, idx = callback.data.split("_")
    server_id = int(server_id)
    idx = int(idx)
    data = await state.get_data()
    peers = data.get("peers_delete_list", [])
    if idx >= len(peers):
        await callback.answer("Peer not found.", show_alert=True)
        return
    peer_id = peers[idx]["Identifier"]
    api_data = await get_admin_api_data_for_server(server_id)
    server = await get_server_by_id(server_id)
    try:
        await delete_peer_by_id(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            peer_id=peer_id
        )
        logger.info(f"Peer deleted on server {server_id} by user {callback.from_user.id}")
        await callback.answer("✅ Peer deleted!")
        from app.bot.routers.peer_manager.handler import show_peers_for_server
        await show_peers_for_server(callback, session, server_id=server_id)
    except Exception as e:
        logger.error(f"Failed to delete peer on server {server_id}: {e}")
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)

@router.callback_query(IsRegistered(), F.data.startswith("peer_delete_cancel_"))
@router.callback_query(IsRegistered(), F.data.startswith("peer_delete_back_"))
async def back_to_peer_manager(callback: CallbackQuery, session: dict, state: FSMContext):
    from app.bot.routers.peer_manager.handler import show_peers_for_server
    server_id = int(callback.data.split("_")[-1])
    await show_peers_for_server(callback, session, server_id=server_id)