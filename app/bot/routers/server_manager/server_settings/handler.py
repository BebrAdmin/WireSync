from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_all_servers, get_server_by_id, get_server_api_data_by_server_id_and_tg_id
from .keyboard import select_server_for_settings_keyboard, server_settings_menu_keyboard
from app.bot.routers.server_manager.handler import open_server_manager
from app.wireguard_api.interfaces import get_all_interfaces

router = Router()

@router.callback_query(F.data == "settings_server_menu")
async def show_settings_server_menu(callback: CallbackQuery, session):
    servers = await get_all_servers()
    if servers:
        text = "Select a server to configure:"
    else:
        text = "No available servers for configuration."
    await callback.message.edit_text(
        text,
        reply_markup=select_server_for_settings_keyboard(servers)
    )

@router.callback_query(F.data.startswith("settings_server_"))
async def show_server_settings_menu(callback: CallbackQuery, session):
    server_id = int(callback.data.replace("settings_server_", ""))
    server = await get_server_by_id(server_id)
    if not server:
        await callback.answer("Server not found.", show_alert=True)
        return

    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    adapters_text = ""
    if api_data:
        try:
            interfaces = await get_all_interfaces(
                session,
                server.api_url,
                api_data.api_login,
                api_data.api_password
            )
            if interfaces:
                adapters_text = "<b>Adapters:</b>\n"
                for iface in interfaces:
                    name = iface.get("DisplayName") or "—"
                    total_peers = iface.get("TotalPeers")
                    peers_str = f"<b>{total_peers}</b> 👥" if total_peers is not None else "peers unknown"
                    adapters_text += f"🔹 <b>{name}</b> | {peers_str}\n"
            else:
                adapters_text = "<b>Adapters:</b> No adapters found\n"
        except Exception as e:
            await callback.answer("Failed to load adapters.", show_alert=True)
            adapters_text = "<b>Adapters:</b> —\n"
    else:
        await callback.answer("No API access for this server.", show_alert=True)
        adapters_text = "<b>No API access for this server.</b>\n"

    text = (
        f"<b>Server settings menu:</b> <b>{server.name}</b>\n\n"
        f"{adapters_text}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=server_settings_menu_keyboard(server_id),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_server_manager")
async def back_to_server_manager(callback: CallbackQuery, session):
    await open_server_manager(callback, session)