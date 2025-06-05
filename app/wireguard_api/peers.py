import aiohttp
import logging
import urllib.parse
from app.wireguard_api.exceptions import WireGuardAPIError

logger = logging.getLogger("api.peers")

async def get_peer_by_id(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, peer_id: str
) -> dict:
    """
    Get a specific peer record by its identifier (public key).
    """
    if not peer_id:
        raise ValueError("peer_id cannot be empty")
    encoded_peer_id = urllib.parse.quote(peer_id, safe='')
    url = api_url.rstrip("/") + f"/peer/by-id/{encoded_peer_id}"
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

async def delete_peer_by_id(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, peer_id: str
) -> None:
    """
    Delete a specific peer record by its identifier (public key).
    """
    if not peer_id:
        raise ValueError("peer_id cannot be empty")
    encoded_peer_id = urllib.parse.quote(peer_id, safe='')
    url = api_url.rstrip("/") + f"/peer/by-id/{encoded_peer_id}"
    logger.info(f"DELETE {url} (user={api_user})")
    try:
        async with session.delete(
            url,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={"accept": "application/json"},
        ) as resp:
            if resp.status == 204:
                logger.info(f"Peer deleted successfully: {url}")
                return
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during DELETE {url}: {e}")
        raise