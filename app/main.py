from contextlib import asynccontextmanager
from http import HTTPStatus
from mimetypes import guess_extension
from typing import Callable, List

from accept_types import get_best_match
from fastapi import Body, Depends, FastAPI, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from jinja2 import Environment as JinjaEnv
from jsonschema import ValidationError
from sqlalchemy import ARRAY, String, cast as db_cast
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, Query as SqlQuery

from app.compose.renderer import InvalidPageNumber, Renderer, RendererNotFound, compose
from app.deps import get_db, get_jinja_env, get_template_static_directory
from app.error_messages import template_not_found, resizing_unsupported, \
    single_page_unsupported, aspect_ratio_compromised, negative_number_invalid, \
    unsupported_mime_type, invalid_compose_json
from app.exceptions import UnsupportedMIMEType
from app.models.template import Template
from app.schemas.template_detail import TemplateDetailSchema
from app.settings import get_settings
from app.util.setup_util import create_template_environment, initialize_file_storage


@asynccontextmanager
async def lifespan(api: FastAPI):
    settings = get_settings()
    api.state.file_storage = initialize_file_storage(settings.STORAGE_TYPE, settings.DATA_DIR, settings.S3_BUCKET)
    api.state.jinja_env = create_template_environment(settings.TEMPLATE_DIRECTORY)
    api.state.template_static_directory = f"{settings.TEMPLATE_DIRECTORY}/static"
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/templates/{template_id}", response_model=TemplateDetailSchema)
def template_by_id(template_id: str, db: Session = Depends(get_db)) -> TemplateDetailSchema | JSONResponse:
    try:
        template = db.query(Template).filter_by(id=template_id).one()
        return TemplateDetailSchema.model_validate(template)
    except NoResultFound:
        return JSONResponse(content={"message": template_not_found.format(template_id)},
                            status_code=HTTPStatus.NOT_FOUND)


@app.get("/templates", response_model=List[TemplateDetailSchema])
def templates(tags: List[str] | None = Query(None), db: Session = Depends(get_db)) -> List[TemplateDetailSchema]:
    template_query: SqlQuery = db.query(Template)

    if tags:
        template_query = template_query.filter(Template.tags.contains(db_cast(tags, ARRAY(String))))

    return [TemplateDetailSchema.model_validate(template) for template in template_query]


@app.post("/template/{template_id}/compose", response_model=None)
def compose_file(template_id: str, payload: dict = Body(...),
                 page: int | None = Query(None), height: int | None = Query(None),
                 width: int | None = Query(None), accept: str | None = Header(None),
                 jinja_env: JinjaEnv = Depends(get_jinja_env),
                 template_static_directory: str = Depends(get_template_static_directory),
                 db: Session = Depends(get_db)) -> StreamingResponse | JSONResponse:
    return _compose(jinja_env, template_static_directory, db, template_id, "compose", lambda t: payload, width, height,
                    page, accept)


@app.get("/template/{template_id}/example", response_model=None)
def example_compose(template_id: str, page: int | None = Query(None),
                    height: int | None = Query(None), width: int | None = Query(None),
                    accept: str | None = Header(None), jinja_env: JinjaEnv = Depends(get_jinja_env),
                    template_static_directory: str = Depends(get_template_static_directory),
                    db: Session = Depends(get_db)) -> StreamingResponse | JSONResponse:
    return _compose(jinja_env, template_static_directory, db, template_id, "example", lambda t: t.example_composition,
                    width, height, page, accept)


PDF_MIME = "application/pdf"
HTML_MIME = "text/html"
PNG_MIME = "image/png"
OCTET_STREAM = "application/octet-stream"

ALL_AVAILABLE_MIME_TYPES = list(Renderer.renderers.keys())


def _compose(
        jinja_env: JinjaEnv,
        template_static_directory: str,
        db: Session,
        template_id: str,
        file_name: str,
        compose_retrieval_function: Callable[[Template], dict],
        width: int | None,
        height: int | None,
        page: int | None,
        accept_header: str | None = PDF_MIME) -> StreamingResponse | JSONResponse:
    mime_type = get_best_match(accept_header, ALL_AVAILABLE_MIME_TYPES)

    try:
        if mime_type is None:
            raise UnsupportedMIMEType(accept_header)

        if (width is not None or height is not None) and mime_type != PNG_MIME:
            return JSONResponse(content={"message": resizing_unsupported.format(mime_type)},
                                status_code=HTTPStatus.BAD_REQUEST)

        if page is not None and mime_type != PNG_MIME:
            return JSONResponse(content={"message": single_page_unsupported.format(mime_type)},
                                status_code=HTTPStatus.BAD_REQUEST)

        if width is not None and height is not None:
            return JSONResponse(content={"message": aspect_ratio_compromised}, status_code=HTTPStatus.BAD_REQUEST)

        if page is not None and page < 0:
            return JSONResponse(content={"message": negative_number_invalid.format(page)},
                                status_code=HTTPStatus.BAD_REQUEST)

        compose_params = {}
        if width is not None:
            compose_params["width"] = width
        if height is not None:
            compose_params["height"] = height
        if page is not None:
            compose_params["page"] = page

        template_model: Template = db.query(Template).filter_by(id=template_id).one()
        compose_data = compose_retrieval_function(template_model)
        composed_file = compose(template_model, compose_data, mime_type, jinja_env, template_static_directory,
                                **compose_params)
        return StreamingResponse(composed_file, media_type=mime_type,
                                 headers={
                                     "Content-Disposition": f"attachment; filename={file_name}{guess_extension(mime_type)}"
                                 })
    except (RendererNotFound, UnsupportedMIMEType):
        return JSONResponse(
            content={"message": unsupported_mime_type.format(accept_header, ", ".join(ALL_AVAILABLE_MIME_TYPES))},
            status_code=HTTPStatus.NOT_ACCEPTABLE)
    except InvalidPageNumber as e:
        return JSONResponse(content={"message": e.message}, status_code=HTTPStatus.BAD_REQUEST)
    except NoResultFound:
        return JSONResponse(content={"message": template_not_found.format(template_id)},
                            status_code=HTTPStatus.NOT_FOUND)
    except ValidationError as ve:
        return JSONResponse(content={"message": invalid_compose_json.format(ve.message)},
                            status_code=HTTPStatus.BAD_REQUEST)
