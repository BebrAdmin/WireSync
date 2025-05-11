import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_all_servers, get_server_by_id
from app.db.crud import (
    delete_server_and_api_data,
    get_server_api_data_by_server_id_and_tg_id
)
from .keyboard import delete_server_keyboard, confirm_delete_keyboard

from app.wireguard_api.interfaces import get_all_interfaces
from app.wireguard_api.users import get_all_users

from app.bot.routers.server_manager.handler import open_server_manager

logger = logging.getLogger("server_delete")

router = Router()

@router.callback_query(F.data == "delete_server_menu")
async def show_delete_server_menu(callback: CallbackQuery, session):
    servers = await get_all_servers()
    if servers:
        text = "Выберите сервер для удаления:"
    else:
        text = "Нет доступных серверов для удаления."
    await callback.message.edit_text(
        text,
        reply_markup=delete_server_keyboard(servers)
    )

@router.callback_query(F.data.startswith("delete_server_"))
async def confirm_delete_server(callback: CallbackQuery, session, state):
    server_id = int(callback.data.replace("delete_server_", ""))
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not api_data:
        await callback.answer("Нет доступа к этому серверу или сервер не найден.", show_alert=True)
        logger.warning(f"User {callback.from_user.id} tried to access or delete server {server_id} without permission")
        return

    server = await get_server_by_id(server_id)
    if not server:
        await callback.answer("Сервер не найден.", show_alert=True)
        logger.warning(f"User {callback.from_user.id} tried to access non-existent server {server_id}")
        return

    try:
        interfaces = await get_all_interfaces(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password
        )
        users = await get_all_users(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password
        )
    except Exception as e:
        await callback.answer(f"Ошибка API: {e}", show_alert=True)
        logger.error(f"API error while getting interfaces/users for server {server_id}: {e}")
        return

    def get_iface_name(iface):
        if isinstance(iface, dict):
            return iface.get('DisplayName') or iface.get('Identifier') or '—'
        return getattr(iface, 'DisplayName', getattr(iface, 'Identifier', '—'))

    def get_user_info(user):
        if isinstance(user, dict):
            identifier = user.get('Identifier', '—')
            fname = user.get('Firstname', '')
            lname = user.get('Lastname', '')
            peer_count = user.get('PeerCount', 0)
        else:
            identifier = getattr(user, 'Identifier', '—')
            fname = getattr(user, 'Firstname', '')
            lname = getattr(user, 'Lastname', '')
            peer_count = getattr(user, 'PeerCount', 0)
        return f"{identifier} {fname} {lname} {peer_count}".strip()

    text = (
        f"<b>Подтвердите удаление сервера:</b>\n"
        f"<b>Интерфейсы:</b>\n"
        + ("\n".join(f"• {get_iface_name(iface)}" for iface in interfaces) if interfaces else "Нет интерфейсов") +
        f"\n\n<b>Пользователи:</b>\n"
        + ("\n".join(f"• {get_user_info(user)}" for user in users) if users else "Нет пользователей")
    )

    await callback.message.edit_text(
        text,
        reply_markup=confirm_delete_keyboard(server_id),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("confirm_delete_"))
async def do_delete_server(callback: CallbackQuery, session):
    server_id = int(callback.data.replace("confirm_delete_", ""))
    server = await get_server_by_id(server_id)
    await delete_server_and_api_data(server_id)
    logger.info(f"Server '{server.name if server else server_id}' was deleted by user {callback.from_user.id}")
    await callback.answer("✅Сервер и связанные данные удалены!")
    await open_server_manager(callback, session)

@router.callback_query(F.data == "delete_server_menu")
async def back_to_delete_menu(callback: CallbackQuery, session):
    await show_delete_server_menu(callback, session)

@router.callback_query(F.data == "back_to_server_manager")
async def back_to_server_manager(callback: CallbackQuery, session, state: dict = None):
    await open_server_manager(callback, session)