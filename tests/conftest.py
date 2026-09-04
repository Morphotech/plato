import tempfile
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from jinja2 import Environment as JinjaEnv, DictLoader, select_autoescape
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.db.base_class import Base
from app.deps import get_db, get_jinja_env
from app.fastapi_app import get_app
from app.file_storage import DiskFileStorage
from app.settings import get_settings

settings = get_settings()
settings.BUCKET_NAME = 'test_template_bucket'
settings.TEMPLATE_DIRECTORY = str(Path(__file__).resolve().parent / "resources")

@pytest.fixture(scope="session")
def db():
    if settings.IN_DOCKER:
        yield from _setup_test_db(settings.SQLALCHEMY_DATABASE_URI)
    else:
        context_manager = PostgresContainer(image=f"postgres:{settings.POSTGRES_VER}")
        with context_manager:
            yield from _setup_test_db(context_manager.get_connection_url())


def _setup_test_db(database_uri):
    test_engine = create_engine(database_uri, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    try:
        db = TestingSessionLocal()
        Base.metadata.create_all(bind=test_engine)
        yield db
    except Exception:
        db.rollback()
    finally:
        db.close()


@pytest.fixture(scope='class')
def fastapi_client_local_storage(db):
    with tempfile.TemporaryDirectory() as file_dir, \
         mock.patch("app.fastapi_app.initialize_file_storage", return_value=DiskFileStorage(file_dir)), \
         mock.patch("app.fastapi_app.db_session", return_value=db):
        jinja_env = JinjaEnv(
            loader=DictLoader({}),
            autoescape=select_autoescape(["html", "xml"]),
            auto_reload=True
        )

        app = get_app()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_jinja_env] = lambda: jinja_env

        with TestClient(app) as client:
            yield client