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
    adapter_create_router,       
    server_register_router,
    delete_server_router, 
    peer_manager_router,          
    cleanup_router, 
)

from app.bot.middleware.session import SessionMiddleware
from app.bot.middleware.message_cleaner import MessageCleanerMiddleware
from app.bot import utils
from app.db.init_db import init_db
from app.bot.tasks.server_health import periodic_server_check

config = load_config()
setup_logging(config.LOGGING)  

# logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger("startup")

bot = Bot(token=config.TOKEN)
dp = Dispatcher()
session: aiohttp.ClientSession = None

async def main():
    global session
    session = aiohttp.ClientSession()
    await init_db()
    await bot.set_my_commands(utils.get_bot_commands())

    asyncio.create_task(periodic_server_check(session, interval=60))

    dp.message.middleware(SessionMiddleware(session))
    dp.callback_query.middleware(SessionMiddleware(session))
    dp.message.middleware(MessageCleanerMiddleware())

    for router in [
        main_router,
        start_router,
        server_manager_router,
        server_settings_router,   
        adapter_create_router,    
        server_register_router,
        delete_server_router,
        peer_manager_router,      
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
        logger.info("Shutdown requested via KeyboardInterrupt (Ctrl+C).")