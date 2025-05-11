import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from app.db import get_all_servers, get_server_by_id, get_server_api_data_by_server_id_and_tg_id
from .keyboard import (
    servers_list_keyboard,
    interfaces_list_keyboard,
    peers_list_keyboard,
)
from app.wireguard_api.provisioning import get_user_peer_info, create_peer, get_peer_config
from app.wireguard_api.interfaces import get_all_interfaces
from app.bot.routers.main.keyboard import main_menu_keyboard
from app.db import get_user_by_tg_id

logger = logging.getLogger("peer_manager")

router = Router()

@router.callback_query(F.data == "peer_manager_menu")
async def show_peer_manager_menu(callback: CallbackQuery, session):
    servers = await get_all_servers()
    logger.info(f"User {callback.from_user.id} opened peer manager menu")
    await callback.message.edit_text(
        "Select a server to manage your connections:",
        reply_markup=servers_list_keyboard(servers)
    )

@router.callback_query(F.data.startswith("peer_manager_server_"))
async def show_interfaces_for_server(callback: CallbackQuery, session):
    server_id = int(callback.data.replace("peer_manager_server_", ""))
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        logger.warning(f"User {callback.from_user.id} tried to access unavailable server {server_id}")
        await callback.answer("No access to this server.", show_alert=True)
        return

    try:
        interfaces = await get_all_interfaces(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password
        )
        if not interfaces:
            logger.info(f"No interfaces found for server {server_id} by user {callback.from_user.id}")
            await callback.answer("No available interfaces.", show_alert=True)
            return
        logger.info(f"User {callback.from_user.id} viewing interfaces for server {server_id}")
        await callback.message.edit_text(
            "Select an interface:",
            reply_markup=interfaces_list_keyboard(interfaces, server_id)
        )
    except Exception as e:
        logger.error(f"Failed to get interfaces for server {server_id}: {e}")
        await callback.answer(f"API error: {e}", show_alert=True)

@router.callback_query(F.data.startswith("peer_manager_interface_"))
async def show_peers_for_interface(callback: CallbackQuery, session):
    parts = callback.data.split("_")
    server_id = int(parts[3])
    interface_id = parts[4]
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        logger.warning(f"User {callback.from_user.id} tried to access unavailable server {server_id} (interface {interface_id})")
        await callback.answer("No access to this server.", show_alert=True)
        return

    try:
        user_info = await get_user_peer_info(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            user_id=api_data.api_login
        )
        peers = [
            peer for peer in user_info.get("Peers", [])
            if peer.get("InterfaceIdentifier") == interface_id
        ]
        logger.info(f"User {callback.from_user.id} viewing peers for server {server_id}, interface {interface_id}")
        await callback.message.edit_text(
            "Your connections:" if peers else "You have no connections. Would you like to create a peer?",
            reply_markup=peers_list_keyboard(peers, server_id, interface_id)
        )
    except Exception as e:
        logger.error(f"Failed to get peers for server {server_id}, interface {interface_id}: {e}")
        await callback.answer(f"API error: {e}", show_alert=True)

@router.callback_query(F.data.startswith("peer_manager_create_"))
async def create_peer_for_user(callback: CallbackQuery, session):
    parts = callback.data.split("_")
    server_id = int(parts[3])
    interface_id = parts[4]
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        logger.warning(f"User {callback.from_user.id} tried to create peer on unavailable server {server_id}")
        await callback.answer("No access to this server.", show_alert=True)
        return
    try:
        await create_peer(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            interface_id=interface_id,
            user_id=api_data.api_login
        )
        logger.info(
            f"Peer created for server_id={server_id}, interface_id={interface_id} by user {callback.from_user.id} (api_login={api_data.api_login})"
        )
        await callback.answer("Peer successfully created!")
        await show_peers_for_interface(callback, session)
    except Exception as e:
        logger.error(f"Failed to create peer for server {server_id}, interface {interface_id}: {e}")
        await callback.answer(f"Failed to create peer: {e}", show_alert=True)

@router.callback_query(F.data.startswith("peer_manager_peer_"))
async def show_peer_config(callback: CallbackQuery, session):
    parts = callback.data.split("_")
    server_id = int(parts[3])
    peer_id = parts[4]
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        logger.warning(f"User {callback.from_user.id} tried to get config for unavailable server {server_id}")
        await callback.answer("No access to this server.", show_alert=True)
        return
    try:
        config = await get_peer_config(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            peer_id=peer_id
        )
        user_info = await get_user_peer_info(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            user_id=api_data.api_login
        )
        interface_id = None
        for peer in user_info.get("Peers", []):
            if peer.get("Identifier") == peer_id:
                interface_id = peer.get("InterfaceIdentifier")
                break
        if not interface_id:
            logger.error(f"Could not determine interface for peer {peer_id} (server {server_id})")
            await callback.answer("Could not determine peer interface.", show_alert=True)
            return

        logger.info(
            f"Peer config sent for server_id={server_id}, peer_id={peer_id} to user {callback.from_user.id} (api_login={api_data.api_login})"
        )
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Failed to delete message before sending config file: {e}")
        file = BufferedInputFile(config.encode("utf-8"), filename="wg-peer.conf")
        await callback.message.answer_document(
            file,
            caption="Your WireGuard config"
        )
        await callback.answer("Config sent!")
    except Exception as e:
        logger.error(f"Failed to get config for server {server_id}, peer_id {peer_id}: {e}")
        await callback.answer(f"Failed to get config: {e}", show_alert=True)