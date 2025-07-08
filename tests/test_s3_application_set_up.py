from tempfile import TemporaryDirectory
import pytest
import boto3
import pathlib
from smart_open import s3
from moto import mock_s3
from sqlalchemy.orm import Session

from app.db.models.template import Template
from app.file_storage import NoIndexTemplateFound


BUCKET_NAME = 'test_template_bucket'
BASE_DIR = 'templating'


def get_static_file_path(template_id: str, file_name: str):
    return f"{BASE_DIR}/static/{template_id}/{file_name}"

def get_template_file_path(template_id: str):
    return f"{BASE_DIR}/templates/{template_id}/{template_id}"


def get_local_static_file_path(template_id: str, file_name: str):
    return f"static/{template_id}/{file_name}"

def get_local_template_file_path(template_id: str):
    return f"templates/{template_id}/{template_id}"


def create_child_temp_folder(main_directory: str) -> str:
    template_dir_name = f"{main_directory}/abc"
    pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
    return template_dir_name

def write_to_s3(bucket_name: str, file_paths: list):
    encoding = "utf-8"
    for file_path in file_paths:
        with s3.open(bucket_name, key_id=file_path, mode="wb") as file:
            file.write("I am file !".encode(encoding))


@pytest.fixture(scope="class")
def populate_db(fastapi_client_s3_storage, db: Session):
    template = Template(id_="0", schema={},
                        type_="text/html", tags=['test_tags'], metadata={},
                        example_composition={'place_holder': 'value'})
    db.add(template)
    db.commit()

    yield

    db.query(Template).delete()
    db.commit()

def create_s3_bucket() -> None:
    conn = boto3.resource('s3', region_name='eu-central-1')
    conn.create_bucket(Bucket=BUCKET_NAME)

@pytest.fixture(scope="function")
@mock_s3
def populate_s3() -> None:
    create_s3_bucket()

    static_file_1 = get_static_file_path(file_name="abc_1", template_id="0")
    static_file_2 = get_static_file_path(file_name="abc_2", template_id="0")
    write_to_s3(bucket_name=BUCKET_NAME, file_paths=[static_file_1, static_file_2])

    template_file_1 = get_template_file_path(template_id="0")
    write_to_s3(bucket_name=BUCKET_NAME, file_paths=[template_file_1])

@pytest.fixture(scope='function')
@mock_s3
def populate_s3_with_missing_template_file() -> None:
    create_s3_bucket()

    static_file = get_static_file_path(file_name="abc", template_id="0")
    write_to_s3(bucket_name=BUCKET_NAME, file_paths=[static_file])

@pytest.mark.usefixtures("populate_db")
class TestS3ApplicationSetup:
    def test_success_case(self, fastapi_client_s3_storage, populate_s3):
        with fastapi_client_s3_storage.application.test_request_context():
            with TemporaryDirectory() as temp:
                # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
                template_dir_name = create_child_temp_folder(temp)
                file_storage = fastapi_client_s3_storage.application.config["storage"]
                file_storage.load_templates(template_dir_name, BASE_DIR)

                static_file_1 = f'{template_dir_name}/{get_local_static_file_path(file_name="abc_1", template_id="0")}'
                static_file_2 = f'{template_dir_name}/{get_local_static_file_path(file_name="abc_2", template_id="0")}'
                template_file_1 = f'{template_dir_name}/{get_local_template_file_path(template_id="0")}'

                assert pathlib.Path(static_file_1).is_file()
                assert pathlib.Path(static_file_2).is_file()
                assert pathlib.Path(template_file_1).is_file()

    def test_missing_template_file(self, client_s3_storage, populate_s3_with_missing_template_file):
        with client_s3_storage.application.test_request_context():
            with pytest.raises(NoIndexTemplateFound):
                with TemporaryDirectory() as temp:
                    # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
                    template_dir_name = create_child_temp_folder(temp)
                    file_storage = client_s3_storage.application.config["storage"]
                    file_storage.load_templates(template_dir_name, BASE_DIR)

# -*- coding: utf-8 -*-
# import boto3
# import pytest
# import pathlib
# from moto import mock_s3
# from smart_open import s3
# from sqlalchemy.orm import Session
#
# from app.file_storage import NoIndexTemplateFound
# from tempfile import TemporaryDirectory
# from app.db.models.template import Template
#
# BUCKET_NAME = 'test_template_bucket'
# BASE_DIR = 'templating'
#

# def get_template_file_path(template_id: str):
#     return f"{BASE_DIR}/templates/{template_id}/{template_id}"
#
#
# def get_local_template_file_path(template_id: str):
#     return f"templates/{template_id}/{template_id}"
#
#
# def get_static_file_path(template_id: str, file_name: str):
#     return f"{BASE_DIR}/static/{template_id}/{file_name}"
#
#
# def get_local_static_file_path(template_id: str, file_name: str):
#     return f"static/{template_id}/{file_name}"
#
#
# def create_child_temp_folder(main_directory: str) -> str:
#     template_dir_name = f"{main_directory}/abc"
#     pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
#     return template_dir_name
#
#
# def write_to_s3(bucket_name: str, file_paths: list):
#     encoding = "utf-8"
#     for file_path in file_paths:
#         with s3.open(bucket_name, key_id=file_path, mode="wb") as file:
#             file.write("I am file !".encode(encoding))
#
#
# def create_s3_bucket() -> None:
#     conn = boto3.resource('s3', region_name='eu-central-1')
#     conn.create_bucket(Bucket=BUCKET_NAME)
#
#
# @pytest.fixture(scope="class")
# def populate_db(client_s3_storage, db: Session):
#     with client_s3_storage.application.test_request_context():
#         template = Template(id_="0", schema={},
#                             type_="text/html", tags=['test_tags'], metadata={},
#                             example_composition={'place_holder': 'value'})
#         db.add(template)
#         db.commit()
#
#     yield
#
#     with client_s3_storage.application.test_request_context():
#         db.delete(Template)
#         db.commit()
#
#
# @pytest.fixture(scope='function')
# @mock_s3
# def populate_s3() -> None:
#     create_s3_bucket()
#
#     static_file_1 = get_static_file_path(file_name="abc_1", template_id="0")
#     static_file_2 = get_static_file_path(file_name="abc_2", template_id="0")
#     write_to_s3(bucket_name=BUCKET_NAME, file_paths=[static_file_1, static_file_2])
#
#     template_file_1 = get_template_file_path(template_id="0")
#     write_to_s3(bucket_name=BUCKET_NAME, file_paths=[template_file_1])
#
#
# @pytest.fixture(scope='function')
# @mock_s3
# def populate_s3_with_missing_template_file() -> None:
#     create_s3_bucket()
#
#     static_file = get_static_file_path(file_name="abc", template_id="0")
#     write_to_s3(bucket_name=BUCKET_NAME, file_paths=[static_file])
#
#
# @pytest.mark.usefixtures("populate_db")
# @mock_s3
# class TestS3ApplicationSetup:
#     def test_success_case(self, client_s3_storage, populate_s3):
#         with client_s3_storage.application.test_request_context():
#             with TemporaryDirectory() as temp:
#                 # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
#                 template_dir_name = create_child_temp_folder(temp)
#                 file_storage = client_s3_storage.application.config["storage"]
#                 file_storage.load_templates(template_dir_name, BASE_DIR)
#
#                 static_file_1 = f'{template_dir_name}/{get_local_static_file_path(file_name="abc_1", template_id="0")}'
#                 static_file_2 = f'{template_dir_name}/{get_local_static_file_path(file_name="abc_2", template_id="0")}'
#                 template_file_1 = f'{template_dir_name}/{get_local_template_file_path(template_id="0")}'
#
#                 assert pathlib.Path(static_file_1).is_file()
#                 assert pathlib.Path(static_file_2).is_file()
#                 assert pathlib.Path(template_file_1).is_file()
#
#     def test_missing_template_file(self, client_s3_storage, populate_s3_with_missing_template_file):
#         with client_s3_storage.application.test_request_context():
#             with pytest.raises(NoIndexTemplateFound):
#                 with TemporaryDirectory() as temp:
#                     # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
#                     template_dir_name = create_child_temp_folder(temp)
#                     file_storage = client_s3_storage.application.config["storage"]
#                     file_storage.load_templates(template_dir_name, BASE_DIR)
