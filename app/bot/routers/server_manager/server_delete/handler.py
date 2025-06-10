import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_all_servers, get_server_by_id, get_users_for_server, get_user_by_id
from app.db.crud import (
    delete_server_and_api_data,
    get_server_api_data_by_server_id_and_tg_id
)
from .keyboard import delete_server_keyboard, confirm_delete_keyboard
from app.wireguard_api.interfaces import get_all_interfaces
from app.wireguard_api.users import get_all_users
from app.bot.routers.server_manager.handler import open_server_manager
from app.bot.filters.is_admin import IsAdmin

logger = logging.getLogger("server_delete")

router = Router()

@router.callback_query(IsAdmin(), F.data == "delete_server_menu")
async def show_delete_server_menu(callback: CallbackQuery, session):
    servers = await get_all_servers()
    text = "<b>Select a server to delete:</b>" if servers else "<i>No servers available for deletion.</i>"
    await callback.message.edit_text(
        text,
        reply_markup=delete_server_keyboard(servers),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), F.data.startswith("delete_server_"))
async def confirm_delete_server(callback: CallbackQuery, session, state):
    server_id = int(callback.data.replace("delete_server_", ""))
    server = await get_server_by_id(server_id)
    if not server:
        await callback.answer("Server not found.", show_alert=True)
        logger.warning(f"User {callback.from_user.id} tried to access non-existent server {server_id}")
        return

    server_info = [
        "<b>Server info:</b>",
        f"Name: {server.name}",
        f"URL: {server.api_url}"
    ]
    if getattr(server, "description", None):
        server_info.append(f"Description: {server.description}")

    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    interfaces_block = []
    users_block = []
    error_block = ""
    api_accessible = False

    if api_data:
        try:
            interfaces = await get_all_interfaces(
                session,
                server.api_url,
                api_data.api_login,
                api_data.api_password
            )
            api_accessible = True
            interfaces_block.append("<b>Interface info:</b>")
            if interfaces:
                for idx, iface in enumerate(interfaces, 1):
                    name = iface.get('DisplayName') or iface.get('Identifier') or '—'
                    identifier = iface.get('Identifier') or '—'
                    total_peers = iface.get('TotalPeers', 0)
                    interfaces_block.append(
                        f"[{idx}] {name}[{identifier}]\nPeers: {total_peers}"
                    )
            else:
                interfaces_block.append("No interfaces found.")
        except Exception:
            error_block = "<blockquote>⚠️ Unable to get server data.</blockquote>"
            api_accessible = False

    user_ids = await get_users_for_server(server_id)
    users = []
    for uid in user_ids:
        user = await get_user_by_id(uid)
        if user:
            users.append(user)

    users_block.append("<b>Users info:</b>")
    if users:
        wg_users = []
        if api_accessible:
            try:
                wg_users = await get_all_users(
                    session,
                    server.api_url,
                    api_data.api_login,
                    api_data.api_password
                )
            except Exception:
                wg_users = []
        for idx, user in enumerate(users, 1):
            line = f"[{idx}] {user.tg_name or '-'}[{user.tg_id}]"
            if api_accessible and wg_users:
                peer_count = 0
                for u in wg_users:
                    if str(user.tg_id) == str(u.get('Identifier')):
                        peer_count = u.get('PeerCount', 0)
                        break
                line += f"\nPeers: {peer_count}"
            users_block.append(line)
    else:
        users_block.append("No users have access to this server.")

    data_blocks = [
        "\n".join(server_info),
        "\n".join(interfaces_block) if interfaces_block else "",
        "\n".join(users_block)
    ]
    data_text = "\n\n".join([block for block in data_blocks if block.strip()])

    text = (
        f"Delete server: <b>{server.name}</b>\n"
        f"{error_block if error_block else ''}"
        f"<blockquote>{data_text}</blockquote>\n"
        f"\nℹ️ <i>All data will be permanently deleted.</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=confirm_delete_keyboard(server_id),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), F.data.startswith("confirm_delete_"))
async def do_delete_server(callback: CallbackQuery, session):
    server_id = int(callback.data.replace("confirm_delete_", ""))
    server = await get_server_by_id(server_id)
    await delete_server_and_api_data(server_id)
    logger.info(f"Server '{server.name if server else server_id}' was deleted by user {callback.from_user.id}")
    await callback.answer("✅ Server and all related data deleted!")
    await open_server_manager(callback, session)

@router.callback_query(IsAdmin(), F.data == "delete_server_menu")
async def back_to_delete_menu(callback: CallbackQuery, session):
    await show_delete_server_menu(callback, session)

@router.callback_query(IsAdmin(), F.data == "back_to_server_manager")
async def back_to_server_manager(callback: CallbackQuery, session, state: dict = None):
    await open_server_manager(callback, session)