from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.settings import get_settings

settings = get_settings()

def db_url(database_name: str) -> str:
    return f'postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{database_name}'

engine = create_engine(db_url(settings.DB_DATABASE), future=True)

SessionLocal = sessionmaker(bind=engine)

ModelBase = DeclarativeBase()

