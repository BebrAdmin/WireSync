from .main.handler import router as main_router
from .start.handler import router as start_router
from .server_manager import (
    server_manager_router,
    server_register_router,
    server_delete_router,
    server_edit_router,
    server_settings_router,
    adapter_create_router,
    adapter_delete_router,
    adapter_update_router,
)
from .peer_manager import (
    peer_manager_router,
    peer_config_router,
    peer_create_router,
    peer_delete_router,
)
from .invite_manager import (
    invite_manager_router,
    invite_create_router,
    invite_delete_router,
)
from .user_manager import (
    user_manager_router,
    user_edit_access_router,
    user_delete_router,
)
from .logs_manager.handler import router as logs_manager_router
from .cleanup import cleanup_router

__all__ = [
    "main_router",
    "start_router",
    "server_manager_router",
    "server_settings_router",
    "server_register_router",
    "server_delete_router",
    "server_edit_router",
    "adapter_create_router",
    "adapter_delete_router",
    "adapter_update_router",
    "peer_manager_router",
    "peer_config_router",
    "peer_create_router",
    "peer_delete_router",
    "invite_manager_router",
    "invite_create_router",
    "invite_delete_router",
    "user_manager_router",
    "user_edit_access_router",
    "user_delete_router",
    "logs_manager_router",
    "cleanup_router",
]