import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, mock_open, patch

import pytest
from fastapi.testclient import TestClient
from google.cloud import storage
from google.cloud.storage import Client
from jinja2 import Environment as JinjaEnv, DictLoader, select_autoescape
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.db.base_class import Base
from app.deps import get_db
from app.file_storage import DiskFileStorage, S3FileStorage, GCSFileStorage
from app.main import app
from app.settings import get_settings

settings = get_settings()
settings.BUCKET_NAME = 'test_template_bucket'

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
    mock_aws_credentials_data = """\
    {"aws_access_key_id": "test_aws_key",
     "aws_secret_access_key": "test_secret_key",
     "region_name": "test_region"}
     """
    mock_aws_open = mock_open(read_data=mock_aws_credentials_data)
    with patch("builtins.open", mock_aws_open):
        @asynccontextmanager
        async def mock_lifespan(app):
            with tempfile.TemporaryDirectory() as file_dir:
                app.state.file_storage = S3FileStorage(file_dir, settings.BUCKET_NAME)
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
def fastapi_client_gcs_storage(db):
    @asynccontextmanager
    async def mock_lifespan(app):
        with tempfile.TemporaryDirectory() as file_dir, mock.patch.object(Client, "from_service_account_json") as mock_init_client:
            gcs_client = MagicMock(spec=Client)
            bucket = MagicMock(spec=storage.Bucket)
            gcs_client.bucket.return_value = bucket
            mock_init_client.return_value = gcs_client
            app.state.mocked_bucket = bucket
            app.state.file_storage = GCSFileStorage(file_dir, settings.BUCKET_NAME)
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