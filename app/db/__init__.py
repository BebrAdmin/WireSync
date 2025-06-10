from .base import Base
from .models import User, Server, ServerAPIData
from .session import engine, AsyncSessionLocal
from .crud import (
    # --- Server CRUD ---
    create_server,
    get_server_by_name,
    get_server_by_api_url,
    get_all_servers,
    get_server_by_id,
    update_server,
    delete_server_and_api_data,

    # --- Server API Data CRUD ---
    create_server_api_data,
    get_server_api_data_by_server_id,
    get_server_api_data_by_server_id_and_tg_id,
    get_server_api_data_by_server_id_and_user_id,
    get_admin_api_data_for_server,

    # --- User CRUD ---
    create_user,
    get_user_by_id,
    get_user_by_tg_id,
    get_user_by_email,
    set_user_registered,
    set_user_authenticated,
    get_all_users,

    # --- UserServerAccess CRUD ---
    add_user_server_access,
    get_user_server_access,
    get_servers_for_user,
    get_users_for_server,
    remove_user_server_access,

    # --- Invite CRUD ---
    create_invite,
    get_invite_by_code,
    set_invite_used,
    deactivate_invite,
    delete_invite,
    get_active_invites,
    get_invite_by_used_by,
)

__all__ = [
    "Base",
    "User",
    "Server",
    "ServerAPIData",
    "engine",
    "AsyncSessionLocal",

    # --- Server CRUD ---
    "create_server",
    "get_server_by_name",
    "get_server_by_api_url",
    "get_all_servers",
    "get_server_by_id",
    "update_server",
    "delete_server_and_api_data",

    # --- Server API Data CRUD ---
    "create_server_api_data",
    "get_server_api_data_by_server_id",
    "get_server_api_data_by_server_id_and_tg_id",
    "get_server_api_data_by_server_id_and_user_id",
    "get_admin_api_data_for_server",

    # --- User CRUD ---
    "create_user",
    "get_user_by_id",
    "get_user_by_tg_id",
    "get_user_by_email",
    "set_user_registered",
    "set_user_authenticated",
    "get_all_users",

    # --- UserServerAccess CRUD ---
    "add_user_server_access",
    "get_user_server_access",
    "get_servers_for_user",
    "get_users_for_server",
    "remove_user_server_access",

    # --- Invite CRUD ---
    "create_invite",
    "get_invite_by_code",
    "set_invite_used",
    "deactivate_invite",
    "delete_invite",
    "get_active_invites",
    "get_invite_by_used_by",
]