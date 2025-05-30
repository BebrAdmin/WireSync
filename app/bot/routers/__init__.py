from .main.handler import router as main_router
from .start.handler import router as start_router
from .server_manager import (
    server_manager_router,
    server_settings_router,
    adapter_create_router,
    adapter_delete_router,
    adapter_update_router,
)
from .server_manager.server_register import router as server_register_router
from .server_manager.delete_server import router as delete_server_router
from .peer_manager import (
    peer_manager_router,
    peer_config_router,
)
from .invite import (
    invite_manager_router,
    create_invite_router,
    delete_invite_router,
)
from .cleanup import cleanup_router

__all__ = [
    "main_router",
    "start_router",
    "server_manager_router",
    "server_settings_router",
    "adapter_create_router",
    "adapter_delete_router",
    "adapter_update_router",
    "server_register_router",
    "delete_server_router",  
    "peer_manager_router",
    "peer_config_router",
    "invite_manager_router",
    "create_invite_router",
    "delete_invite_router",
    "cleanup_router",
]