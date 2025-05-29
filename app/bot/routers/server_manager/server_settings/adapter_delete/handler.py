import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_server_by_id, get_server_api_data_by_server_id_and_tg_id
from app.bot.filters.is_admin import IsAdmin
from app.wireguard_api.interfaces import get_all_interfaces, delete_interface_by_id
from app.wireguard_api.metrics import get_interface_metrics
from app.bot.routers.server_manager.server_settings.adapter_delete.keyboard import (
    adapter_delete_select_keyboard,
    adapter_delete_confirm_keyboard,
)
from app.bot.routers.server_manager.server_settings.keyboard import server_settings_menu_keyboard

logger = logging.getLogger("adapter_delete")

router = Router()

async def show_adapters_list(event, session, server_id, error_text=None):
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, event.from_user.id)
    adapters_text = ""
    error_block = ""
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
                identifier = iface.get("Identifier") or "—"
                total_peers = iface.get("TotalPeers")
                peers_str = f"<b>{total_peers}</b> 👥" if total_peers is not None else "peers unknown"
                adapters_text += f"• <b>{name}</b> [{identifier}] | {peers_str}\n"
        else:
            adapters_text = "<b>Adapters:</b> No adapters found\n"
    except Exception as e:
        logger.error(f"Error loading adapters for server {server_id}: {e}")
        adapters_text = "<b>Adapters:</b> —\n"
        if error_text:
            error_block = f"<blockquote>⚠️ <b>{error_text}</b></blockquote>\n\n"

    text = (
        f"{error_block}"
        f"<b>Server settings menu:</b> <b>{server.name}</b>\n\n"
        f"{adapters_text}"
    )
    await event.message.edit_text(
        text,
        reply_markup=server_settings_menu_keyboard(server_id),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), F.data.regexp(r"^delete_adapter_\d+$"))
async def adapter_delete_entry(callback: CallbackQuery, session):
    server_id = int(callback.data.split("_")[2])
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        logger.warning(f"User {callback.from_user.id} tried to access unavailable server {server_id} for adapter delete")
        await callback.answer("No access to this server.", show_alert=True)
        return

    try:
        interfaces = await get_all_interfaces(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password
        )
    except Exception as e:
        logger.error(f"API error while getting interfaces for server {server_id}: {e}")
        await callback.answer("Failed to load adapters.", show_alert=True)
        return

    if not interfaces:
        await callback.answer("No adapters found on this server.", show_alert=True)
        return

    text = (
        f"<b>Select an adapter to delete on {server.name}:</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=adapter_delete_select_keyboard(server_id, interfaces),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), F.data.startswith("delete_adapter_select_"))
async def adapter_delete_select(callback: CallbackQuery, session):
    parts = callback.data.split("_")
    server_id = int(parts[3])
    iface_id = "_".join(parts[4:])
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        logger.warning(f"User {callback.from_user.id} tried to access unavailable server {server_id} for adapter delete")
        await callback.answer("No access to this server.", show_alert=True)
        return

    try:
        interfaces = await get_all_interfaces(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password
        )
        iface = next((i for i in interfaces if str(i.get("Identifier")) == iface_id), None)
    except Exception as e:
        logger.error(f"API error while getting interfaces for server {server_id}: {e}")
        await callback.answer("Failed to load adapters.", show_alert=True)
        return

    if not iface:
        await callback.answer("Adapter not found.", show_alert=True)
        return

    name = iface.get("DisplayName") or "—"
    identifier = iface.get("Identifier") or "—"
    total_peers = iface.get("TotalPeers", 0)
    try:
        metrics = await get_interface_metrics(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password,
            identifier
        )
        rx = metrics.get("RxBytes", 0)
        tx = metrics.get("TxBytes", 0)
    except Exception as e:
        logger.error(f"Error loading metrics for adapter {identifier} on server {server_id}: {e}")
        rx = tx = 0

    def human_bytes(num):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(num) < 1024.0:
                return f"{num:.0f} {unit}"
            num /= 1024.0
        return f"{num:.0f} PB"

    metrics_str = f"📥 {human_bytes(rx)} / 📤 {human_bytes(tx)}"

    text = (
        f"<b>Are you sure you want to delete the following adapter?</b>\n\n"
        f"<blockquote>{name} [{identifier}]\n"
        f"👥 {total_peers} Peers\n"
        f"{metrics_str}</blockquote>\n\n"
        f"ℹ️ <i>All peers for this adapter will be permanently deleted.</i>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=adapter_delete_confirm_keyboard(server_id, identifier),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), F.data.startswith("delete_adapter_confirm_"))
async def adapter_delete_confirm(callback: CallbackQuery, session):
    parts = callback.data.split("_")
    server_id = int(parts[3])
    iface_id = "_".join(parts[4:])
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        logger.warning(f"User {callback.from_user.id} tried to confirm delete on unavailable server {server_id}")
        await callback.answer("No access to this server.", show_alert=True)
        return

    try:
        await delete_interface_by_id(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password,
            iface_id
        )
        logger.info(f"Adapter {iface_id} deleted on server {server_id} by user {callback.from_user.id}")
        await callback.answer("✅ Adapter deleted successfully!")
        await show_adapters_list(callback, session, server_id)
    except Exception as e:
        logger.error(f"Error deleting adapter {iface_id} on server {server_id}: {e}")
        await callback.answer("Failed to delete adapter.", show_alert=True)
        await show_adapters_list(callback, session, server_id, error_text="Failed to delete adapter.")

@router.callback_query(IsAdmin(), F.data.startswith("delete_adapter_cancel_"))
async def adapter_delete_cancel(callback: CallbackQuery, session):
    parts = callback.data.split("_")
    server_id = int(parts[3])
    logger.info(f"Adapter delete cancelled by user {callback.from_user.id} for server {server_id}")
    await show_adapters_list(callback, session, server_id)