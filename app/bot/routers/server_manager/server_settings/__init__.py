from .handler import router
from .adapter_create import router as adapter_create_router
from .adapter_delete import router as adapter_delete_router
from .adapter_update import router as adapter_update_router

__all__ = [
    "router",
    "adapter_create_router",
    "adapter_delete_router",
    "adapter_update_router",
]