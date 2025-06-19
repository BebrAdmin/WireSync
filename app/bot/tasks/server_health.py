import asyncio
import logging
from sqlalchemy import select
from datetime import datetime

from app.db import (
    get_all_servers,
    get_admin_api_data_for_server,
    AsyncSessionLocal,
    Server,
    User,
)
from app.wireguard_api.interfaces import get_all_interfaces

from app.config import load_config
config = load_config()

logger = logging.getLogger("server_health")

async def get_admin_user():
    """
    Get the first admin user from the database using SQLAlchemy ORM.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.is_admin == True).limit(1)
        )
        return result.scalar_one_or_none()

async def check_all_servers(aiohttp_session):
    """
    Check all servers from the DB via API using admin data.
    Updates server status and last_checked in the DB ('active' or 'error').
    aiohttp_session: aiohttp.ClientSession
    """
    servers = await get_all_servers()
    if not servers:
        logger.info("No servers to check.")
        return

    admin = await get_admin_user()
    if not admin:
        logger.error("No admin user found in the database!")
        return

    for server in servers:
        api_data = await get_admin_api_data_for_server(server.id)
        if not api_data:
            logger.warning(f"No admin API data for server {server.name} (id={server.id})")
            continue
        try:
            await get_all_interfaces(
                aiohttp_session,
                server.api_url,
                api_data.api_login,
                api_data.api_password
            )
            status = "active"
            logger.info(f"Server {server.name} [{server.api_url}] is active.")
        except Exception as e:
            status = "error"
            logger.error(f"Server {server.name} [{server.api_url}] is unavailable: {e}")

        async with AsyncSessionLocal() as db_session:
            db_server = await db_session.get(Server, server.id)
            if db_server:
                db_server.status = status
                db_server.last_checked = datetime.utcnow()
                await db_session.commit()
        
async def periodic_server_check(aiohttp_session, interval=None):
    """
    Periodically checks all servers with the specified interval (in seconds).
    """
    if interval is None:
        interval = config.SERVER_HEALTH_INTERVAL
    while True:
        await check_all_servers(aiohttp_session)
        await asyncio.sleep(interval)