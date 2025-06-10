import aiohttp
import logging
from app.wireguard_api.exceptions import WireGuardAPIError

logger = logging.getLogger("api.provisioning")

async def get_peer_config(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, peer_id: str
) -> str:
    """
    Get peer config in wg-quick format (text/plain).
    """
    if not peer_id:
        raise ValueError("peer_id cannot be empty")
    url = api_url.rstrip("/") + "/provisioning/data/peer-config"
    params = {"PeerId": peer_id}
    logger.info(f"GET {url} (user={api_user}) params={params}")
    try:
        async with session.get(
            url,
            params=params,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={"accept": "text/plain"},
        ) as resp:
            if resp.status == 200:
                text = await resp.text()
                logger.info(f"Success: {url}")
                return text
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during GET {url}: {e}")
        raise

async def get_peer_qr(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, peer_id: str
) -> bytes:
    """
    Get peer configuration QR code (image/png).
    """
    if not peer_id:
        raise ValueError("peer_id cannot be empty")
    url = api_url.rstrip("/") + "/provisioning/data/peer-qr"
    params = {"PeerId": peer_id}
    logger.info(f"GET {url} (user={api_user}) params={params}")
    try:
        async with session.get(
            url,
            params=params,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={"accept": "image/png"},
        ) as resp:
            if resp.status == 200:
                data = await resp.read()
                logger.info(f"Success: {url}")
                return data
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during GET {url}: {e}")
        raise

async def get_user_peer_info(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, user_id: str
) -> dict:
    """
    Get information about user's peer records by user identifier.
    """
    if not user_id:
        raise ValueError("user_id cannot be empty")
    url = api_url.rstrip("/") + "/provisioning/data/user-info"
    params = {"UserId": user_id}
    logger.info(f"GET {url} (user={api_user}) params={params}")
    try:
        async with session.get(
            url,
            params=params,
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

async def create_peer(
    session: aiohttp.ClientSession,
    api_url: str, api_user: str, api_pass: str, interface_id: str, user_id: str
) -> dict:
    """
    Create a new peer for the specified interface and user.
    """
    if not interface_id:
        raise ValueError("interface_id cannot be empty")
    if not user_id:
        raise ValueError("user_id cannot be empty")
    url = api_url.rstrip("/") + "/provisioning/new-peer"
    data = {
        "InterfaceIdentifier": interface_id,
        "UserIdentifier": user_id
    }
    logger.info(f"POST {url} (user={api_user}) data={data}")
    try:
        async with session.post(
            url,
            json=data,
            auth=aiohttp.BasicAuth(api_user, api_pass),
            timeout=10,
            headers={
                "accept": "application/json",
                "content-type": "application/json"
            },
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                logger.info(f"Created peer at {url}")
                return result
            else:
                text = await resp.text()
                logger.error(f"API error {resp.status} for {url}: {text}")
                raise WireGuardAPIError(f"API error {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Exception during POST {url}: {e}")
        raise