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
        text = "Выберите сервер для настройки:"
    else:
        text = "Нет доступных серверов для настройки."
    await callback.message.edit_text(
        text,
        reply_markup=select_server_for_settings_keyboard(servers)
    )

@router.callback_query(F.data.startswith("settings_server_"))
async def show_server_settings_menu(callback: CallbackQuery, session):
    server_id = int(callback.data.replace("settings_server_", ""))
    server = await get_server_by_id(server_id)
    if not server:
        await callback.answer("Сервер не найден.", show_alert=True)
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
                adapters_text = "<b>Адаптеры:</b>\n"
                for iface in interfaces:
                    name = iface.get("DisplayName") or iface.get("Identifier") or "—"
                    adapters_text += f"• <b>{name}</b>\n"
            else:
                adapters_text = "<b>Адаптеры:</b> Нет адаптеров\n"
        except Exception as e:
            adapters_text = f"<b>Ошибка получения адаптеров:</b> {e}\n"
    else:
        adapters_text = "<b>Нет доступа к API для этого сервера.</b>\n"

    text = (
        f"<b>Меню настроек для сервера:</b> <b>{server.name}</b>\n\n"
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