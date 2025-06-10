from .handler import router as server_manager_router
from .server_delete.handler import router as server_delete_router
from .server_register.handler import router as server_register_router
from .server_edit.handler import router as server_edit_router
from .server_settings import (
    router as server_settings_router,
    adapter_create_router,
    adapter_delete_router,
    adapter_update_router,
)

__all__ = [
    "server_manager_router",
    "server_delete_router",
    "server_register_router",
    "server_edit_router",
    "server_settings_router",
    "adapter_create_router",
    "adapter_delete_router",
    "adapter_update_router",
]