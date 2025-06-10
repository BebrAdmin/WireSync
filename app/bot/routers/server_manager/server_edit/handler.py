import json
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.bot.filters.is_admin import IsAdmin
from .fsm import ServerEditState
from .keyboard import server_edit_custom_keyboard, edit_server_select_keyboard
from app.db import get_all_servers, get_server_by_id
from app.db.crud import update_server
from app.bot.routers.server_manager.handler import open_server_manager
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger("server_edit")

router = Router()

EDITABLE_FIELDS = ["name", "description"]

def get_edit_config(server):
    return {
        "Server_name": server.name,
        "Description": server.description or ""
    }

def get_edit_config_text(config, error_text=None, raw_text=None):
    error_block = ""
    if error_text:
        error_block = f"<blockquote>⚠️ <b>Error:</b> <i>{error_text}</i></blockquote>\n\n"
    config_block = (
        f"<pre>{raw_text}</pre>" if raw_text is not None
        else f"<pre>{json.dumps(config, indent=2, ensure_ascii=False)}</pre>"
    )
    return (
        f"{error_block}"
        "<b>Server edit template:</b>\n"
        f"{config_block}\n\n"
        "ℹ️ <i>Paste your updated configuration above and use the buttons below.</i>"
    )

def validate_edit_config(data):
    if not isinstance(data, dict):
        return False, "The configuration must be a valid JSON object."
    if "Server_name" not in data or not data["Server_name"]:
        return False, "Server_name must be a non-empty string."
    if "Description" not in data:
        return False, "Description is required (can be empty)."
    if not isinstance(data["Server_name"], str):
        return False, "Server_name must be a string."
    if not isinstance(data["Description"], str):
        return False, "Description must be a string."
    return True, None

@router.callback_query(IsAdmin(), F.data == "edit_server_menu")
async def show_edit_server_menu(callback: CallbackQuery):
    servers = await get_all_servers()
    if not servers:
        await callback.answer("No servers available to edit.", show_alert=True)
        return
    await callback.message.edit_text(
        "<b>Select a server to edit:</b>",
        reply_markup=edit_server_select_keyboard(servers),
        parse_mode="HTML"
    )

@router.callback_query(IsAdmin(), F.data.regexp(r"^server_edit_\d+$"))
async def start_server_edit(callback: CallbackQuery, state: FSMContext):
    server_id = int(callback.data.split("_")[-1])
    server = await get_server_by_id(server_id)
    if not server:
        await callback.answer("Server not found.", show_alert=True)
        return
    config = get_edit_config(server)
    msg = await callback.message.edit_text(
        get_edit_config_text(config),
        reply_markup=server_edit_custom_keyboard(server_id),
        parse_mode="HTML"
    )
    await state.set_state(ServerEditState.custom_config)
    await state.update_data(
        server_id=server_id,
        bot_message_id=msg.message_id,
        custom_config=config,
        original_config=config.copy(),
        json_parse_error=False,
        raw_text=None,
        last_bot_text=msg.text
    )

@router.message(IsAdmin(), StateFilter(ServerEditState.custom_config))
async def server_edit_custom_config(message: Message, state: FSMContext):
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
        new_text = get_edit_config_text(
            data.get("custom_config", {}),
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
                reply_markup=server_edit_custom_keyboard(data["server_id"]),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                logger.error(f"Edit message error: {e}")
        await state.update_data(custom_config=None, json_parse_error=True, raw_text=user_text, last_bot_text=new_text)
        return

    ok, err = validate_edit_config(user_json)
    if not ok:
        new_text = get_edit_config_text(
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
                reply_markup=server_edit_custom_keyboard(data["server_id"]),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                logger.error(f"Edit message error: {e}")
        await state.update_data(custom_config=None, json_parse_error=False, raw_text=None, last_bot_text=new_text)
        return

    new_text = get_edit_config_text(user_json)
    last_text = data.get("last_bot_text")
    if new_text == last_text:
        return
    try:
        await message.bot.edit_message_text(
            new_text,
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=server_edit_custom_keyboard(data["server_id"]),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.error(f"Edit message error: {e}")
    await state.update_data(custom_config=user_json, json_parse_error=False, raw_text=None, last_bot_text=new_text)

@router.callback_query(IsAdmin(), F.data.regexp(r"^server_edit_apply_\d+$"), StateFilter(ServerEditState.custom_config))
async def server_edit_apply(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    config = data.get("custom_config")
    original_config = data.get("original_config")
    json_parse_error = data.get("json_parse_error", False)
    server_id = data.get("server_id")
    if json_parse_error or not config:
        await callback.answer("Please paste a valid configuration first.", show_alert=True)
        return

    if config == original_config:
        await callback.answer("No changes detected in configuration.", show_alert=True)
        return

    server = await update_server(server_id, config["Server_name"], config["Description"])
    if not server:
        await callback.answer("Server not found.", show_alert=True)
        return

    logger.info(f"Server '{server.name}' (ID: {server.id}) updated by user {callback.from_user.id}")

    await state.clear()
    await callback.answer("✅ Server updated successfully!")
    await open_server_manager(callback, session)

@router.callback_query(IsAdmin(), F.data == "server_edit_reset", StateFilter(ServerEditState.custom_config))
async def server_edit_reset(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    original_config = data.get("original_config")
    default_text = get_edit_config_text(original_config)
    current_text = callback.message.text or callback.message.html_text
    if current_text == default_text:
        await callback.answer("Already default template.", show_alert=True)
        return
    await state.update_data(
        custom_config=original_config,
        json_parse_error=False,
        raw_text=None,
        last_bot_text=default_text
    )
    try:
        await callback.message.edit_text(
            default_text,
            reply_markup=server_edit_custom_keyboard(data["server_id"]),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.error(f"Edit message error: {e}")
    await callback.answer("Reset to default.")

@router.callback_query(IsAdmin(), F.data == "server_edit_cancel", StateFilter(ServerEditState.custom_config))
async def server_edit_cancel(callback: CallbackQuery, state: FSMContext, session):
    await state.clear()
    await open_server_manager(callback, session)