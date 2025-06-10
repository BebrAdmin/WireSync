import asyncio
import logging
from app.db import (
    get_all_servers,
    get_users_for_server,
    get_user_by_id as get_db_user_by_id,
    get_server_api_data_by_server_id_and_user_id,
    get_admin_api_data_for_server,
    get_invite_by_used_by,
    create_server_api_data,
    get_server_api_data_by_server_id_and_tg_id,
)
from app.wireguard_api.users import (
    get_user_by_id as wg_get_user_by_id,
    get_all_users as wg_get_all_users,
    create_user as wg_create_user,
    update_user_by_id,
    delete_user_by_id,
)
from app.bot.utils import generate_password

from app.config import load_config
config = load_config()

logger = logging.getLogger("user_sync")

async def sync_all_users_on_servers(aiohttp_session):
    servers = await get_all_servers()
    for server in servers:
        if getattr(server, "status", None) != "active":
            continue

        allowed_user_ids = await get_users_for_server(server.id)
        user_map = {}
        for user_id in allowed_user_ids:
            db_user = await get_db_user_by_id(user_id)
            if db_user:
                user_map[user_id] = db_user

        admin_api_data = await get_admin_api_data_for_server(server.id)
        if not admin_api_data:
            logger.warning(f"No admin API data for server {server.id}")
            continue

        try:
            wg_users = await wg_get_all_users(
                aiohttp_session,
                server.api_url,
                admin_api_data.api_login,
                admin_api_data.api_password
            )
        except Exception as e:
            logger.error(f"Failed to get users from WG server {server.id}: {e}")
            continue

        wg_api_logins = set(str(u.get("Identifier")) for u in wg_users if u.get("Identifier"))

        for api_login in wg_api_logins:
            found = False
            for user_id in allowed_user_ids:
                api_data = await get_server_api_data_by_server_id_and_user_id(server.id, user_id)
                if api_data and api_data.api_login == api_login:
                    found = True
                    break
            if not found and api_login != admin_api_data.api_login:
                try:
                    await delete_user_by_id(
                        aiohttp_session,
                        server.api_url,
                        admin_api_data.api_login,
                        admin_api_data.api_password,
                        api_login
                    )
                    logger.info(f"Deleted WG user {api_login} from server {server.id} (not in user_server_access)")
                except Exception as e:
                    logger.error(f"Failed to delete WG user {api_login} from server {server.id}: {e}")

        for user_id in allowed_user_ids:
            db_user = user_map.get(user_id)
            if not db_user:
                continue

            api_data = await get_server_api_data_by_server_id_and_user_id(server.id, db_user.id)
            if not api_data:
                invite = await get_invite_by_used_by(db_user.id)
                admin_api_data_for_create = None
                if invite:
                    admin_api_data_for_create = await get_server_api_data_by_server_id_and_tg_id(server.id, invite.admin_tg_id)
                if not admin_api_data_for_create:
                    admin_api_data_for_create = await get_admin_api_data_for_server(server.id)
                if not admin_api_data_for_create:
                    logger.warning(f"No admin API data for server {server.id} (for user {db_user.tg_id})")
                    continue

                api_login = str(db_user.tg_id)
                api_password = generate_password()
                password = getattr(db_user, "password", generate_password())
                payload = {
                    "ApiToken": api_password,
                    "Department": db_user.department,
                    "Disabled": False,
                    "DisabledReason": "",
                    "Email": db_user.email,
                    "Firstname": db_user.tg_name,
                    "Identifier": api_login,
                    "IsAdmin": db_user.is_admin,
                    "Lastname": "",
                    "Locked": False,
                    "LockedReason": "",
                    "Notes": "",
                    "Password": password,
                    "Phone": db_user.phone,
                    "Source": "db"
                }
                try:
                    await wg_create_user(
                        session=aiohttp_session,
                        api_url=server.api_url,
                        api_user=admin_api_data_for_create.api_login,
                        api_pass=admin_api_data_for_create.api_password,
                        user_data=payload
                    )
                    await create_server_api_data({
                        "server_id": server.id,
                        "user_id": db_user.id,
                        "tg_id": db_user.tg_id,
                        "api_login": api_login,
                        "api_password": api_password,
                        "password": password
                    })
                    logger.info(f"Created WG user and server_api_data for {db_user.tg_id} on server {server.id}")
                except Exception as e:
                    logger.error(f"Failed to create WG user {db_user.tg_id} on server {server.id}: {e}")
                continue

            invite = await get_invite_by_used_by(db_user.id)
            admin_api_data_for_create = None
            if invite:
                admin_api_data_for_create = await get_server_api_data_by_server_id_and_tg_id(server.id, invite.admin_tg_id)
            if not admin_api_data_for_create:
                admin_api_data_for_create = await get_admin_api_data_for_server(server.id)
            if not admin_api_data_for_create:
                logger.warning(f"No admin API data for server {server.id} (for user {db_user.tg_id})")
                continue

            try:
                wg_user = await wg_get_user_by_id(
                    aiohttp_session,
                    server.api_url,
                    admin_api_data_for_create.api_login,
                    admin_api_data_for_create.api_password,
                    api_data.api_login
                )
                need_update = (
                    wg_user.get("Email") != db_user.email or
                    wg_user.get("Department") != db_user.department
                )
                if need_update:
                    payload = {
                        "ApiToken": api_data.api_password,
                        "Department": db_user.department,
                        "Disabled": False,
                        "DisabledReason": "",
                        "Email": db_user.email,
                        "Firstname": db_user.tg_name,
                        "Identifier": api_data.api_login,
                        "IsAdmin": db_user.is_admin,
                        "Lastname": "",
                        "Locked": False,
                        "LockedReason": "",
                        "Notes": "",
                        "Password": api_data.password,
                        "Phone": db_user.phone,
                        "Source": "db"
                    }
                    await update_user_by_id(
                        session=aiohttp_session,
                        api_url=server.api_url,
                        api_user=admin_api_data_for_create.api_login,
                        api_pass=admin_api_data_for_create.api_password,
                        user_id=api_data.api_login,
                        user_data=payload
                    )
                    logger.info(f"Updated WG user {api_data.api_login} on server {server.id}")
            except Exception as e:
                logger.warning(f"User {api_data.api_login} not found on WG server {server.id}: {e}")
                payload = {
                    "ApiToken": api_data.api_password,
                    "Department": db_user.department,
                    "Disabled": False,
                    "DisabledReason": "",
                    "Email": db_user.email,
                    "Firstname": db_user.tg_name,
                    "Identifier": api_data.api_login,
                    "IsAdmin": db_user.is_admin,
                    "Lastname": "",
                    "Locked": False,
                    "LockedReason": "",
                    "Notes": "",
                    "Password": api_data.password,
                    "Phone": db_user.phone,
                    "Source": "db"
                }
                try:
                    await wg_create_user(
                        session=aiohttp_session,
                        api_url=server.api_url,
                        api_user=admin_api_data_for_create.api_login,
                        api_pass=admin_api_data_for_create.api_password,
                        user_data=payload
                    )
                    logger.info(f"Created WG user {api_data.api_login} on server {server.id}")
                except Exception as e2:
                    logger.error(f"Failed to create WG user {api_data.api_login} on server {server.id}: {e2}")

        logger.info(f"user_sync: server {server.id} ({getattr(server, 'name', '')}) sync completed successfully")
    logger.info("user_sync: all servers sync completed successfully")

async def periodic_user_sync(aiohttp_session, interval=None):
    if interval is None:
        interval = config.USER_SYNC_INTERVAL
    while True:
        await sync_all_users_on_servers(aiohttp_session)
        await asyncio.sleep(interval)