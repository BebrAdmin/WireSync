from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.db import get_all_servers, get_user_by_tg_id
from .keyboard import server_manager_keyboard
from app.bot.routers.main.keyboard import main_menu_keyboard
from app.bot.tasks.server_health import check_all_servers
import zoneinfo
from aiogram.exceptions import TelegramBadRequest

from app.config import load_config
config = load_config()

router = Router()

def status_emoji(status: str) -> str:
    if status.lower() == "active":
        return "🟢 [Active]"
    return "🔴 [Error]"

def format_time(dt):
    if not dt:
        return "never"
    import zoneinfo
    local_tz = zoneinfo.ZoneInfo(config.TIMEZONE)
    if dt.tzinfo is None:
        from datetime import timezone
        dt = dt.replace(tzinfo=timezone.utc)
    dt_local = dt.astimezone(local_tz)
    return dt_local.strftime("%d.%m.%Y %H:%M:%S")

async def render_server_manager_message(callback: CallbackQuery):
    servers = await get_all_servers()
    if servers:
        servers_text = "\n".join(
            f"{status_emoji(server.status)} <b>{server.name}</b>\n"
            f"Last check: <i>{format_time(server.last_checked)}</i>"
            for server in servers
        )
        text = (
            "Server Management Menu:\n\n"
            f"{servers_text}"
        )
    else:
        text = "Server Management Menu:\n\n<b>No servers available yet.</b>"
    return text, server_manager_keyboard()

@router.callback_query(F.data == "server_manager")
async def open_server_manager(callback: CallbackQuery, session):
    await check_all_servers(session)
    text, markup = await render_server_manager_message(callback)
    try:
        if (
            callback.message.text == text
            and callback.message.reply_markup == markup
        ):
            return
        await callback.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

@router.callback_query(F.data == "sync_servers")
async def sync_servers(callback: CallbackQuery, session):
    await callback.answer("✅ Successfully synchronized!")
    await check_all_servers(session)
    await open_server_manager(callback, session)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user = await get_user_by_tg_id(callback.from_user.id)
    is_admin = bool(user and getattr(user, "is_admin", False))
    await callback.message.edit_text(
        "Main Menu",
        reply_markup=main_menu_keyboard(is_admin=is_admin)
    )