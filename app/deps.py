from contextlib import contextmanager
from typing import Generator
from fastapi import Request
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.file_storage import PlatoFileStorage
from jinja2 import Environment as JinjaEnv


def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for dependency injection in FastAPI routes.
    """
    with db_session() as db:
        yield db


def get_file_storage(request: Request) -> PlatoFileStorage:
    """
    Retrieves the file storage instance from the request's application state.

    :param request: The FastAPI request object
    :type request: Request

    :return: The file storage instance
    :rtype: PlatoFileStorage
    """
    return request.app.state.file_storage

def get_jinja_env(request: Request) -> JinjaEnv:
    """
    Retrieves the Jinja environment from the request's application state.

    :param request: The FastAPI request object
    :type request: Request

    :return: The Jinja environment
    :rtype: JinjaEnv
    """
    return request.app.state.jinja_env

def get_template_static_directory(request: Request) -> str:
    """
    Retrieves the static directory for templates from the request's application state.

    :param request: The FastAPI request object
    :type request: Request

    :return: The static directory path for templates
    """
    return request.app.state.template_static_directory
