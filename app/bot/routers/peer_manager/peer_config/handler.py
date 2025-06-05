import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from app.wireguard_api.peers import get_peer_by_id
from app.wireguard_api.provisioning import get_peer_config, get_peer_qr
from .keyboard import peer_menu_keyboard, peer_config_close_keyboard
from app.db import get_server_by_id, get_server_api_data_by_server_id_and_tg_id
from app.bot.filters.is_registered import IsRegistered

router = Router()

@router.callback_query(IsRegistered(), F.data.startswith("peer_manager_peer_"))
async def show_peer_menu(callback: CallbackQuery, session):
    try:
        parts = callback.data.split("_")
        server_id = int(parts[3])
        peer_id = parts[4]
        server = await get_server_by_id(server_id)
        api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
        if not server or not api_data:
            await callback.answer("Server is not available", show_alert=True)
            from app.bot.routers.peer_manager.handler import show_peer_manager_menu
            await show_peer_manager_menu(callback, session)
            return
        peer = await get_peer_by_id(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            peer_id=peer_id
        )
        important_fields = [
            "DisplayName", "Identifier", "InterfaceIdentifier", "AllowedIPs",
            "Addresses", "PublicKey", "Endpoint"
        ]
        peer_short = {k: peer.get(k) for k in important_fields if k in peer}
        peer_json = json.dumps(peer_short, indent=2)
        text = (
            f"Peer info: <b>{server.name}</b>\n"
            f"<blockquote><pre>{peer_json}</pre></blockquote>\n"
            f"\n<i>ℹ️ You can get a QR code or configuration file using the buttons below.</i>"
        )
        await callback.message.edit_text(
            text,
            reply_markup=peer_menu_keyboard(server_id, peer_id),
            parse_mode="HTML"
        )
    except Exception:
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)

@router.callback_query(IsRegistered(), F.data.startswith("peer_config_file_"))
async def send_peer_config(callback: CallbackQuery, session):
    try:
        parts = callback.data.split("_")
        server_id = int(parts[3])
        peer_id = parts[4]
        server = await get_server_by_id(server_id)
        api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
        if not server or not api_data:
            await callback.answer("Server is not available", show_alert=True)
            from app.bot.routers.peer_manager.handler import show_peer_manager_menu
            await show_peer_manager_menu(callback, session)
            return
        config = await get_peer_config(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            peer_id=peer_id
        )
        await callback.message.answer_document(
            BufferedInputFile(config.encode("utf-8"), filename="wg-peer.conf"),
            reply_markup=peer_config_close_keyboard()
        )
        await callback.answer()
    except Exception:
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)

@router.callback_query(IsRegistered(), F.data.startswith("peer_config_qr_"))
async def send_peer_qr(callback: CallbackQuery, session):
    try:
        parts = callback.data.split("_")
        server_id = int(parts[3])
        peer_id = parts[4]
        server = await get_server_by_id(server_id)
        api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
        if not server or not api_data:
            await callback.answer("Server is not available", show_alert=True)
            from app.bot.routers.peer_manager.handler import show_peer_manager_menu
            await show_peer_manager_menu(callback, session)
            return
        qr = await get_peer_qr(
            session,
            api_url=server.api_url,
            api_user=api_data.api_login,
            api_pass=api_data.api_password,
            peer_id=peer_id
        )
        await callback.message.answer_photo(
            BufferedInputFile(qr, filename="peer-qr.png"),
            reply_markup=peer_config_close_keyboard()
        )
        await callback.answer()
    except Exception:
        await callback.answer("Server is not available", show_alert=True)
        from app.bot.routers.peer_manager.handler import show_peer_manager_menu
        await show_peer_manager_menu(callback, session)

@router.callback_query(F.data == "peer_config_close")
async def close_peer_config_message(callback: CallbackQuery):
    await callback.message.delete()

@router.callback_query(IsRegistered(), F.data.startswith("peer_config_back_"))
async def back_to_peers(callback: CallbackQuery, session):
    from app.bot.routers.peer_manager.handler import show_peers_for_server
    parts = callback.data.split("_")
    server_id = int(parts[-1])
    await show_peers_for_server(callback, session, server_id=server_id)