from dataclasses import dataclass, field
from environs import Env

@dataclass
class LoggingConfig:
    LEVEL: str = "INFO"
    FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ARCHIVE_FORMAT: str = "zip"  

@dataclass
class Config:
    TOKEN: str
    DATABASE_URL: str
    TIMEZONE: str = "UTC"
    SERVER_HEALTH_INTERVAL: int = 300
    USER_SYNC_INTERVAL: int = 60
    LOGGING: LoggingConfig = field(default_factory=LoggingConfig)  

def load_config() -> Config:
    env = Env()
    env.read_env() 

    return Config(
        TOKEN=env.str("TOKEN"),
        DATABASE_URL=env.str("DATABASE_URL"),
        TIMEZONE=env.str("TIMEZONE", "UTC"),
        SERVER_HEALTH_INTERVAL=env.int("SERVER_HEALTH_INTERVAL", 300),
        USER_SYNC_INTERVAL=env.int("USER_SYNC_INTERVAL", 60),
    )