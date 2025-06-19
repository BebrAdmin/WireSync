from .models import User, Server, ServerAPIData, UserServerAccess, Invite
from .session import AsyncSessionLocal
from sqlalchemy import select, update, delete

# --- Server CRUD ---

async def create_server(server_data: dict):
    server_data.pop("country_tag", None)
    async with AsyncSessionLocal() as session:
        server = Server(**server_data)
        session.add(server)
        await session.commit()
        await session.refresh(server)
        return server

async def get_server_by_name(name: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Server).where(Server.name == name)
        )
        return result.scalar_one_or_none()

async def get_server_by_api_url(api_url: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Server).where(Server.api_url == api_url)
        )
        return result.scalar_one_or_none()

async def get_all_servers():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Server))
        return result.scalars().all()

async def get_server_by_id(server_id: int):
    async with AsyncSessionLocal() as session:
        return await session.get(Server, server_id)

async def update_server(server_id: int, name: str, description: str):
    async with AsyncSessionLocal() as session:
        server = await session.get(Server, server_id)
        if not server:
            return None
        server.name = name
        server.description = description
        await session.commit()
        await session.refresh(server)
        return server

async def delete_server_and_api_data(server_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(ServerAPIData).where(ServerAPIData.server_id == server_id)
        )
        await session.execute(
            delete(UserServerAccess).where(UserServerAccess.server_id == server_id)
        )
        await session.execute(
            delete(Server).where(Server.id == server_id)
        )
        await session.commit()

# --- Server API Data CRUD ---

async def create_server_api_data(api_data: dict):
    async with AsyncSessionLocal() as session:
        api_entry = ServerAPIData(**api_data)
        session.add(api_entry)
        await session.commit()
        await session.refresh(api_entry)
        return api_entry

async def get_server_api_data_by_server_id(server_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ServerAPIData).where(ServerAPIData.server_id == server_id)
        )
        return result.scalar_one_or_none()

async def get_server_api_data_by_server_id_and_tg_id(server_id: int, tg_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ServerAPIData).where(
                ServerAPIData.server_id == server_id,
                ServerAPIData.tg_id == tg_id
            )
        )
        return result.scalar_one_or_none()

async def get_server_api_data_by_server_id_and_user_id(server_id: int, user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ServerAPIData).where(
                ServerAPIData.server_id == server_id,
                ServerAPIData.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

async def get_admin_api_data_for_server(server_id: int):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(ServerAPIData)
            .join(User, ServerAPIData.user_id == User.id)
            .where(
                ServerAPIData.server_id == server_id,
                User.is_admin == True
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

# --- User CRUD ---

async def create_user(user_data: dict):
    async with AsyncSessionLocal() as session:
        user = User(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def get_user_by_id(user_id: int):
    async with AsyncSessionLocal() as session:
        return await session.get(User, user_id)

async def get_user_by_tg_id(tg_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        return result.scalar_one_or_none()

async def get_user_by_email(email: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

async def set_user_registered(tg_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User).where(User.tg_id == tg_id).values(is_registered=True)
        )
        await session.commit()

async def set_user_authenticated(tg_id: int, value: bool = True):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User).where(User.tg_id == tg_id).values(is_authenticated=value)
        )
        await session.commit()

async def get_all_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

# --- UserServerAccess CRUD ---

async def add_user_server_access(user_id: int, server_id: int):
    async with AsyncSessionLocal() as session:
        access = UserServerAccess(user_id=user_id, server_id=server_id)
        session.add(access)
        await session.commit()
        await session.refresh(access)
        return access

async def get_user_server_access(user_id: int, server_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserServerAccess).where(
                UserServerAccess.user_id == user_id,
                UserServerAccess.server_id == server_id
            )
        )
        return result.scalar_one_or_none()

async def get_servers_for_user(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserServerAccess.server_id).where(UserServerAccess.user_id == user_id)
        )
        return [row[0] for row in result.all()]

async def get_users_for_server(server_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserServerAccess.user_id).where(UserServerAccess.server_id == server_id)
        )
        return [row[0] for row in result.all()]

async def remove_user_server_access(user_id: int, server_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(UserServerAccess).where(
                UserServerAccess.user_id == user_id,
                UserServerAccess.server_id == server_id
            )
        )
        await session.commit()

# --- Invite CRUD ---

async def create_invite(code: str, server_ids: list, is_admin: bool = False, admin_tg_id: int = None):
    async with AsyncSessionLocal() as session:
        invite = Invite(
            code=code,
            server_ids=server_ids,
            is_admin=is_admin,
            admin_tg_id=admin_tg_id 
        )
        session.add(invite)
        await session.commit()
        await session.refresh(invite)
        return invite

async def get_invite_by_code(code: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Invite).where(Invite.code == code)
        )
        return result.scalar_one_or_none()

async def set_invite_used(invite_id: int, tg_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Invite)
            .where(Invite.id == invite_id)
            .values(used_by=tg_id, is_active=False)
        )
        await session.commit()

async def deactivate_invite(invite_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Invite)
            .where(Invite.id == invite_id)
            .values(is_active=False)
        )
        await session.commit()

async def delete_invite(invite_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(Invite).where(Invite.id == invite_id)
        )
        await session.commit()

async def get_active_invites():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Invite).where(Invite.is_active == True)
        )
        return result.scalars().all()
    
async def get_invite_by_used_by(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Invite).where(Invite.used_by == user_id)
        )
        return result.scalar_one_or_none()