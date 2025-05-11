import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_server_by_id, get_server_api_data_by_server_id_and_tg_id
from app.bot.routers.server_manager.server_settings.keyboard import server_settings_menu_keyboard
from app.wireguard_api.interfaces import prepare_interface, create_interface, get_all_interfaces

logger = logging.getLogger("adapter_create")

router = Router()

@router.callback_query(F.data.startswith("add_adapter_"))
async def add_adapter(callback: CallbackQuery, session):
    server_id = int(callback.data.replace("add_adapter_", ""))
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        await callback.answer("Нет доступа к серверу или сервер не найден.", show_alert=True)
        return

    try:
        interface_data = await prepare_interface(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password
        )
    except Exception as e:
        logger.error(f"Error in prepare_interface for server {server_id}: {e}")
        await callback.answer(f"Ошибка prepare_interface: {e}", show_alert=True)
        return

    try:
        await create_interface(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password,
            interface_data
        )
        logger.info(
            f"Adapter created for server '{server.name}' (id={server.id}) by user {callback.from_user.id}"
        )
        await callback.answer("✅ Адаптер успешно создан!")
    except Exception as e:
        logger.error(f"Error creating adapter for server {server_id}: {e}")
        await callback.answer(f"Ошибка создания адаптера: {e}", show_alert=True)
        return

    adapters_text = ""
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

    text = (
        f"<b>Меню настроек для сервера:</b> <b>{server.name}</b>\n\n"
        f"{adapters_text}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=server_settings_menu_keyboard(server_id),
        parse_mode="HTML"
    )