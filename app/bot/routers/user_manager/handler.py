import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_all_users, get_servers_for_user, get_all_servers
from app.db import get_server_api_data_by_server_id_and_user_id
from app.wireguard_api.provisioning import get_user_peer_info
from .keyboard import users_manager_keyboard
from app.bot.filters.is_admin import IsAdmin

logger = logging.getLogger("user_manager")
router = Router()

async def build_users_info(users, servers, session):
    lines = []
    unresponsive_servers = set()
    for idx, user in enumerate(users, 1):
        servers_ids = await get_servers_for_user(user.id)
        user_servers = [s for s in servers if s.id in servers_ids]
        peers_info = []
        for server in user_servers:
            api_data = await get_server_api_data_by_server_id_and_user_id(server.id, user.id)
            peer_count = "-"
            if api_data:
                try:
                    user_peer_info = await get_user_peer_info(
                        session,
                        api_url=server.api_url,
                        api_user=api_data.api_login,
                        api_pass=api_data.api_password,
                        user_id=api_data.api_login
                    )
                    peer_count = len(user_peer_info.get("Peers", []))
                except Exception:
                    peer_count = "?"
                    unresponsive_servers.add(server.name)
            peers_info.append(f"{server.name}({peer_count})")
        peers_block = ", ".join(peers_info) if peers_info else "—"
        lines.append(
            f"[{idx}] <b>{user.tg_name or user.email or user.tg_id}</b> "
            f"({'Admin' if user.is_admin else 'User'})\n"
            f"ID: <code>{user.tg_id}</code> | Email: <code>{user.email or '-'}</code>\n"
            f"Servers/Peers: {peers_block}"
        )
    warn_block = ""
    if unresponsive_servers:
        warn_block = "<blockquote>⚠️ Server " + ", ".join(unresponsive_servers) + " is not responding</blockquote>\n\n"
    return warn_block + "<blockquote>" + "\n\n".join(lines) + "</blockquote>"

@router.callback_query(IsAdmin(), F.data == "user_manager_menu")
async def show_user_manager_menu(callback: CallbackQuery, session):
    users = await get_all_users()
    servers = await get_all_servers()
    users_info = await build_users_info(users, servers, session)
    await callback.message.edit_text(
        "<b>Users Manager:</b>\n" + users_info,
        reply_markup=users_manager_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), F.data == "user_manager_back")
async def user_manager_back(callback: CallbackQuery):
    from app.bot.routers.main.handler import main_menu_callback
    await main_menu_callback(callback)