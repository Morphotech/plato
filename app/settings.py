import os
from functools import lru_cache

from pydantic import field_validator, PostgresDsn
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

SETTINGS_DIR = os.path.dirname(__file__)

class Settings(BaseSettings):
    DB_DATABASE: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str 
    DB_PORT: int
    SQLALCHEMY_DATABASE_URI: str | None = None

    STORAGE_TYPE: str
    TEMPLATE_DIRECTORY: str
    TEMPLATE_DIRECTORY_NAME: str
    DATA_DIR: str 
    S3_BUCKET: str | None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, values: ValidationInfo) -> str:
        return v or PostgresDsn.build(
            scheme="postgresql",
            username=values.data["DB_USERNAME"],
            password=values.data["DB_PASSWORD"],
            host=values.data["DB_HOST"],
            port=int(values.data["DB_PORT"]),
            path=values.data['DB_DATABASE'],
        ).unicode_string()

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=[os.path.join(SETTINGS_DIR, "../.env")]
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()

