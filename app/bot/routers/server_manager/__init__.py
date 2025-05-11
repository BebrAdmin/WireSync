from .handler import router as server_manager_router
from .delete_server.handler import router as delete_server_router
from .server_register.handler import router as server_register_router
from .server_settings import router as server_settings_router, adapter_create_router

__all__ = [
    "server_manager_router",
    "delete_server_router",
    "server_register_router",
    "server_settings_router",
    "adapter_create_router",
]