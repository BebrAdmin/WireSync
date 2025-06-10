import asyncio
import aiohttp
import logging

from aiogram import Bot, Dispatcher
from app.config import load_config
from app.logger import setup_logging  

from app.bot.routers import (
    main_router,
    start_router,
    server_manager_router,
    server_settings_router,
    server_register_router,
    server_delete_router,
    server_edit_router,
    adapter_create_router,
    adapter_delete_router,
    adapter_update_router,       
    peer_manager_router,
    peer_config_router,
    peer_create_router,
    peer_delete_router, 
    invite_manager_router,
    invite_create_router,
    invite_delete_router,
    user_manager_router,
    user_edit_access_router,
    user_delete_router,
    logs_manager_router,
    cleanup_router, 
)

from app.bot.middleware.session import SessionMiddleware
from app.bot.middleware.message_cleaner import MessageCleanerMiddleware
from app.bot import utils
from app.db.init_db import init_db
from app.bot.tasks.server_health import periodic_server_check
from app.bot.tasks.user_sync import periodic_user_sync

config = load_config()
# logging.basicConfig(level=logging.INFO)  
setup_logging(config.LOGGING)  

logger = logging.getLogger("startup")

bot = Bot(token=config.TOKEN)
dp = Dispatcher()
session: aiohttp.ClientSession = None

async def main():
    global session
    session = aiohttp.ClientSession()
    await init_db()
    await bot.set_my_commands(utils.get_bot_commands())

    asyncio.create_task(periodic_server_check(session))
    asyncio.create_task(periodic_user_sync(session))

    dp.message.middleware(SessionMiddleware(session))
    dp.callback_query.middleware(SessionMiddleware(session))
    dp.message.middleware(MessageCleanerMiddleware())

    for router in [
        main_router,
        start_router,
        server_manager_router,
        server_settings_router,
        server_register_router,
        server_delete_router,
        server_edit_router, 
        adapter_create_router,
        adapter_delete_router,
        adapter_update_router,  
        peer_manager_router,
        peer_config_router,
        peer_create_router,
        peer_delete_router, 
        invite_manager_router,
        invite_create_router,
        invite_delete_router,
        user_manager_router,
        user_edit_access_router,
        user_delete_router,
        logs_manager_router,
        cleanup_router,
    ]:
        dp.include_router(router)

    try:
        logger.info("Bot has started successfully and is now polling for updates.")
        await dp.start_polling(bot)
    finally:
        await session.close()
        logger.info("Bot has been shut down gracefully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")