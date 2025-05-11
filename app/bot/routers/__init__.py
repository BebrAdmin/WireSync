from .main.handler import router as main_router
from .start.handler import router as start_router
from .server_manager import (
    server_manager_router,
    server_settings_router,
    adapter_create_router,
)
from .server_manager.server_register import router as server_register_router
from .server_manager.delete_server import router as delete_server_router
from .peer_manager import router as peer_manager_router
from .cleanup import cleanup_router

__all__ = [
    "main_router",
    "start_router",
    "server_manager_router",
    "server_settings_router",
    "adapter_create_router",
    "server_register_router",
    "delete_server_router",  
    "peer_manager_router",
    "cleanup_router",
]