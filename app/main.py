from contextlib import asynccontextmanager
import json
import uuid
import zipfile
import shutil
from http import HTTPStatus
from mimetypes import guess_extension
from typing import Any, Callable, List, Tuple 
from fastapi import Body, Depends, FastAPI, File, Form, Header, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from jsonschema import ValidationError, validate as json_validate
from sqlalchemy import ARRAY, String, cast as db_cast
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session, Query as SqlQuery
from accept_types import get_best_match
from jinja2 import Environment as JinjaEnv

from app.models.template import Template
from app.deps import get_db, get_file_storage, get_jinja_env, get_template_static_directory
from app.settings import Settings, get_settings
from app.util.path_util import tmp_zipfile_path
from app.util.setup_util import create_template_environment, initialize_file_storage
from app.views.template_detail_view import TemplateDetailView
from app import file_storage
from app.compose.renderer import InvalidPageNumber, Renderer, RendererNotFound, compose
from app.error_messages import template_not_found, resizing_unsupported, \
    single_page_unsupported, aspect_ratio_compromised, negative_number_invalid, \
    unsupported_mime_type, invalid_compose_json, invalid_zip_file, template_already_exists, \
    invalid_directory_structure, invalid_template_details, invalid_json_field
from app.views.template_detail_view import TEMPLATE_UPDATE_SCHEMA
from app.exceptions import UnsupportedMIMEType



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

@app.get("/templates/{template_id}", response_model=dict[str, Any])
def template_by_id(template_id: str, db: Session = Depends(get_db)) -> dict[str, Any] | JSONResponse:
    try:
        template: Template = db.query(Template).filter_by(id=template_id).one()
        view = TemplateDetailView.view_from_template(template)
        return view._asdict()
    except NoResultFound:
        return JSONResponse(content={"message": template_not_found.format(template_id)}, status_code=HTTPStatus.NOT_FOUND)

@app.get("/templates")
def templates(tags: List[str] | None = Query(None), db: Session = Depends(get_db)) -> List[dict[str, Any]]:
    template_query: SqlQuery = db.query(Template)

    if tags:
        template_query = template_query.filter(Template.tags.contains(db_cast(tags, ARRAY(String))))
    json_views = [TemplateDetailView.view_from_template(template)._asdict() for
                      template in
                      template_query]

    return json_views

@app.post("/template/create", response_model=TemplateDetailView)
def create_template(zipfile: UploadFile = File(...), template_details: str = Form(...),
                    db: Session = Depends(get_db), 
                    file_storage: file_storage.PlatoFileStorage = Depends(get_file_storage),
                    settings: Settings = Depends(get_settings)) -> TemplateDetailView | JSONResponse:
    is_zipfile, zip_file_name = _save_and_validate_zipfile(zipfile)
    if not is_zipfile:
        return JSONResponse(content={"message": invalid_zip_file}, status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    template_entry_json = json.loads(template_details)

    template_id = template_entry_json['title']
    new_template = Template.from_json_dict(template_entry_json)

    template = db.query(Template).filter_by(id=template_id).one_or_none()
    if template is not None:
        return JSONResponse(content={"message": template_already_exists.format(template_id)}, status_code=HTTPStatus.CONFLICT)

    try:
        file_storage.save_template_files(template_id, settings.TEMPLATE_DIRECTORY_NAME, zip_file_name)

        db.add(new_template)
        db.commit()
    except IntegrityError:
        return JSONResponse(content={"message": template_already_exists.format(template_id)}, status_code=HTTPStatus.CONFLICT)
    except FileNotFoundError:
        return JSONResponse(content={"message": invalid_directory_structure}, status_code=HTTPStatus.BAD_REQUEST)
    
    return JSONResponse(content=TemplateDetailView.view_from_template(new_template)._asdict(), status_code=HTTPStatus.CREATED)



@app.put("/template/{template_id}/update", response_model=TemplateDetailView)
def update_template(template_id: str,
                    zipfile: UploadFile = File(...), template_details: str = Form(...),
                    db: Session = Depends(get_db),
                    file_storage: file_storage.PlatoFileStorage = Depends(get_file_storage),
                    settings: Settings = Depends(get_settings)) -> TemplateDetailView | JSONResponse:
    is_zipfile, zip_file_name = _save_and_validate_zipfile(zipfile)
    if not is_zipfile:
        return JSONResponse(content={"message": invalid_zip_file}, status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    template_entry_json = json.loads(template_details)

    try:
        json_validate(template_entry_json, schema=TEMPLATE_UPDATE_SCHEMA)
        # update template into database
        template = db.query(Template).filter_by(id=template_id).one()
        template.update_fields(template_entry_json)
        db.commit()

        # uploads template files from zip file to file storage
        file_storage.save_template_files(template_id, settings.TEMPLATE_DIRECTORY_NAME, zip_file_name)
    except NoResultFound:
        return JSONResponse(content={"message": template_not_found.format(template_id)}, status_code=HTTPStatus.NOT_FOUND)
    except FileNotFoundError:
        return JSONResponse(content={"message": invalid_directory_structure}, status_code=HTTPStatus.BAD_REQUEST)
    except ValidationError as ve:
        return JSONResponse(content={"message": invalid_template_details.format(ve.message)}, status_code=HTTPStatus.BAD_REQUEST)

    return JSONResponse(content=TemplateDetailView.view_from_template(template)._asdict())


@app.patch("/template/{template_id}/update_details", response_model=TemplateDetailView)
def update_template_details(template_id: str, template_details: dict = Body(...),
                            db: Session = Depends(get_db)) -> TemplateDetailView | JSONResponse:
    try:
        # update template into database
        template = db.query(Template).filter_by(id=template_id).one()
        template.update_fields(template_details)
        db.commit()
    except NoResultFound:
        return JSONResponse(content={"message": template_not_found.format(template_id)}, status_code=HTTPStatus.NOT_FOUND)
    except KeyError as e:
        return JSONResponse(content={"message": invalid_json_field.format(e.args)}, status_code=HTTPStatus.BAD_REQUEST)

    return JSONResponse(content=TemplateDetailView.view_from_template(template)._asdict())


def _save_and_validate_zipfile(zip_file: UploadFile) -> Tuple[bool, str]:
    """
    Saves in tmp directory and checks if file is a ZIP file.

    Returns:
        bool: Indicates if the file is a ZIP file
        str: ZIP filename it was saved as in the tmp directory

    """
    zip_uid = str(uuid.uuid4())
    zip_file_name = f"zipfile_{zip_uid}"

    with open(tmp_zipfile_path(zip_file_name), "wb") as buffer:
        shutil.copyfileobj(zip_file.file, buffer)
    is_zipfile = zipfile.is_zipfile(zip_file.file)

    return is_zipfile, zip_file_name


@app.post("/template/{template_id}/compose", response_model=None)
def compose_file(template_id: str, payload: dict = Body(...), 
                 page: int | None = Query(None), height: int | None = Query(None), 
                 width: int | None = Query(None), accept: str | None = Header(None),
                 jinja_env: JinjaEnv = Depends(get_jinja_env),
                 template_static_directory: str = Depends(get_template_static_directory), 
                 db: Session = Depends(get_db)) -> StreamingResponse | JSONResponse:
    return _compose(jinja_env, template_static_directory, db, template_id, "compose", lambda t: payload, width, height, page, accept)


@app.get("/template/{template_id}/example", response_model=None)
def example_compose(template_id: str, page: int | None = Query(None), 
                    height: int | None = Query(None), width: int | None = Query(None),
                    accept: str | None = Header(None), jinja_env: JinjaEnv = Depends(get_jinja_env),
                    template_static_directory: str = Depends(get_template_static_directory), 
                    db: Session = Depends(get_db)) -> StreamingResponse | JSONResponse:
    return _compose(jinja_env, template_static_directory, db, template_id, "example", lambda t: t.example_composition, width, height, page, accept)

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
            return JSONResponse(content={"message": resizing_unsupported.format(mime_type)}, status_code=HTTPStatus.BAD_REQUEST)

        if page is not None and mime_type != PNG_MIME:
            return JSONResponse(content={"message": single_page_unsupported.format(mime_type)}, status_code=HTTPStatus.BAD_REQUEST)

        if width is not None and height is not None:
            return JSONResponse(content={"message": aspect_ratio_compromised}, status_code=HTTPStatus.BAD_REQUEST)

        if page is not None and page < 0:
            return JSONResponse(content={"message": negative_number_invalid.format(page)}, status_code=HTTPStatus.BAD_REQUEST)

        compose_params = {}
        if width is not None:
            compose_params["width"] = width
        if height is not None:
            compose_params["height"] = height
        if page is not None:
            compose_params["page"] = page

        template_model: Template = db.query(Template).filter_by(id=template_id).one()
        compose_data = compose_retrieval_function(template_model)
        composed_file = compose(template_model, compose_data, mime_type, jinja_env, template_static_directory, **compose_params)
        return StreamingResponse(composed_file, media_type=mime_type,
                                 headers={
        "Content-Disposition": f"attachment; filename={file_name}{guess_extension(mime_type)}"
                                 })
    except (RendererNotFound, UnsupportedMIMEType):
        return JSONResponse(
                content={"message": unsupported_mime_type.format(accept_header, ", ".join(ALL_AVAILABLE_MIME_TYPES))}, status_code=HTTPStatus.NOT_ACCEPTABLE)
    except InvalidPageNumber as e:
        return JSONResponse(content={"message": e.message}, status_code=HTTPStatus.BAD_REQUEST)
    except NoResultFound:
        return JSONResponse(content={"message": template_not_found.format(template_id)}, status_code=HTTPStatus.NOT_FOUND)
    except ValidationError as ve:
        return JSONResponse(content={"message": invalid_compose_json.format(ve.message)}, status_code=HTTPStatus.BAD_REQUEST)
