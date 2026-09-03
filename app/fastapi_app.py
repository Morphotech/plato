import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import deps
from app.api.routers.templates import router as templates_router
from app.db.session import db_session
from app.settings import get_settings
from app.util.setup_util import initialize_file_storage

logger = logging.getLogger(__name__)


def get_app() -> FastAPI:
    """
    Builds and returns the Plato FastAPI application.

    Returns:
        FastAPI: the configured app instance.
    """
    settings = get_settings()
    logger.info(f"Plato starting up (storage={settings.STORAGE_TYPE}, template_directory={settings.TEMPLATE_DIRECTORY})")

    fastapi_app = FastAPI()

    settings = get_settings()
    file_storage = initialize_file_storage(settings.STORAGE_TYPE, settings.DATA_DIR, settings.BUCKET_NAME)
    with db_session() as db:
        file_storage.load_templates(settings.TEMPLATE_DIRECTORY, settings.TEMPLATE_DIRECTORY_NAME, db)

    fastapi_app.include_router(templates_router)

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
        allow_headers=["*"],  # Allows all headers
    )

    return fastapi_app
