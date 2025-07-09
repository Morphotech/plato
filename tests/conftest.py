import tempfile
import ssl
from contextlib import asynccontextmanager, nullcontext
from time import sleep
from typing import Generator 
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jinja2 import Environment as JinjaEnv, DictLoader, select_autoescape
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.compose import DockerCompose
from testcontainers.core.utils import inside_container

from app.db.models import Base
from app.file_storage import DiskFileStorage, S3FileStorage
from app.main import app
from app.deps import get_db


BUCKET_NAME = 'test_template_bucket'

TEST_DB_URL = f"postgresql://test:test@{'database:5432' if inside_container() else 'localhost:5456'}/test"



def override_get_db():
    test_engine = create_engine(TEST_DB_URL, future=True)
    TestingSessionLocal = sessionmaker(bind=test_engine)
    db = TestingSessionLocal()
    Base.metadata.create_all(test_engine)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope='class')
def db() -> Generator[Session, None, None]:
    yield from override_get_db()



def fastapi_client(lifespan) -> Generator[TestClient, None, None]:
    if inside_container():
        context_manager = nullcontext()
    else:
        current_folder = str(Path(__file__).resolve().parent)
        docker_compose_path = f"{current_folder}/docker/"
        context_manager = DockerCompose(filepath=docker_compose_path, 
                                        compose_file_name="docker-compose.local.test.yml")
    with context_manager:
        sleep(5)

        app.router.lifespan_context = lifespan
        with TestClient(app) as client:
            yield client

@pytest.fixture(scope='class')
def fastapi_client_local_storage():
    @asynccontextmanager
    async def mock_lifespan_local_storage(app: FastAPI):
        app.dependency_overrides[get_db] = override_get_db
        with tempfile.TemporaryDirectory() as file_dir:
            app.state.file_storage = DiskFileStorage(file_dir)
            app.state.jinja_env = JinjaEnv(loader=DictLoader({}), 
                                           autoescape=select_autoescape(["html", "xml"]),
                                           auto_reload=True)
            current_folder = str(Path(__file__).resolve().parent)
            app.state.template_static_directory = f"{current_folder}/resources/static"
            yield
        app.dependency_overrides.clear()
    yield from fastapi_client(mock_lifespan_local_storage)


@pytest.fixture(scope='class')
def fastapi_client_s3_storage():
    @asynccontextmanager
    async def mock_lifespan_s3_storage(app: FastAPI):
        app.dependency_overrides[get_db] = override_get_db
        with tempfile.TemporaryDirectory() as file_dir:
            app.state.file_storage = S3FileStorage(file_dir, BUCKET_NAME)
            app.state.jinja_env = JinjaEnv(loader=DictLoader({}), 
                                           autoescape=select_autoescape(["html", "xml"]),
                                           auto_reload=True)
            current_folder = str(Path(__file__).resolve().parent)
            app.state.template_static_directory = f"{current_folder}/resources/static"
            yield
        app.dependency_overrides.clear()
    yield from fastapi_client(mock_lifespan_s3_storage)


