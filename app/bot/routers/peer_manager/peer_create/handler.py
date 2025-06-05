import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_server_by_id, get_server_api_data_by_server_id_and_tg_id, get_admin_api_data_for_server, get_all_servers
from app.wireguard_api.interfaces import get_all_interfaces
from app.wireguard_api.provisioning import create_peer
from .keyboard import interfaces_keyboard, confirm_create_peer_keyboard
from app.bot.filters.is_registered import IsRegistered

router = Router()
logger = logging.getLogger("peer_create")

@router.callback_query(IsRegistered(), F.data.startswith("peer_manager_create_"))
async def choose_interface(callback: CallbackQuery, session):
    server_id = int(callback.data.split("_")[-1])
    server = await get_server_by_id(server_id)
    admin_api_data = await get_admin_api_data_for_server(server_id)
    if not server or not admin_api_data:
        logger.warning(f"User {callback.from_user.id} has no access to server interfaces (server_id={server_id})")
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)
        return
    interfaces = await get_all_interfaces(
        session,
        api_url=server.api_url,
        api_user=admin_api_data.api_login,
        api_pass=admin_api_data.api_password
    )
    await callback.message.edit_text(
        f"Create peer: <b>{server.name}</b>\nSelect an interface for the new peer:",
        reply_markup=interfaces_keyboard(server_id, interfaces),
        parse_mode="HTML"
    )

@router.callback_query(IsRegistered(), F.data.startswith("peer_create_interface_"))
async def confirm_peer_create(callback: CallbackQuery, session):
    _, _, _, server_id, interface_id = callback.data.split("_")
    server_id = int(server_id)
    from app.db import get_server_by_id
    server = await get_server_by_id(server_id)
    if not server:
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)
        return
    await callback.message.edit_text(
        f"Create peer: <b>{server.name}</b>\nCreate a peer on interface <b>{interface_id}</b>?",
        reply_markup=confirm_create_peer_keyboard(server_id, interface_id),
        parse_mode="HTML"
    )

@router.callback_query(IsRegistered(), F.data.startswith("peer_create_confirm_"))
async def do_peer_create(callback: CallbackQuery, session):
    _, _, _, server_id, interface_id = callback.data.split("_")
    server_id = int(server_id)
    server = await get_server_by_id(server_id)
    user_api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not user_api_data:
        logger.warning(f"User {callback.from_user.id} has no access to server (server_id={server_id})")
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)
        return
    try:
        result = await create_peer(
            session,
            api_url=server.api_url,
            api_user=user_api_data.api_login,
            api_pass=user_api_data.api_password,
            interface_id=interface_id,
            user_id=user_api_data.api_login
        )
        logger.info(f"Peer created for user {callback.from_user.id} on server {server_id}, interface {interface_id}")
        await callback.answer("✅ Peer created!")
        from app.bot.routers.peer_manager.handler import show_peers_for_server
        await show_peers_for_server(callback, session, server_id=server_id)
    except Exception as e:
        logger.error(f"Failed to create peer for user {callback.from_user.id} on server {server_id}: {e}")
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)

@router.callback_query(IsRegistered(), F.data.startswith("peer_create_back_"))
async def back_to_peers(callback: CallbackQuery, session):
    from app.bot.routers.peer_manager.handler import show_peers_for_server
    server_id = int(callback.data.split("_")[-1])
    await show_peers_for_server(callback, session, server_id=server_id)