from .models import User, Server, ServerAPIData
from .session import AsyncSessionLocal
from sqlalchemy import select, update, delete

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

async def get_user_by_id(user_id: int):
    async with AsyncSessionLocal() as session:
        return await session.get(User, user_id)

async def create_user(user_data: dict):
    async with AsyncSessionLocal() as session:
        user = User(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
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
            update(User).where(User.tg_id == tg_id).values(authenticated=value)
        )
        await session.commit()
        
async def delete_server_and_api_data(server_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(ServerAPIData).where(ServerAPIData.server_id == server_id)
        )
        await session.execute(
            delete(Server).where(Server.id == server_id)
        )
        await session.commit()        

async def get_server_api_data_by_server_id_and_tg_id(server_id: int, tg_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ServerAPIData).where(
                ServerAPIData.server_id == server_id,
                ServerAPIData.tg_id == tg_id
            )
        )
        return result.scalar_one_or_none()
    
async def get_server_by_id(server_id: int):
    async with AsyncSessionLocal() as session:
        return await session.get(Server, server_id)
    
async def get_admin_api_data_for_server(server_id: int):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(ServerAPIData)
            .join(User, ServerAPIData.tg_id == User.tg_id)
            .where(
                ServerAPIData.server_id == server_id,
                User.is_admin == True
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()