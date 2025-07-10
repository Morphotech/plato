import io
from math import isclose
from contextlib import asynccontextmanager
from PIL import Image
import tempfile
from pathlib import Path
from fastapi import FastAPI
from app.file_storage import DiskFileStorage
from fastapi.testclient import TestClient
import pytest
from jinja2 import DictLoader, select_autoescape
from sqlalchemy.orm import Session
from http import HTTPStatus
from fitz import Document
from jinja2 import Environment as JinjaEnv
from itertools import chain
from app.error_messages import aspect_ratio_compromised, resizing_unsupported, \
                            unsupported_mime_type

from app.models.template import Template
from app.deps import get_db
from app.main import ALL_AVAILABLE_MIME_TYPES
from tests.conftest import fastapi_client, override_get_db
from tests import get_message


PLAIN_TEXT_TEMPLATE_ID = "plain_text"
PNG_IMAGE_TEMPLATE_ID = "png_image"
QR_CODE_TEMPLATE_ID = 'qr_code'
NO_IMAGE_TEMPLATE_ID = PNG_IMAGE_TEMPLATE_ID.replace('p', 'u')
PNG_IMAGE_NAME = "balloons.png"

@pytest.fixture(scope='class')
def client_with_jinjaenv():
    template_loader = DictLoader({})
    plain_text_jinja_id = f"{PLAIN_TEXT_TEMPLATE_ID}/{PLAIN_TEXT_TEMPLATE_ID}"
    template_loader.mapping[plain_text_jinja_id] = "{{ p.plain }}"

    png_template_jinja_id = f"{PNG_IMAGE_TEMPLATE_ID}/{PNG_IMAGE_TEMPLATE_ID}"
    template_loader.mapping[png_template_jinja_id] = \
        '<!DOCTYPE html>' \
        '<html>' \
        '<body>' \
        '<img id="img_" src="file://{{ template_static }}' \
        f'{PNG_IMAGE_NAME}">' \
        '</img>' \
        '</body>' \
        '</html>'

    no_image_template_jinja_id = f"{NO_IMAGE_TEMPLATE_ID}/{NO_IMAGE_TEMPLATE_ID}"
    template_loader.mapping[no_image_template_jinja_id] = \
        '<!DOCTYPE html>' \
        '<html>' \
        '<body>' \
        '<img id="img_" src="file://{{ template_static }}' \
        'no_img.png">' \
        '</img>' \
        '</body>' \
        '</html>'

    qr_code_template_jinja_id = f"{QR_CODE_TEMPLATE_ID}/{QR_CODE_TEMPLATE_ID}"
    template_loader.mapping[qr_code_template_jinja_id] = \
        '<!DOCTYPE html>' \
        '<html>' \
        '<body>' \
        '<img src="file://{{ p.qr_code }}" alt="qr_fail">' \
        '</body>' \
        '</html>'

    @asynccontextmanager
    async def mock_lifespan(app: FastAPI):
        app.dependency_overrides[get_db] = override_get_db
        with tempfile.TemporaryDirectory() as file_dir:
            app.state.file_storage = DiskFileStorage(file_dir)
            app.state.jinja_env = JinjaEnv(loader=template_loader,
                                           autoescape=select_autoescape(["html", "xml"]),
                                            auto_reload=True)
            current_folder = str(Path(__file__).resolve().parent)
            app.state.template_static_directory = f"{current_folder}/resources/static"
            yield
        app.dependency_overrides.clear()
    yield from fastapi_client(mock_lifespan)
    del template_loader.mapping[plain_text_jinja_id]
    del template_loader.mapping[png_template_jinja_id]
    del template_loader.mapping[no_image_template_jinja_id]
    del template_loader.mapping[qr_code_template_jinja_id]

@pytest.fixture(scope="class")
def template_test_examples(client_with_jinjaenv: TestClient, db: Session):
    plain_text_template_model = Template(id_=PLAIN_TEXT_TEMPLATE_ID,
                                         schema={"type": "object",
                                                 "properties": {"plain": {"type": "string"}}
                                                 },
                                         type_="text/html", metadata={},
                                         example_composition={"plain": "plain_example"}, tags=[])
    db.add(plain_text_template_model)

    png_image_template_model = Template(id_=PNG_IMAGE_TEMPLATE_ID,
                                        schema={"type": "object",
                                                "properties": {}
                                                },
                                        type_="text/html", metadata={}, example_composition={}, tags=[])
    db.add(png_image_template_model)

    no_image_template_model = Template(id_=NO_IMAGE_TEMPLATE_ID,
                                       schema={"type": "object",
                                               "properties": {}
                                               },
                                       type_="text/html", metadata={}, example_composition={}, tags=[])
    db.add(no_image_template_model)

    qr_code_template_model = Template(id_=QR_CODE_TEMPLATE_ID,
                                      schema={"type": "object",
                                              "properties": {}
                                              },
                                      type_="text/html", metadata={"qr_entries": ["qr_code"]},
                                      example_composition={}, tags=[])
    db.add(qr_code_template_model)
    db.commit()

    yield

    db.query(Template).delete()
    db.commit()



@pytest.mark.usefixtures("template_test_examples")
class TestCompose:
    COMPOSE_ENDPOINT = "/template/{0}/compose"
    EXAMPLE_COMPOSE_ENDPOINT = "/template/{0}/example"

    def test_compose_plain_ok(self, client_with_jinjaenv: TestClient):
        expected_text = "This is some plain text"
        json_request = {"plain": expected_text}
        response = client_with_jinjaenv.post(self.COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID), json=json_request)
        assert response.status_code == HTTPStatus.OK
        assert response.content is not None
        pdf_document = Document(filetype="bytes", stream=response.content)
        real_text = "".join((page.get_text() for page in pdf_document))
        assert real_text.strip() == expected_text


    def test_compose_image_exists(self, client_with_jinjaenv):
        def get_images_from_template(template_id: str):
            response = client_with_jinjaenv.post(self.COMPOSE_ENDPOINT.format(template_id), json={})
            assert response.content is not None
            assert response.status_code == HTTPStatus.OK
            pdf_document = Document(filetype="bytes", stream=response.content)
            blocks = chain.from_iterable((page.get_text("dict")["blocks"] for page in pdf_document))
            return [block["image"] for block in blocks]

        images = get_images_from_template(PNG_IMAGE_TEMPLATE_ID)
        assert len(images) == 1

        images = get_images_from_template(NO_IMAGE_TEMPLATE_ID)
        assert len(images) == 0

    def test_example_ok(self, client_with_jinjaenv, db: Session):
        test_template = db.query(Template).filter_by(id=PLAIN_TEXT_TEMPLATE_ID).one()
        expected_text = test_template.example_composition["plain"]

        response = client_with_jinjaenv.get(self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID))
        assert response.status_code == HTTPStatus.OK
        assert response.content is not None
        pdf_document = Document(filetype="bytes", stream=response.content)
        real_text = "".join((page.get_text() for page in pdf_document))
        assert real_text.strip() == expected_text

    def test_resize_ok(self, client_with_jinjaenv):
        error = 1
        expected_resize = 200

        response = client_with_jinjaenv.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}",
            headers={"accept": "image/png"}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.content is not None
        with Image.open(io.BytesIO(response.content)) as img:
            width, height = img.size
        expected_resolution = height / width
        assert height != expected_resize
        assert width != expected_resize

        response = client_with_jinjaenv.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}?width={expected_resize}",
            headers={"accept": "image/png"}
        )

        def maintains_aspect_ratio(response):
            assert response.status_code == HTTPStatus.OK
            assert response.content is not None
            with Image.open(io.BytesIO(response.content)) as img_:
                width_, height_ = img_.size
            real_resolution = height_ / width_
            assert isclose(expected_resolution, real_resolution, abs_tol=error / 10)
            return width_, height_

        real_width, _ = maintains_aspect_ratio(response)
        assert isclose(expected_resize, real_width, abs_tol=error)
        response = client_with_jinjaenv.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}?height={expected_resize}",
            headers={"accept": "image/png"}
        )
        _, real_height = maintains_aspect_ratio(response)
        assert isclose(expected_resize, real_height, abs_tol=error)

    def test_resize_nok(self, client_with_jinjaenv):
        intended_resize = 200

        response = client_with_jinjaenv.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}"
            f"?width={intended_resize}&height={intended_resize}",
            headers={"accept": "image/png"}
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert get_message(response) == aspect_ratio_compromised

        pdf_mimetype = "application/pdf"

        response = client_with_jinjaenv.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}"
            f"?width={intended_resize}",
            headers={"accept": pdf_mimetype}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert get_message(response) == resizing_unsupported.format(pdf_mimetype)

    def test_unsupported_mimetype(self, client_with_jinjaenv):
        jpeg_mimetype = "image/jpeg"

        response = client_with_jinjaenv.get(
            f"{self.EXAMPLE_COMPOSE_ENDPOINT.format(PLAIN_TEXT_TEMPLATE_ID)}",
            headers={"accept": jpeg_mimetype}
        )

        assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
        assert get_message(response) == unsupported_mime_type.format(jpeg_mimetype, ", ".join(ALL_AVAILABLE_MIME_TYPES))

    def test_compose_qr_code_exists(self, client_with_jinjaenv):
        response = client_with_jinjaenv.post(self.COMPOSE_ENDPOINT.format(QR_CODE_TEMPLATE_ID), json={"qr_code": "qr_url.com"})
        assert response.content is not None
        assert response.status_code == HTTPStatus.OK

        pdf_document = Document(filetype="bytes", stream=response.content)
        blocks = chain.from_iterable((page.get_text("dict")["blocks"] for page in pdf_document))
        images = [block["image"] for block in blocks]
        assert len(images) == 1



