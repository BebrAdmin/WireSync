import aiohttp
import logging
from app.wireguard_api.exceptions import WireGuardAPIError

logger = logging.getLogger("api.users")

async def get_all_users(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str
) -> list:
    """
    Get a list of all users.
    """
    url = api_url.rstrip("/") + "/user/all"
    logger.info(f"GET {url} (user={api_user})")
    try:
        async with session.get(
            url,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={"accept": "application/json"},
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"Success: {url} [{len(data)} users]")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during GET {url}: {e}")
        raise

async def get_user_by_id(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, user_id: str
) -> dict:
    """
    Get user information by user identifier.
    """
    url = api_url.rstrip("/") + f"/user/by-id/{user_id}"
    logger.info(f"GET {url} (user={api_user})")
    try:
        async with session.get(
            url,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={"accept": "application/json"},
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"Success: {url}")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during GET {url}: {e}")
        raise

async def update_user_by_id(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, user_id: str, user_data: dict
) -> dict:
    """
    Update user information by user identifier.
    """
    url = api_url.rstrip("/") + f"/user/by-id/{user_id}"
    logger.info(f"PUT {url} (user={api_user})")
    try:
        async with session.put(
            url,
            json=user_data,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={
                "accept": "application/json",
                "content-type": "application/json"
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"Updated user at {url}")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during PUT {url}: {e}")
        raise

async def delete_user_by_id(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, user_id: str
) -> None:
    """
    Delete a user by user identifier.
    """
    url = api_url.rstrip("/") + f"/user/by-id/{user_id}"
    logger.info(f"DELETE {url} (user={api_user})")
    try:
        async with session.delete(
            url,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={"accept": "application/json"},
        ) as resp:
            if resp.status == 204:
                logger.info(f"Deleted user {user_id} at {url}")
                return
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during DELETE {url}: {e}")
        raise

async def create_user(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, user_data: dict
) -> dict:
    """
    Create a new user.
    """
    url = api_url.rstrip("/") + "/user/new"
    logger.info(f"POST {url} (user={api_user})")
    try:
        async with session.post(
            url,
            json=user_data,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={
                "accept": "application/json",
                "content-type": "application/json"
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"Created user at {url}")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during POST {url}: {e}")
        raise