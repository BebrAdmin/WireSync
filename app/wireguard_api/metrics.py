import aiohttp
import logging
from app.wireguard_api.exceptions import WireGuardAPIError

logger = logging.getLogger("api.metrics")

async def get_interface_metrics(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, interface_id: str
) -> dict:
    """
    Get metrics for a specific WireGuard interface.
    """
    url = api_url.rstrip("/") + f"/metrics/by-interface/{interface_id}"
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

async def get_user_metrics(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, user_id: str
) -> dict:
    """
    Get metrics for a specific user.
    """
    url = api_url.rstrip("/") + f"/metrics/by-user/{user_id}"
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

async def get_peer_metrics(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, peer_id: str
) -> dict:
    """
    Get metrics for a specific peer.
    """
    url = api_url.rstrip("/") + f"/metrics/by-peer/{peer_id}"
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