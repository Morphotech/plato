import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jinja2 import Environment as JinjaEnv, DictLoader, select_autoescape
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.db.base_class import Base
from app.deps import get_db
from app.file_storage import DiskFileStorage, S3FileStorage
from app.main import app
from app.settings import get_settings

settings = get_settings()
settings.S3_BUCKET = 'test_template_bucket'


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
def fastapi_client_s3_storage(db):
    @asynccontextmanager
    async def mock_lifespan(app):
        with tempfile.TemporaryDirectory() as file_dir:
            app.state.file_storage = S3FileStorage(file_dir, settings.S3_BUCKET)
            app.state.jinja_env = JinjaEnv(
                loader=DictLoader({}),
                autoescape=select_autoescape(["html", "xml"]),
                auto_reload=True
            )
            current_folder = Path(__file__).resolve().parent
            app.state.template_static_directory = str(current_folder / "resources/static")
            yield

    app.dependency_overrides[get_db] = lambda: db
    app.router.lifespan_context = mock_lifespan

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope='class')
def fastapi_client_local_storage(db):
    @asynccontextmanager
    async def mock_lifespan(app):
        with tempfile.TemporaryDirectory() as file_dir:
            app.state.file_storage = DiskFileStorage(file_dir)
            app.state.jinja_env = JinjaEnv(
                loader=DictLoader({}),
                autoescape=select_autoescape(["html", "xml"]),
                auto_reload=True
            )
            current_folder = Path(__file__).resolve().parent
            app.state.template_static_directory = str(current_folder / "resources/static")
            yield

    app.dependency_overrides[get_db] = lambda: db
    app.router.lifespan_context = mock_lifespan

    with TestClient(app) as client:
        yield client