from sqlalchemy import Column, Integer, String, DateTime, func, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, unique=True, index=True, nullable=False) 
    tg_name = Column(String(128), nullable=False)  
    email = Column(String(128), unique=True, index=True, nullable=True)  
    phone = Column(String(20), nullable=True)                            
    department = Column(String(64), nullable=True)                       
    is_authenticated = Column(Boolean, default=False, nullable=False)
    is_registered = Column(Boolean, default=False, nullable=False) 
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, index=True, nullable=False)
    description = Column(String(256), nullable=True)
    api_url = Column(String(256), nullable=False)
    status = Column(String(16), nullable=False, default="active") 
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_checked = Column(DateTime, default=None)
    
    api_data = relationship("ServerAPIData", back_populates="server", uselist=False)

class ServerAPIData(Base):
    __tablename__ = "server_api_data"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)  
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)     
    tg_id = Column(Integer, nullable=False)
    password = Column(String(64), nullable=False)
    api_login = Column(String(128), nullable=False)
    api_password = Column(String(64), nullable=False)

    server = relationship("Server", back_populates="api_data")
    user = relationship("User")  

    __table_args__ = (
        UniqueConstraint('server_id', 'user_id', name='uix_serverid_userid'),  
    )
    
class UserServerAccess(Base):
    __tablename__ = "user_server_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    
class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False)
    server_ids = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    admin_tg_id = Column(Integer, nullable=False, index=True)  
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)