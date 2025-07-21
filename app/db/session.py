from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import get_settings

settings = get_settings()


if settings.SQLALCHEMY_DATABASE_URI is not None:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def db_session() -> Iterator:
    """
    Yields a database session, and closes it after it is no longer needed (or if an issue occurs)

    :return: The database session
    :rtype: Iterator
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
