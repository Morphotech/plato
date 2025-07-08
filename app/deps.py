from typing import Generator
from fastapi import Request
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.file_storage import PlatoFileStorage
from jinja2 import Environment as JinjaEnv


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_file_storage(request: Request) -> PlatoFileStorage:
    return request.app.state.file_storage

def get_jinja_env(request: Request) -> JinjaEnv:
    return request.app.state.jinja_env

def get_template_static_directory(request: Request) -> str:
    return request.app.state.template_static_directory
