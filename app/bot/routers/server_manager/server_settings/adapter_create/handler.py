import logging
import json
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.db import get_server_by_id, get_server_api_data_by_server_id_and_tg_id
from app.bot.routers.server_manager.server_settings.keyboard import server_settings_menu_keyboard
from app.bot.routers.server_manager.server_settings.adapter_create.keyboard import (
    adapter_create_confirm_keyboard,
    adapter_create_custom_keyboard,
)
from app.wireguard_api.interfaces import prepare_interface, create_interface, get_all_interfaces
from app.bot.filters.is_admin import IsAdmin
from .fsm import AdapterCreateState

logger = logging.getLogger("adapter_create")

router = Router()

EDITABLE_FIELDS = [
    "DisplayName", "Mode", "Dns", "DnsSearch", "Mtu",
    "PeerDefDns", "PeerDefDnsSearch", "PeerDefEndpoint",
    "PeerDefAllowedIPs", "PeerDefMtu", "PeerDefPersistentKeepalive"
]

READONLY_FIELDS = [
    "Identifier", "ListenPort", "Addresses"
]

def filter_editable_fields(interface_data):
    return {k: v for k, v in interface_data.items() if k in EDITABLE_FIELDS}

def get_readonly_fields(interface_data):
    return {k: v for k, v in interface_data.items() if k in READONLY_FIELDS}

def validate_adapter_config(data):
    if not isinstance(data, dict):
        return False, "Config must be a JSON object."
    for k in data:
        if k not in EDITABLE_FIELDS:
            return False, f"Field '{k}' is not editable."
    if "DisplayName" in data and len(data["DisplayName"]) > 64:
        return False, "DisplayName must not exceed 64 characters."
    if "Mtu" in data and not (1 <= int(data["Mtu"]) <= 9000):
        return False, "Mtu must be in range 1–9000."
    if "PeerDefMtu" in data and not (1 <= int(data["PeerDefMtu"]) <= 9000):
        return False, "PeerDefMtu must be in range 1–9000."
    return True, None

def readonly_fields_text(readonly):
    lines = []
    for k, v in readonly.items():
        if isinstance(v, list):
            value = ", ".join(str(x) for x in v)
        else:
            value = str(v)
        lines.append(f"{k}: <code>{value}</code>")
    return "\n".join(lines)

def get_custom_config_text(readonly, custom_config, error_text=None, raw_text=None):
    error_block = ""
    if error_text:
        error_block = f"<blockquote>⚠️ <b>Error:</b> <i>{error_text}</i></blockquote>\n\n"
    config_block = (
        f"<pre>{raw_text}</pre>" if raw_text is not None
        else f"<pre>{json.dumps(custom_config, indent=2, ensure_ascii=False)}</pre>"
    )
    return (
        f"{error_block}"
        "🔒 <b>Read-only fields:</b>\n"
        f"{readonly_fields_text(readonly)}\n\n"
        "✏️ <b>Your configuration:</b>\n"
        f"{config_block}\n\n"
        "ℹ️ <i>Send the updated configuration in the chat or use the buttons below.</i>"
    )

def extract_api_error_message(error: Exception) -> str:
    match = re.search(r'"Message":"(?:[^"]*?: )*([^"]+)"', str(error))
    if match:
        return match.group(1)
    match2 = re.search(r'(failed to [^"]+)', str(error))
    if match2:
        return match2.group(1)
    return str(error)

@router.callback_query(IsAdmin(), F.data.startswith("add_adapter_"))
async def add_adapter(callback: CallbackQuery, state: FSMContext, session):
    server_id = int(callback.data.replace("add_adapter_", ""))
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        await callback.answer("No access to this server or server not found.", show_alert=True)
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
        await callback.answer("Failed to load adapter template.", show_alert=True)
        return

    editable = filter_editable_fields(interface_data)
    readonly = get_readonly_fields(interface_data)
    await state.set_data({
        "server_id": server_id,
        "interface_template": editable,
        "full_template": interface_data,
        "api_login": api_data.api_login,
        "api_password": api_data.api_password,
        "api_url": server.api_url,
        "server_name": server.name,
        "bot_message_id": callback.message.message_id,
        "custom_config": None,
        "json_parse_error": False,
        "raw_text": None
    })
    text = (
        "🔒 <b>Read-only fields:</b>\n"
        f"{readonly_fields_text(readonly)}\n\n"
        "✏️ <b>Editable template:</b>\n"
        f"<pre>{json.dumps(editable, indent=2, ensure_ascii=False)}</pre>\n\n"
        "ℹ️ <i>Send the updated configuration in the chat or use the buttons below.</i>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=adapter_create_confirm_keyboard(server_id),
        parse_mode="HTML"
    )
    await state.set_state(AdapterCreateState.waiting_confirm)

@router.callback_query(IsAdmin(), F.data.startswith("adapter_create_confirm_"), StateFilter(AdapterCreateState.waiting_confirm))
async def adapter_create_confirm(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    config = data["full_template"]
    try:
        await create_interface(
            session,
            data["api_url"],
            data["api_login"],
            data["api_password"],
            config
        )
        logger.info(
            f"Adapter created for server '{data['server_name']}' (id={data['server_id']}) by user {callback.from_user.id}"
        )
        await callback.answer("✅ Adapter created successfully!")
        await show_adapters_list(callback, session, data["server_id"])
        await state.clear()
    except Exception as e:
        logger.error(f"Error creating adapter for server {data['server_id']}: {e}")
        await callback.answer(extract_api_error_message(e), show_alert=True)

@router.message(IsAdmin(), StateFilter(AdapterCreateState.waiting_confirm, AdapterCreateState.custom_config))
async def adapter_create_custom(message: Message, state: FSMContext, session):
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    server_id = data["server_id"]
    readonly = get_readonly_fields(data["full_template"])
    user_text = message.text

    try:
        user_json = json.loads(user_text)
        json_parse_error = False
    except Exception:
        user_json = {}
        json_parse_error = True

    await message.delete()
    if json_parse_error:
        await message.bot.edit_message_text(
            get_custom_config_text(readonly, {}, error_text="Invalid JSON format.", raw_text=user_text),
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=adapter_create_custom_keyboard(server_id),
            parse_mode="HTML"
        )
        await state.set_state(AdapterCreateState.custom_config)
        await state.update_data(custom_config=None, json_parse_error=True, raw_text=user_text)
        return

    ok, err = validate_adapter_config(user_json)
    if not ok:
        await message.bot.edit_message_text(
            get_custom_config_text(readonly, user_json, error_text=err),
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=adapter_create_custom_keyboard(server_id),
            parse_mode="HTML"
        )
        await state.set_state(AdapterCreateState.custom_config)
        await state.update_data(custom_config=user_json, json_parse_error=False, raw_text=None)
        return

    await message.bot.edit_message_text(
        get_custom_config_text(readonly, user_json),
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=adapter_create_custom_keyboard(server_id),
        parse_mode="HTML"
    )
    await state.set_state(AdapterCreateState.custom_config)
    await state.update_data(custom_config=user_json, json_parse_error=False, raw_text=None)

@router.callback_query(IsAdmin(), F.data.startswith("adapter_create_custom_confirm_"), StateFilter(AdapterCreateState.custom_config))
async def adapter_create_custom_confirm(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    server_id = data["server_id"]
    json_parse_error = data.get("json_parse_error", False)
    raw_text = data.get("raw_text")
    custom_config = data.get("custom_config")
    if json_parse_error or not custom_config:
        await callback.answer("Error: Invalid JSON format. Please fix your config.", show_alert=True)
        return

    ok, err = validate_adapter_config(custom_config)
    if not ok:
        await callback.answer(f"Validation error: {err}", show_alert=True)
        return

    config = data["full_template"].copy()
    config.update(custom_config)
    try:
        await create_interface(
            session,
            data["api_url"],
            data["api_login"],
            data["api_password"],
            config
        )
        logger.info(
            f"Adapter created (custom) for server '{data['server_name']}' (id={server_id}) by user {callback.from_user.id}"
        )
        await callback.answer("✅ Adapter created successfully!")
        await show_adapters_list(callback, session, server_id)
        await state.clear()
    except Exception as e:
        logger.error(f"Error creating adapter for server {server_id}: {e}")
        await callback.answer(extract_api_error_message(e), show_alert=True)

@router.callback_query(IsAdmin(), F.data.startswith("adapter_create_reset_"), StateFilter(AdapterCreateState.custom_config))
async def adapter_create_reset(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    server_id = data["server_id"]
    editable = data["interface_template"]
    readonly = get_readonly_fields(data["full_template"])
    bot_message_id = data["bot_message_id"]
    text = (
        "🔒 <b>Read-only fields:</b>\n"
        f"{readonly_fields_text(readonly)}\n\n"
        "✏️ <b>Editable template:</b>\n"
        f"<pre>{json.dumps(editable, indent=2, ensure_ascii=False)}</pre>\n\n"
        "ℹ️ <i>Send the updated configuration in the chat or use the buttons below.</i>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=adapter_create_confirm_keyboard(server_id),
        parse_mode="HTML"
    )
    await state.set_state(AdapterCreateState.waiting_confirm)
    await state.update_data(custom_config=None, json_parse_error=False, raw_text=None)

@router.callback_query(IsAdmin(), F.data.startswith("adapter_create_cancel_"), StateFilter(AdapterCreateState.waiting_confirm, AdapterCreateState.custom_config))
async def adapter_create_cancel(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    await show_adapters_list(callback, session, data["server_id"])
    await state.clear()

async def show_adapters_list(event, session, server_id, state: FSMContext = None):
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, event.from_user.id)
    adapters_text = ""
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
                adapters_text += f"• <b>{name}</b> | {peers_str}\n"
        else:
            adapters_text = "<b>Adapters:</b> No adapters found\n"
    except Exception as e:
        adapters_text = f"<b>Error loading adapters:</b> {e}\n"

    text = (
        f"<b>Server settings menu:</b> <b>{server.name}</b>\n\n"
        f"{adapters_text}"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text,
            reply_markup=server_settings_menu_keyboard(server_id),
            parse_mode="HTML"
        )
    elif state is not None:
        data = await state.get_data()
        bot_message_id = data.get("bot_message_id")
        if bot_message_id:
            await event.bot.edit_message_text(
                text,
                chat_id=event.chat.id,
                message_id=bot_message_id,
                reply_markup=server_settings_menu_keyboard(server_id),
                parse_mode="HTML"
            )