from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_DATABASE: str = ""
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: int = 5455
    STORAGE_TYPE: str = ""
    TEMPLATE_DIRECTORY: str = ""
    TEMPLATE_DIRECTORY_NAME: str = ""
    DATA_DIR: str = ""
    S3_BUCKET: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

