import os
import asyncio
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from app.bot.routers.logs_manager.fsm import LogsManagerState
from .keyboard import logs_menu_keyboard, close_file_keyboard
from app.bot.filters.is_admin import IsAdmin

LOG_PATH = "app/logs/app.log"
LOGS_PER_PAGE = 15
LOG_LEVELS = ["INFO", "WARNING", "ERROR", "ALL"]
LIVE_UPDATE_INTERVAL = 3

router = Router()

def read_log_lines(level="INFO", page=1):
    if not os.path.exists(LOG_PATH):
        return [], 1
    with open(LOG_PATH, encoding="utf-8") as f:
        if level == "ALL":
            lines = f.readlines()
        else:
            lines = [line for line in f if f"[{level}]" in line]
    lines = lines[::-1]
    total_pages = max(1, (len(lines) + LOGS_PER_PAGE - 1) // LOGS_PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * LOGS_PER_PAGE
    end = start + LOGS_PER_PAGE
    return lines[start:end], total_pages

def format_logs_message(lines, level, mode, page, total_pages):
    emoji = {"INFO": "🟢", "WARNING": "🟡", "ERROR": "🔴", "ALL": "📋"}.get(level, "📋")
    header = "<b>Logs Manager:</b>"
    if not lines:
        logs_block = "<pre>No logs found for this level.</pre>"
    else:
        logs_block = "<pre>" + "".join(f"> {line}" for line in reversed(lines))[-4000:] + "</pre>"
    footer = (
        f"<b>Level:</b> {emoji} {level}  │  "
        f"<b>Mode:</b> {mode}  │  "
        f"<b>Page:</b> {page}/{total_pages}"
    )
    return f"{header}\n{logs_block}\n{footer}"

async def live_update_logs(message, state: FSMContext):
    while True:
        data = await state.get_data()
        mode = data.get("mode", "Freeze")
        page = data.get("page", 1)
        level = data.get("level", "INFO")
        if mode != "Live":
            break
        for handler in logging.getLogger().handlers:
            try:
                handler.flush()
            except Exception:
                pass
        _, total_pages = read_log_lines(level=level, page=1)
        if page > total_pages:
            page = total_pages
            await state.update_data(page=page)
        lines, total_pages = read_log_lines(level=level, page=page)
        msg = format_logs_message(lines, level, mode, page, total_pages)
        try:
            await message.edit_text(
                msg,
                reply_markup=logs_menu_keyboard(level=level, mode=mode, page=page, total_pages=total_pages),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                break
        except Exception:
            break
        await asyncio.sleep(LIVE_UPDATE_INTERVAL)

async def cancel_live_task(state: FSMContext):
    data = await state.get_data()
    task = data.get("live_task")
    if task and not task.done():
        task.cancel()
    await state.update_data(live_task=None)

@router.callback_query(IsAdmin(), F.data == "logs_manager_menu")
async def show_logs_manager_menu(callback: CallbackQuery, state: FSMContext):
    for handler in logging.getLogger().handlers:
        try:
            handler.flush()
        except Exception:
            pass
    await cancel_live_task(state)
    await state.set_state(LogsManagerState.view)
    await state.update_data(level="INFO", mode="Live", page=1)
    lines, total_pages = read_log_lines(level="INFO", page=1)
    msg = format_logs_message(lines, "INFO", "Live", 1, total_pages)
    try:
        await callback.message.edit_text(
            msg,
            reply_markup=logs_menu_keyboard(level="INFO", mode="Live", page=1, total_pages=total_pages),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass
    task = asyncio.create_task(live_update_logs(callback.message, state))
    await state.update_data(live_task=task)

@router.callback_query(IsAdmin(), F.data == "logs_level_switch")
async def switch_log_level(callback: CallbackQuery, state: FSMContext):
    await cancel_live_task(state)
    data = await state.get_data()
    mode = data.get("mode", "Live")
    page = 1
    current_level = data.get("level", "INFO")
    idx = LOG_LEVELS.index(current_level)
    next_level = LOG_LEVELS[(idx + 1) % len(LOG_LEVELS)]
    await state.update_data(level=next_level, page=page)
    lines, total_pages = read_log_lines(level=next_level, page=page)
    msg = format_logs_message(lines, next_level, mode, page, total_pages)
    try:
        await callback.message.edit_text(
            msg,
            reply_markup=logs_menu_keyboard(level=next_level, mode=mode, page=page, total_pages=total_pages),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass
    if mode == "Live":
        task = asyncio.create_task(live_update_logs(callback.message, state))
        await state.update_data(live_task=task)

@router.callback_query(IsAdmin(), F.data == "logs_mode_toggle")
async def toggle_logs_mode(callback: CallbackQuery, state: FSMContext):
    await cancel_live_task(state)
    data = await state.get_data()
    level = data.get("level", "INFO")
    mode = data.get("mode", "Live")
    page = data.get("page", 1)
    new_mode = "Live" if mode == "Freeze" else "Freeze"
    await state.update_data(mode=new_mode)
    lines, total_pages = read_log_lines(level=level, page=page)
    msg = format_logs_message(lines, level, new_mode, page, total_pages)
    try:
        await callback.message.edit_text(
            msg,
            reply_markup=logs_menu_keyboard(level=level, mode=new_mode, page=page, total_pages=total_pages),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass
    if new_mode == "Live":
        task = asyncio.create_task(live_update_logs(callback.message, state))
        await state.update_data(live_task=task)

@router.callback_query(IsAdmin(), F.data == "logs_next")
async def logs_next_page(callback: CallbackQuery, state: FSMContext):
    await cancel_live_task(state)
    data = await state.get_data()
    level = data.get("level", "INFO")
    mode = data.get("mode", "Live")
    page = data.get("page", 1)
    if page <= 1:
        await callback.answer("You are already at the latest logs.", show_alert=True)
        return
    page = page - 1
    await state.update_data(page=page)
    lines, total_pages = read_log_lines(level=level, page=page)
    msg = format_logs_message(lines, level, mode, page, total_pages)
    try:
        await callback.message.edit_text(
            msg,
            reply_markup=logs_menu_keyboard(level=level, mode=mode, page=page, total_pages=total_pages),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass
    if mode == "Live":
        task = asyncio.create_task(live_update_logs(callback.message, state))
        await state.update_data(live_task=task)

@router.callback_query(IsAdmin(), F.data == "logs_prev")
async def logs_prev_page(callback: CallbackQuery, state: FSMContext):
    await cancel_live_task(state)
    data = await state.get_data()
    level = data.get("level", "INFO")
    mode = data.get("mode", "Live")
    page = data.get("page", 1)
    lines, total_pages = read_log_lines(level=level, page=page)
    if page >= total_pages:
        await callback.answer("You are already at the oldest logs.", show_alert=True)
        return
    page = page + 1
    await state.update_data(page=page)
    lines, total_pages = read_log_lines(level=level, page=page)
    msg = format_logs_message(lines, level, mode, page, total_pages)
    try:
        await callback.message.edit_text(
            msg,
            reply_markup=logs_menu_keyboard(level=level, mode=mode, page=page, total_pages=total_pages),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass
    if mode == "Live":
        task = asyncio.create_task(live_update_logs(callback.message, state))
        await state.update_data(live_task=task)

@router.callback_query(IsAdmin(), F.data == "logs_refresh")
async def logs_refresh(callback: CallbackQuery, state: FSMContext):
    for handler in logging.getLogger().handlers:
        try:
            handler.flush()
        except Exception:
            pass
    data = await state.get_data()
    mode = data.get("mode", "Freeze")
    if mode == "Live":
        await callback.answer("Live mode: logs update automatically.", show_alert=True)
        return
    level = data.get("level", "INFO")
    page = data.get("page", 1)
    lines, total_pages = read_log_lines(level=level, page=page)
    msg = format_logs_message(lines, level, mode, page, total_pages)
    try:
        await callback.message.edit_text(
            msg,
            reply_markup=logs_menu_keyboard(level=level, mode=mode, page=page, total_pages=total_pages),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass

@router.callback_query(IsAdmin(), F.data == "logs_download")
async def logs_download(callback: CallbackQuery, state: FSMContext):
    await cancel_live_task(state)
    if not os.path.exists(LOG_PATH):
        await callback.answer("Log file not found.", show_alert=True)
        return
    now = datetime.now().strftime("%d_%m_%Y")
    filename = f"{now}.log"
    with open(LOG_PATH, "rb") as f:
        await callback.message.answer_document(
            BufferedInputFile(f.read(), filename=filename),
            reply_markup=close_file_keyboard(callback.from_user.id)
        )
    await callback.answer()

@router.callback_query(F.data.startswith("close_file_"))
async def close_file_message(callback: CallbackQuery):
    if str(callback.from_user.id) in callback.data:
        await callback.message.delete()
    else:
        await callback.answer("You can't close this file.", show_alert=True)

@router.callback_query(IsAdmin(), F.data == "logs_back")
async def logs_back(callback: CallbackQuery, state: FSMContext):
    await cancel_live_task(state)
    from app.bot.routers.main.handler import main_menu_callback
    await main_menu_callback(callback)