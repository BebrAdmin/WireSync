import logging
import json
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.db import get_server_by_id, get_server_api_data_by_server_id_and_tg_id
from app.wireguard_api.interfaces import get_interface_by_id, update_interface_by_id, get_all_interfaces
from app.bot.filters.is_admin import IsAdmin
from .fsm import AdapterUpdateState
from .keyboard import adapter_update_custom_keyboard, adapter_update_select_keyboard
from app.bot.routers.server_manager.server_settings.adapter_delete.handler import show_adapters_list

logger = logging.getLogger("adapter_update")

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
        return False, "The configuration must be a valid JSON object."
    for k in data:
        if k not in EDITABLE_FIELDS:
            return False, f"The field '{k}' is not editable."
    if "DisplayName" in data and len(data["DisplayName"]) > 64:
        return False, "DisplayName must not exceed 64 characters."
    if "Mtu" in data and not (1 <= int(data["Mtu"]) <= 9000):
        return False, "MTU must be in range 1–9000."
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
        "ℹ️ <i>Send the updated configuration in the chat or use the buttons below.\n"
        "After updating the adapter, you will need to recreate the peers for clients to apply the new settings.</i>"
    )

def extract_api_error_message(error: Exception) -> str:
    match = re.search(r'"Message":"(?:[^"]*?: )*([^"]+)"', str(error))
    if match:
        return match.group(1)
    match2 = re.search(r'(failed to [^"]+)', str(error))
    if match2:
        return match2.group(1)
    return str(error)

@router.callback_query(IsAdmin(), F.data.startswith("update_adapter_"))
async def update_adapter_select(callback: CallbackQuery, session):
    server_id = int(callback.data.replace("update_adapter_", ""))
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        await callback.answer("You do not have access to this server.", show_alert=True)
        return

    try:
        interfaces = await get_all_interfaces(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password
        )
    except Exception as e:
        await callback.answer("Failed to load adapters. Please try again later.", show_alert=True)
        return

    if not interfaces:
        await callback.answer("No adapters found on this server.", show_alert=True)
        return

    text = (
        f"<b>Select an adapter to update on {server.name}:</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=adapter_update_select_keyboard(server_id, interfaces),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), F.data.regexp(r"^adapter_update_\d+_.+"))
async def adapter_update_entry(callback: CallbackQuery, state: FSMContext, session):
    parts = callback.data.split("_")
    server_id = int(parts[2])
    iface_id = "_".join(parts[3:])
    server = await get_server_by_id(server_id)
    api_data = await get_server_api_data_by_server_id_and_tg_id(server_id, callback.from_user.id)
    if not server or not api_data:
        await callback.answer("You do not have access to this server or the server was not found.", show_alert=True)
        return

    try:
        interface_data = await get_interface_by_id(
            session,
            server.api_url,
            api_data.api_login,
            api_data.api_password,
            iface_id
        )
    except Exception as e:
        logger.error(f"Error in get_interface_by_id for server {server_id}: {e}")
        await callback.answer("Failed to load adapter configuration. Please try again later.", show_alert=True)
        return

    editable = filter_editable_fields(interface_data)
    readonly = get_readonly_fields(interface_data)
    await state.set_data({
        "server_id": server_id,
        "iface_id": iface_id,
        "interface_template": editable,
        "full_template": interface_data,
        "api_login": api_data.api_login,
        "api_password": api_data.api_password,
        "api_url": server.api_url,
        "server_name": server.name,
        "bot_message_id": callback.message.message_id,
        "custom_config": editable,
        "json_parse_error": False,
        "raw_text": None,
        "last_bot_text": None
    })
    text = get_custom_config_text(readonly, editable)
    if callback.message.text != text or callback.message.reply_markup != adapter_update_custom_keyboard(server_id, iface_id):
        await callback.message.edit_text(
            text,
            reply_markup=adapter_update_custom_keyboard(server_id, iface_id),
            parse_mode="HTML"
        )
    await state.update_data(last_bot_text=text)
    await state.set_state(AdapterUpdateState.custom_config)

@router.message(IsAdmin(), StateFilter(AdapterUpdateState.custom_config))
async def adapter_update_custom_message(message: Message, state: FSMContext, session):
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    server_id = data["server_id"]
    iface_id = data["iface_id"]
    readonly = get_readonly_fields(data["full_template"])
    user_text = message.text

    try:
        user_json = json.loads(user_text)
        json_parse_error = False
    except Exception:
        user_json = {}
        json_parse_error = True

    await message.delete()
    new_text = get_custom_config_text(
        readonly,
        user_json if not json_parse_error else {},
        error_text="Invalid JSON format." if json_parse_error else None,
        raw_text=user_text if json_parse_error else None
    )
    last_text = data.get("last_bot_text")
    if new_text == last_text:
        return

    await message.bot.edit_message_text(
        new_text,
        chat_id=message.chat.id,
        message_id=bot_message_id,
        reply_markup=adapter_update_custom_keyboard(server_id, iface_id),
        parse_mode="HTML"
    )
    await state.update_data(
        custom_config=None if json_parse_error else user_json,
        json_parse_error=json_parse_error,
        raw_text=user_text if json_parse_error else None,
        last_bot_text=new_text
    )

@router.callback_query(IsAdmin(), F.data.startswith("adapter_update_custom_confirm_"), StateFilter(AdapterUpdateState.custom_config))
async def adapter_update_custom_confirm(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    server_id = data["server_id"]
    iface_id = data["iface_id"]
    json_parse_error = data.get("json_parse_error", False)
    custom_config = data.get("custom_config")
    if json_parse_error or not custom_config:
        await callback.answer("The configuration is not valid JSON. Please correct the format and try again.", show_alert=True)
        return

    ok, err = validate_adapter_config(custom_config)
    if not ok:
        await callback.answer(f"Validation error: {err}", show_alert=True)
        return

    config = data["full_template"].copy()
    config.update(custom_config)
    if config == data["full_template"]:
        await callback.answer("No changes detected. The configuration is already up to date.", show_alert=True)
        return

    try:
        await update_interface_by_id(
            session,
            data["api_url"],
            data["api_login"],
            data["api_password"],
            iface_id,
            config
        )
        logger.info(
            f"Adapter updated for server '{data['server_name']}' (id={server_id}) by user {callback.from_user.id}"
        )
        await callback.answer("✅Adapter successfully updated!")
        await show_adapters_list(callback, session, server_id)
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating adapter for server {server_id}: {e}")
        await callback.answer(f"Failed to update adapter: {extract_api_error_message(e)}", show_alert=True)

@router.callback_query(IsAdmin(), F.data.startswith("adapter_update_reset_"), StateFilter(AdapterUpdateState.custom_config))
async def adapter_update_reset(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    server_id = data["server_id"]
    iface_id = data["iface_id"]
    try:
        interface_data = await get_interface_by_id(
            session,
            data["api_url"],
            data["api_login"],
            data["api_password"],
            iface_id
        )
    except Exception as e:
        await callback.answer("Failed to reload the adapter configuration. Please try again later.", show_alert=True)
        return

    editable = filter_editable_fields(interface_data)
    readonly = get_readonly_fields(interface_data)
    if editable == data.get("custom_config"):
        await callback.answer("The configuration is already up to date. No reset is required.", show_alert=True)
        return

    text = get_custom_config_text(readonly, editable)
    if callback.message.text != text or callback.message.reply_markup != adapter_update_custom_keyboard(server_id, iface_id):
        await callback.message.edit_text(
            text,
            reply_markup=adapter_update_custom_keyboard(server_id, iface_id),
            parse_mode="HTML"
        )
    await state.update_data(custom_config=editable, json_parse_error=False, raw_text=None, last_bot_text=text)

@router.callback_query(IsAdmin(), F.data.startswith("adapter_update_cancel_"))
async def adapter_update_cancel(callback: CallbackQuery, state: FSMContext, session):
    parts = callback.data.split("_")
    try:
        server_id = int(parts[3])
    except (IndexError, ValueError):
        await callback.answer("Unable to determine the server. Please try again.", show_alert=True)
        await state.clear()
        return
    await show_adapters_list(callback, session, server_id)
    await state.clear()

@router.callback_query(F.data.regexp(r"^settings_server_\d+$"))
async def back_to_server_settings(callback: CallbackQuery, session):
    server_id = int(callback.data.replace("settings_server_", ""))
    from app.bot.routers.server_manager.server_settings.handler import show_server_settings_menu
    await show_server_settings_menu(callback, session)