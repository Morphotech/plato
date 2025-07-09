import pytest
from sqlalchemy.orm import Session
import boto3
from moto import mock_aws
from pathlib import Path
from fastapi.testclient import TestClient
from http import HTTPStatus
import json

from app.db.models.template import Template
from tests.test_s3_application_set_up import BUCKET_NAME

TEMPLATE_ID = "template_test_1"
CURRENT_TEST_PATH = str(Path(__file__).resolve().parent)

TEMPLATE_DETAILS_1 = {"title": TEMPLATE_ID,
                      "schema": {
                          "type": "object",
                          "required": [
                              "cert_name",
                              "serial_number"
                          ],
                          "properties": {
                              "qr_code": {
                                  "type": "string"
                              },
                              "cert_name": {
                                  "type": "string"
                              },
                              "serial_number": {
                                  "type": "string"
                              }
                          }
                      },
                      "type": "text/html",
                      "metadata": {
                          "qr_entries": [
                              "qr_code"
                          ]
                      },
                      "example_composition": {
                          "qr_code": "https://vizidox.com",
                          "cert_date": "2020-01-12",
                          "cert_name": "Alan Turing",
                          "serial_number": "C18009"
                      },
                      "tags": [
                      ]}

TEMPLATE_DETAILS_1_UPDATE = {
    "schema": {
        "type": "object",
        "required": [
            "cert_name",
            "serial_number"
        ],
        "properties": {
            "qr_code": {
                "type": "string"
            },
            "cert_name": {
                "type": "string"
            },
            "serial_number": {
                "type": "string"
            }
        }
    },
    "type": "text/html",
    "metadata": {
        "qr_entries": [
            "qr_code"
        ]
    },
    "example_composition": {
        "qr_code": "https://vizidox.com",
        "cert_date": "2022-01-12",
        "cert_name": "Ada Lovelace",
        "serial_number": "D8999"
    },
    "tags": [
    ]}

TEMPLATE_DETAILS_2 = {"title": "template_test_2",
                      "schema": {
                          "type": "object",
                          "required": [
                              "cert_name",
                              "serial_number"
                          ],
                          "properties": {
                              "qr_code": {
                                  "type": "string"
                              },
                              "cert_name": {
                                  "type": "string"
                              },
                              "serial_number": {
                                  "type": "string"
                              }
                          }
                      },
                      "type": "text/html",
                      "metadata": {
                          "qr_entries": [
                              "qr_code"
                          ]
                      },
                      "example_composition": {
                          "qr_code": "https://vizidox.com",
                          "cert_date": "2020-01-12",
                          "cert_name": "Alan Turing",
                          "serial_number": "C18009"
                      },
                      "tags": [
                      ]}

TEMPLATE_DETAILS_2_UPDATE = {
    "schema": {
        "type": "object",
        "required": [
            "cert_name",
            "serial_number"
        ],
        "properties": {
            "qr_code": {
                "type": "string"
            },
            "cert_name": {
                "type": "string"
            },
            "serial_number": {
                "type": "string"
            }
        }
    },
    "type": "text/html",
    "metadata": {
        "qr_entries": [
            "qr_code"
        ]
    },
    "example_composition": {
        "qr_code": "https://vizidox.com",
        "cert_date": "2020-01-12",
        "cert_name": "Alan Turing",
        "serial_number": "C18009"
    },
    "tags": [
    ]}


@pytest.fixture(scope="function")
def populate_db_s3(fastapi_client_s3_storage, db: Session):
    yield from _fleeting_database(fastapi_client_s3_storage, db)


@pytest.fixture(scope="function")
def populate_db(fastapi_client_local_storage, db: Session):
    yield from _fleeting_database(fastapi_client_local_storage, db)


def _fleeting_database(client: TestClient, db: Session):
    t = Template(id_=TEMPLATE_ID,
                 schema={
                     "type": "object",
                     "required": [
                         "cert_name",
                         "serial_number"
                     ],
                     "properties": {
                         "qr_code": {
                             "type": "string"
                         },
                         "cert_name": {
                             "type": "string"
                         },
                         "serial_number": {
                             "type": "string"
                         }
                     }
                 },
                 type_="text/html", metadata={}, example_composition={}, tags=[])
    db.add(t)
    db.commit()

    yield

    db.query(Template).delete()
    db.commit()


@pytest.fixture(scope="class")
def setup_s3():
    with mock_aws():
        conn = boto3.resource('s3')
        conn.create_bucket(Bucket=BUCKET_NAME)
        yield

@pytest.mark.usefixtures("populate_db")
class TestManageTemplates:
    CREATE_TEMPLATE_ENDPOINT = '/template/create'
    UPDATE_TEMPLATE = '/template/{0}/update'
    UPDATE_TEMPLATE_DETAILS = '/template/{0}/update_details'


    def test_create_new_template_invalid_zip_file(self, fastapi_client_local_storage: TestClient):
        with open(f'{CURRENT_TEST_PATH}/resources/invalid_file.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS_2)
            data: dict = {'template_details': template_details_str}
            result = fastapi_client_local_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data, 
                                                       files={ "zipfile": ('invalid_file.zip', file, 'application/zip') } if file is not None else None)
            assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_create_new_template_already_exists(self, fastapi_client_local_storage: TestClient):
        with open(f'{CURRENT_TEST_PATH}/resources/{TEMPLATE_ID}.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS_1)
            data: dict = {'template_details': template_details_str}
            result = fastapi_client_local_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data,
                                                       files={"zipfile": (f'{TEMPLATE_ID}.zip', file, 'application/zip')} if file is not None else None)
            assert result.status_code == HTTPStatus.CONFLICT


    def test_create_new_template_invalid_file_type(self, fastapi_client_local_storage: TestClient):
        filename = 'example.pdf'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_2)
        data: dict = {'template_details': template_details_str}
        result = fastapi_client_local_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data,
                                           files={"zipfile": (filename, file, 'application/zip')} if file is not None else None)
        assert result.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    def test_create_new_template_ok(self, fastapi_client_local_storage: TestClient, db: Session):
        with open(f'{CURRENT_TEST_PATH}/resources/template_test_2.zip', 'rb') as file:
            template_id = "template_test_2"
            template_details_str = json.dumps(TEMPLATE_DETAILS_2)
            data: dict = {'template_details': template_details_str}
            filename = f'{template_id}.zip'
            result = fastapi_client_local_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data,
                                                       files={"zipfile": (filename, file, 'application/zip')} if file is not None else None)
            assert result.status_code == HTTPStatus.CREATED
            template_model: Template = db.query(Template).filter_by(id=template_id).one()
            assert template_model is not None

            expected_template = Template.from_json_dict(TEMPLATE_DETAILS_2)
            assert template_model.schema == expected_template.schema

    def test_update_template_invalid_zip_file(self, fastapi_client_local_storage: TestClient):
        with open(f'{CURRENT_TEST_PATH}/resources/invalid_file.zip', 'rb') as file:
            template_details_str = json.dumps(TEMPLATE_DETAILS_2_UPDATE)
            data: dict = {'template_details': template_details_str}

            result = fastapi_client_local_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data,
                                                      files={"zipfile": ("invalid_file.zip", file, 'application/zip')} if file is not None else None)
            assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_update_template_invalid_details(self, fastapi_client_local_storage: TestClient):
        with open(f'{CURRENT_TEST_PATH}/resources/{TEMPLATE_ID}.zip', 'rb') as file:
            template_details_str = json.dumps({"user": "Carlos Coda"})
            data: dict = {'template_details': template_details_str}

            result = fastapi_client_local_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data,
                                                      files={"zipfile": ("template_test_1.zip", file, 'application/zip')} if file is not None else None)
            assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_update_template_invalid_file_type(self, fastapi_client_local_storage: TestClient):
        filename = 'example.pdf'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_2)
        data: dict = {'template_details': template_details_str}

        result = fastapi_client_local_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data,
                                          files={"zipfile": (filename, file, 'application/zip')} if file is not None else None)
        assert result.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    def test_update_template_not_found(self, fastapi_client_local_storage: TestClient):
        template_id = "template_test_2"
        filename = 'template_test_2.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_2)
        data: dict = {'template_details': template_details_str}

        result = fastapi_client_local_storage.put(self.UPDATE_TEMPLATE.format(template_id), data=data,
                                          files={"zipfile": (filename, file, 'application/zip')} if file is not None else None)
        assert result.status_code == HTTPStatus.NOT_FOUND

    def test_update_template_ok(self, fastapi_client_local_storage: TestClient, db: Session):
        filename = 'template_test_1.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_1_UPDATE)
        data: dict = {'template_details': template_details_str}
        result = fastapi_client_local_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data,
                                          files={"zipfile": (filename, file, 'application/zip')} if file is not None else None)
        assert result.status_code == HTTPStatus.OK
        template_model: Template = db.query(Template).filter_by(id=TEMPLATE_ID).one()
        assert template_model.example_composition is not None
        expected_example_composition = {
            "qr_code": "https://vizidox.com",
            "cert_date": "2022-01-12",
            "cert_name": "Ada Lovelace",
            "serial_number": "D8999"
        }
        assert template_model.example_composition == expected_example_composition
        expected_template = Template.from_json_dict(TEMPLATE_DETAILS_1)
        assert template_model.schema == expected_template.schema

    def test_update_template_details_not_found(self, fastapi_client_local_storage: TestClient):
        template_id = "template_test_3"
        data: dict = {'template_details': {"tags": ["test"]}}

        result = fastapi_client_local_storage.patch(self.UPDATE_TEMPLATE_DETAILS.format(template_id), json=data)
        assert result.status_code == HTTPStatus.NOT_FOUND

    def test_update_template_details_invalid(self, fastapi_client_local_storage: TestClient):
        data: dict = {"user": "invalid"}

        result = fastapi_client_local_storage.patch(self.UPDATE_TEMPLATE_DETAILS.format(TEMPLATE_ID), json=data)
        assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_update_template_details_ok(self, fastapi_client_local_storage: TestClient, db: Session):
        example_composition_data = {"qr_code": "https://google.com",
                                    "cert_date": "2021-01-12",
                                    "cert_name": "Albert Einstein",
                                    "serial_number": "C9999"}

        data: dict = {"example_composition": example_composition_data}

        result = fastapi_client_local_storage.patch(self.UPDATE_TEMPLATE_DETAILS.format(TEMPLATE_ID), json=data)
        assert result.status_code == HTTPStatus.OK
        template_model: Template = db.query(Template).filter_by(id=TEMPLATE_ID).one()
        assert template_model.example_composition is not None
        assert template_model.example_composition == example_composition_data


@pytest.mark.usefixtures("populate_db_s3")
@pytest.mark.usefixtures("setup_s3")
class TestManageTemplatesS3FileStorage:
    CREATE_TEMPLATE_ENDPOINT = '/template/create'
    UPDATE_TEMPLATE = '/template/{0}/update'
    UPDATE_TEMPLATE_DETAILS = '/template/{0}/update_details'

    def test_create_new_template_ok(self, fastapi_client_s3_storage: TestClient, db: Session):
        with open(f'{CURRENT_TEST_PATH}/resources/template_test_2.zip', 'rb') as file:
            template_id = "template_test_2"
            template_details_str = json.dumps(TEMPLATE_DETAILS_2)
            data: dict = {'template_details': template_details_str}
            filename = f'{template_id}.zip'

            result = fastapi_client_s3_storage.post(self.CREATE_TEMPLATE_ENDPOINT, data=data,
                                            files={"zipfile": (filename, file, 'application/zip')} if file is not None else None)
            assert result.status_code == HTTPStatus.CREATED
            template_model: Template = db.query(Template).filter_by(id=template_id).one()
            assert template_model is not None

            expected_template = Template.from_json_dict(TEMPLATE_DETAILS_2)
            assert template_model.schema == expected_template.schema

    def test_update_template_ok(self, fastapi_client_s3_storage: TestClient, db: Session):
        filename = 'template_test_1.zip'
        file = open(f'{CURRENT_TEST_PATH}/resources/{filename}', "rb")
        template_details_str = json.dumps(TEMPLATE_DETAILS_1_UPDATE)
        data: dict = {'template_details': template_details_str}
        result = fastapi_client_s3_storage.put(self.UPDATE_TEMPLATE.format(TEMPLATE_ID), data=data,
                                               files={"zipfile": (filename, file, 'application/zip')} if file is not None else None)
        assert result.status_code == HTTPStatus.OK
        template_model: Template = db.query(Template).filter_by(id=TEMPLATE_ID).one()
        assert template_model.example_composition is not None
        expected_example_composition = {
            "qr_code": "https://vizidox.com",
            "cert_date": "2022-01-12",
            "cert_name": "Ada Lovelace",
            "serial_number": "D8999"
        }
        assert template_model.example_composition == expected_example_composition
        expected_template = Template.from_json_dict(TEMPLATE_DETAILS_1)
        assert template_model.schema == expected_template.schema

    def test_update_template_details_ok(self, fastapi_client_s3_storage: TestClient, db: Session):
        example_composition_data = {"qr_code": "https://google.com",
                                    "cert_date": "2021-01-12",
                                    "cert_name": "Albert Einstein",
                                    "serial_number": "C9999"}

        data: dict = {"example_composition": example_composition_data}

        result = fastapi_client_s3_storage.patch(self.UPDATE_TEMPLATE_DETAILS.format(TEMPLATE_ID), json=data)
        assert result.status_code == HTTPStatus.OK
        template_model: Template = db.query(Template).filter_by(id=TEMPLATE_ID).one()
        assert template_model.example_composition is not None
        assert template_model.example_composition == example_composition_data


