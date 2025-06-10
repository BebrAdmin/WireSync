import aiohttp
import logging
from app.wireguard_api.exceptions import WireGuardAPIError

logger = logging.getLogger("api.interfaces")

async def get_all_interfaces(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str
) -> list:
    """
    Get a list of all WireGuard interfaces.
    """
    url = api_url.rstrip("/") + "/interface/all"
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
                logger.info(f"Success: {url} [{len(data)} interfaces]")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during GET {url}: {e}")  # Только строка ошибки, без traceback
        raise

async def get_interface_by_id(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, interface_id: str
) -> dict:
    """
    Get information about a specific WireGuard interface by its identifier.
    """
    url = api_url.rstrip("/") + f"/interface/by-id/{interface_id}"
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

async def update_interface_by_id(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, interface_id: str, interface_data: dict
) -> dict:
    """
    Update a WireGuard interface by its identifier.
    """
    url = api_url.rstrip("/") + f"/interface/by-id/{interface_id}"
    logger.info(f"PUT {url} (user={api_user})")
    try:
        async with session.put(
            url,
            json=interface_data,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={
                "accept": "application/json",
                "content-type": "application/json"
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"Updated interface {interface_id} at {url}")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during PUT {url}: {e}")
        raise


async def delete_interface_by_id(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, interface_id: str
) -> None:
    """
    Delete a WireGuard interface by its identifier.
    """
    url = api_url.rstrip("/") + f"/interface/by-id/{interface_id}"
    logger.info(f"DELETE {url} (user={api_user})")
    try:
        async with session.delete(
            url,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={"accept": "application/json"},
        ) as resp:
            if resp.status == 204:
                logger.info(f"Deleted interface {interface_id} at {url}")
                return
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during DELETE {url}: {e}")
        raise

async def create_interface(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, interface_data: dict
) -> dict:
    """
    Create a new WireGuard interface.
    """
    url = api_url.rstrip("/") + "/interface/new"
    logger.info(f"POST {url} (user={api_user})")
    try:
        async with session.post(
            url,
            json=interface_data,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={
                "accept": "application/json",
                "content-type": "application/json"
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"Created interface at {url}")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during POST {url}: {e}")
        raise
        
async def prepare_interface(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str
) -> dict:
    """
    Prepare a new WireGuard interface record.
    """
    url = api_url.rstrip("/") + "/interface/prepare"
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
                logger.info(f"Prepared interface at {url}")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during GET {url}: {e}")
        raise