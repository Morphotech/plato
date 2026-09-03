from mimetypes import guess_extension
from typing import Callable, List, Annotated

from accept_types import get_best_match
from fastapi import APIRouter, Body, Depends, Query, Header
from fastapi.responses import StreamingResponse
from jinja2 import Environment as JinjaEnv
from jsonschema import ValidationError
from sqlalchemy import ARRAY, String, cast as db_cast
from sqlalchemy.orm import Session, Query as SqlQuery

from app.compose.renderer import InvalidPageNumber, Renderer, RendererNotFound, compose
from app.deps import get_db, get_jinja_env
from app.exceptions import UnsupportedMIMEType, PNGCompositionUnavailable, UnsupportedResizingException, \
    SinglePageUnsupportedException, TemplateNotFoundException, InvalidPageNumberException, \
    JSONSchemaVerificationErrorException
from app.models.template import Template
from app.request_logger_route import RequestLoggerRoute
from app.schemas.compose import ComposeBaseSchema, ComposeSchema
from app.schemas.template_detail import TemplateDetailSchema, MIMETypeEnum

ALL_AVAILABLE_MIME_TYPES = list(Renderer.renderers.keys())

router = APIRouter(route_class=RequestLoggerRoute)


@router.get("/templates/{template_id}", response_model=TemplateDetailSchema)
def template_by_id(template_id: str, db: Annotated[Session, Depends(get_db)]) -> Template:

    template = db.query(Template).filter_by(id=template_id).one_or_none()
    if template is None:
        raise TemplateNotFoundException(template_id)

    return template


@router.get("/templates", response_model=List[TemplateDetailSchema])
def templates(db: Annotated[Session, Depends(get_db)], tags: Annotated[List[str] | None, Query(...)] = None) -> List[Template]:
    template_query: SqlQuery = db.query(Template)

    if tags:
        template_query = template_query.filter(Template.tags.contains(db_cast(tags, ARRAY(String))))

    return template_query.all()


@router.post("/template/{template_id}/compose", response_model=None)
def compose_file(template_id: str, compose_file_schema: Annotated[ComposeSchema, Query(...)],
                 payload: Annotated[dict, Body(...)], jinja_env: Annotated[JinjaEnv, Depends(get_jinja_env)],
                 db: Annotated[Session, Depends(get_db)],
                 custom_accept: Annotated[str | None, Header(...)] = None) -> StreamingResponse:
    return _compose(db, jinja_env,
                    lambda t: payload, template_id, "compose", compose_file_schema, custom_accept)


@router.get("/template/{template_id}/example", response_model=None)
def example_compose(template_id: str, compose_file_schema: Annotated[ComposeSchema, Query(...)],
                    jinja_env: Annotated[JinjaEnv, Depends(get_jinja_env)],
                    db: Annotated[Session, Depends(get_db)],
                    custom_accept: Annotated[str | None, Header(...)] = None) -> StreamingResponse:
    return _compose(db, jinja_env,
                    lambda t: t.example_composition, template_id, "example", compose_file_schema, custom_accept)


def _compose(db: Session, jinja_env: JinjaEnv,
             compose_retrieval_function: Callable[[Template], dict], template_id: str, file_name: str,
             compose_schema: ComposeBaseSchema, custom_accept: str | None) -> StreamingResponse:
    accept_header = custom_accept or MIMETypeEnum.PDF_MIME.value
    mime_type = get_best_match(accept_header, ALL_AVAILABLE_MIME_TYPES)

    if mime_type is None:
        raise UnsupportedMIMEType(accept_header)

    if mime_type == MIMETypeEnum.PNG_MIME:
        raise PNGCompositionUnavailable()

    if (compose_schema.width is not None or compose_schema.height is not None) and mime_type != MIMETypeEnum.PNG_MIME:
        raise UnsupportedResizingException(mime_type)

    if compose_schema.page is not None and mime_type != MIMETypeEnum.PNG_MIME:
        raise SinglePageUnsupportedException(mime_type)

    template_model: Template | None = db.query(Template).filter_by(id=template_id).one_or_none()
    if template_model is None:
        raise TemplateNotFoundException(template_id)

    try:
        compose_data = compose_retrieval_function(template_model)
        composed_file = compose(template_model, compose_data, mime_type, jinja_env,
                                **compose_schema.model_dump(exclude_none=True))
        return StreamingResponse(composed_file, media_type=mime_type,
                                 headers={
                                     "Content-Disposition": f"attachment; filename={file_name}{guess_extension(mime_type)}"
                                 })
    except RendererNotFound as e:
        raise UnsupportedMIMEType(mime_type) from e
    except InvalidPageNumber as e:
        raise InvalidPageNumberException(compose_schema.page) from e
    except ValidationError as ve:
        raise JSONSchemaVerificationErrorException() from ve
