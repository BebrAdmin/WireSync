from .handler import router as peer_manager_router
from .peer_config.handler import router as peer_config_router
from .peer_create.handler import router as peer_create_router
from .peer_delete.handler import router as peer_delete_router

__all__ = [
    "peer_manager_router",
    "peer_config_router",
    "peer_create_router",
    "peer_delete_router",
]