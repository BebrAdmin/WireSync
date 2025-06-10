import logging
import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from .fsm import ServerRegisterState
from .keyboard import (
    server_register_custom_keyboard,
    server_register_select_users_keyboard,
    server_register_no_users_keyboard,
    server_register_post_add_keyboard,
)
from app.db import (
    create_server, get_server_by_name, get_server_by_api_url,
    create_server_api_data, get_user_by_tg_id, get_all_servers,
    get_all_users, add_user_server_access
)
from app.bot.routers.server_manager.handler import open_server_manager
from app.bot.routers.server_manager.server_settings.handler import show_server_settings_menu, show_settings_server_menu
from app.wireguard_api.interfaces import get_all_interfaces
from app.bot.tasks.user_sync import sync_all_users_on_servers
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger("server_register")

router = Router()

SERVER_CONFIG_FIELDS = [
    "Server_name",
    "Description",
    "Api_url",
    "Api_login",
    "Api_token",
    "Password"
]

SERVER_CONFIG_TEMPLATE = {
    "Server_name": "MyServer",
    "Description": "Description of the server",
    "Api_url": "https://example.com/api",
    "Api_login": "admin",
    "Api_token": "your_api_token",
    "Password": "your_password"
}

def validate_server_config(data):
    if not isinstance(data, dict):
        return False, "The configuration must be a valid JSON object."
    for field in SERVER_CONFIG_FIELDS:
        if field not in data:
            return False, f"Missing required field: {field}"
    if not data["Server_name"] or not isinstance(data["Server_name"], str):
        return False, "Server_name must be a non-empty string."
    if not data["Api_url"].startswith("http://") and not data["Api_url"].startswith("https://"):
        return False, "Api_url must start with http:// or https://"
    if not data["Api_login"]:
        return False, "Api_login must not be empty."
    if not (32 <= len(data["Api_token"]) <= 64):
        return False, "Api_token must be 32-64 characters."
    if not (16 <= len(data["Password"]) <= 64):
        return False, "Password must be 16-64 characters."
    return True, None

def get_custom_config_text(config, error_text=None, raw_text=None):
    error_block = ""
    if error_text:
        error_block = f"<blockquote>⚠️ <b>Error:</b> <i>{error_text}</i></blockquote>\n\n"
    config_block = (
        f"<pre>{raw_text}</pre>" if raw_text is not None
        else f"<pre>{json.dumps(config, indent=2, ensure_ascii=False)}</pre>"
    )
    return (
        f"{error_block}"
        "<b>Server configuration template:</b>\n"
        f"{config_block}\n\n"
        "ℹ️ <i>Paste your configuration above and use the buttons below.</i>"
    )

@router.callback_query(F.data == "register_server")
async def start_register_server(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ServerRegisterState.custom_config)
    msg = await callback.message.edit_text(
        get_custom_config_text(SERVER_CONFIG_TEMPLATE),
        reply_markup=server_register_custom_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(
        bot_message_id=msg.message_id,
        custom_config=None,
        json_parse_error=False,
        raw_text=None,
        last_bot_text=msg.text
    )

@router.message(StateFilter(ServerRegisterState.custom_config))
async def server_register_custom_config(message: Message, state: FSMContext, session):
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    user_text = message.text

    try:
        user_json = json.loads(user_text)
        json_parse_error = False
    except Exception:
        user_json = {}
        json_parse_error = True

    await message.delete()
    if json_parse_error:
        new_text = get_custom_config_text(
            SERVER_CONFIG_TEMPLATE,
            error_text="Invalid JSON format.",
            raw_text=user_text
        )
        last_text = data.get("last_bot_text")
        if new_text == last_text:
            return
        try:
            await message.bot.edit_message_text(
                new_text,
                chat_id=message.chat.id,
                message_id=bot_message_id,
                reply_markup=server_register_custom_keyboard(),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                logger.error(f"Edit message error: {e}")
        await state.update_data(custom_config=None, json_parse_error=True, raw_text=user_text, last_bot_text=new_text)
        return

    ok, err = validate_server_config(user_json)
    if not ok:
        new_text = get_custom_config_text(
            user_json,
            error_text=err,
            raw_text=None
        )
        last_text = data.get("last_bot_text")
        if new_text == last_text:
            return
        try:
            await message.bot.edit_message_text(
                new_text,
                chat_id=message.chat.id,
                message_id=bot_message_id,
                reply_markup=server_register_custom_keyboard(),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                logger.error(f"Edit message error: {e}")
        await state.update_data(custom_config=None, json_parse_error=False, raw_text=None, last_bot_text=new_text)
        return

    new_text = get_custom_config_text(user_json)
    last_text = data.get("last_bot_text")
    if new_text == last_text:
        return
    try:
        await message.bot.edit_message_text(
            new_text,
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=server_register_custom_keyboard(),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.error(f"Edit message error: {e}")
    await state.update_data(custom_config=user_json, json_parse_error=False, raw_text=None, last_bot_text=new_text)

@router.callback_query(F.data == "server_register_apply", StateFilter(ServerRegisterState.custom_config))
async def server_register_apply(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    config = data.get("custom_config")
    json_parse_error = data.get("json_parse_error", False)
    if json_parse_error or not config:
        await callback.answer("Please paste a valid configuration first.", show_alert=True)
        return

    if await get_server_by_name(config["Server_name"]):
        await callback.answer("Server with this name already exists.", show_alert=True)
        return
    if await get_server_by_api_url(config["Api_url"]):
        await callback.answer("Server with this API URL already exists.", show_alert=True)
        return

    try:
        await get_all_interfaces(
            session=session,
            api_url=config["Api_url"],
            api_user=config["Api_login"],
            api_pass=config["Api_token"]
        )
    except Exception as e:
        logger.error(f"API test failed: {e}")
        await callback.answer(f"API error: {str(e)}", show_alert=True)
        return

    logger.info(f"Server config validated for '{config['Server_name']}' by user {callback.from_user.id}")

    users = await get_all_users()
    admin_users = [u for u in users if getattr(u, "is_admin", False)]
    regular_users = [u for u in users if not getattr(u, "is_admin", False)]
    selected_users = []
    users_info = {u.id: (u.tg_name if getattr(u, "tg_name", None) else str(u.tg_id)) for u in regular_users}
    await state.update_data(
        config=config,
        selected_users=selected_users,
        admin_users=[u.id for u in admin_users],
        regular_users=[u.id for u in regular_users],
        users_info=users_info
    )
    await state.set_state(ServerRegisterState.select_users)

    if regular_users:
        text = (
            "<b>Select users who will have access to this server:</b>\n"
            "Click on a user to toggle access.\n"
            "Use <b>Accept All</b> to select everyone.\n\n"
            "ℹ️ <i>All administrators automatically have access to this server.</i>"
        )
        markup = server_register_select_users_keyboard([u.id for u in regular_users], selected_users, users_info)
    else:
        text = (
            "<b>No users available to grant access.</b>\n\n"
            "ℹ️ <i>All administrators automatically have access to this server.</i>"
        )
        markup = server_register_no_users_keyboard()

    try:
        await callback.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        logger.error(f"Edit message error: {e}")
        await callback.answer("Internal error: failed to show user selection.", show_alert=True)

@router.callback_query(F.data == "server_register_reset", StateFilter(ServerRegisterState.custom_config))
async def server_register_reset(callback: CallbackQuery, state: FSMContext):
    default_text = get_custom_config_text(SERVER_CONFIG_TEMPLATE)
    current_text = callback.message.text or callback.message.html_text
    if (current_text == default_text):
        await callback.answer("Already default template.", show_alert=True)
        return
    await state.update_data(
        custom_config=None,
        json_parse_error=False,
        raw_text=None,
        last_bot_text=default_text
    )
    try:
        await callback.message.edit_text(
            default_text,
            reply_markup=server_register_custom_keyboard(),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.error(f"Edit message error: {e}")

@router.callback_query(F.data == "server_register_cancel", StateFilter(ServerRegisterState.custom_config, ServerRegisterState.select_users))
async def server_register_cancel(callback: CallbackQuery, state: FSMContext, session):
    await state.clear()
    await open_server_manager(callback, session)

@router.callback_query(F.data.startswith("server_register_user_"), StateFilter(ServerRegisterState.select_users))
async def server_register_toggle_user(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("server_register_user_", ""))
    data = await state.get_data()
    selected = set(data.get("selected_users", []))
    if user_id in selected:
        selected.remove(user_id)
    else:
        selected.add(user_id)
    regular_users = data.get("regular_users", [])
    users_info = data.get("users_info", {})
    await state.update_data(selected_users=list(selected))
    try:
        markup = server_register_select_users_keyboard(regular_users, list(selected), users_info)
        await callback.message.edit_reply_markup(
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        logger.error(f"Edit reply markup error: {e}")

@router.callback_query(F.data == "server_register_accept_all", StateFilter(ServerRegisterState.select_users))
async def server_register_accept_all(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    regular_users = data.get("regular_users", [])
    users_info = data.get("users_info", {})
    selected_users = set(data.get("selected_users", []))
    if set(regular_users) == selected_users:
        new_selected = []
    else:
        new_selected = regular_users
    await state.update_data(selected_users=new_selected)
    try:
        markup = server_register_select_users_keyboard(regular_users, new_selected, users_info)
        await callback.message.edit_reply_markup(
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.error(f"Edit reply markup error: {e}")

@router.callback_query(F.data == "server_register_users_apply", StateFilter(ServerRegisterState.select_users))
async def server_register_users_apply(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    config = data.get("config")
    selected_users = set(data.get("selected_users", []))
    admin_users = set(data.get("admin_users", []))

    server = await create_server({
        "name": config["Server_name"],
        "description": config["Description"],
        "api_url": config["Api_url"],
        "status": "active"
    })
    admin_user = await get_user_by_tg_id(callback.from_user.id)
    await create_server_api_data({
        "server_id": server.id,
        "user_id": admin_user.id,
        "api_login": config["Api_login"],
        "api_password": config["Api_token"],
        "tg_id": callback.from_user.id,
        "password": config["Password"]
    })
    for user_id in selected_users | admin_users:
        await add_user_server_access(user_id, server.id)
    logger.info(f"Server '{server.name}' registered and access granted to users: {selected_users | admin_users}")

    await sync_all_users_on_servers(session)
    await state.clear()
    try:
        await callback.message.edit_text(
            f"✅ Server <b>{server.name}</b> successfully added and synchronized!\n\n"
            "Would you like to configure this server now?",
            reply_markup=server_register_post_add_keyboard(server.id),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        logger.error(f"Edit message error: {e}")

@router.callback_query(F.data.startswith("server_register_configure_yes_"))
async def server_register_configure_yes(callback: CallbackQuery, session):
    await show_settings_server_menu(callback, session)

@router.callback_query(F.data == "server_register_configure_no")
async def server_register_configure_no(callback: CallbackQuery, session):
    await open_server_manager(callback, session)