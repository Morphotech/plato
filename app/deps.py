from functools import lru_cache
from typing import Generator

from jinja2 import Environment as JinjaEnv
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.settings import get_settings
from app.util.setup_util import create_template_environment


def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for dependency injection in FastAPI routes.
    """
    with db_session() as db:
        yield db


@lru_cache
def get_jinja_env() -> JinjaEnv:
    """
    Builds (once) the Jinja environment used to render templates, from settings.

    :return: The Jinja environment
    :rtype: JinjaEnv
    """
    return create_template_environment(get_settings().TEMPLATE_DIRECTORY)
