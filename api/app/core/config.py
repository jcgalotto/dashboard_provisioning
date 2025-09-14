from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ORACLE_DSN: str = ""
    ORACLE_USER: str = ""
    ORACLE_PASSWORD: str = ""
    ORACLE_POOL_MIN: int = 1
    ORACLE_POOL_MAX: int = 5
    JWT_SECRET: str = "change_me"
    JWT_EXPIRES_MIN: int = 60
    LOG_FILE_PATH: str = "/var/log/app/app.log"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
