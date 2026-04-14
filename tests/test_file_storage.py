import pathlib
from tempfile import TemporaryDirectory

from unittest import mock
from unittest.mock import call, MagicMock

import pytest
from app.file_storage import S3FileStorage, NoIndexTemplateFound
from app.models import Template
from google.cloud.storage import Blob
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

BASE_DIR = 'templating'

def get_local_static_file_path(template_id: str, file_name: str):
    return f"static/{template_id}/{file_name}"

def get_local_template_file_path(template_id: str):
    return f"templates/{template_id}/{template_id}"

def create_child_temp_folder(main_directory: str) -> str:
    template_dir_name = f"{main_directory}/abc"
    pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
    return template_dir_name

@pytest.fixture(scope="function")
def populate_db(fastapi_client_s3_storage, db: Session):
    template = Template(id_="0", schema={},
                        type_="text/html", tags=['test_tags'], metadata={},
                        example_composition={'place_holder': 'value'})
    db.add(template)
    db.commit()

    yield

    db.query(Template).delete()
    db.commit()

class TestFileStorage:
    def test_file_storage_write_files(self, fastapi_client_local_storage: TestClient):
        files = {"templating/templates/0/0": b"file content",
                 "templating/static/0/abc_1": b"static content",
                 "templating/static/0/abc_2": b"static content"}

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            file_storage = fastapi_client_local_storage.app.state.file_storage
            file_storage.write_files(files, template_dir)

            static_file_1 = f'{template_dir}/templating/{get_local_static_file_path(file_name="abc_1", template_id="0")}'
            static_file_2 = f'{template_dir}/templating/{get_local_static_file_path(file_name="abc_2", template_id="0")}'
            template_file_1 = f'{template_dir}/templating/{get_local_template_file_path(template_id="0")}'

            assert pathlib.Path(static_file_1).is_file()
            assert pathlib.Path(static_file_2).is_file()
            assert pathlib.Path(template_file_1).is_file()

    @pytest.mark.usefixtures("populate_db")
    @mock.patch.object(S3FileStorage, "get_file")
    def test_file_storage_load_templates(self, mock_s3_get_file, fastapi_client_s3_storage: TestClient, db: Session):
        mock_s3_get_file.side_effect = [{"templating/static/0/abc_1": b"static content",
                                         "templating/static/0/abc_2": b"static content"},
                                        {"templating/templates/0/0": b"file content"}]

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            s3_file_storage = fastapi_client_s3_storage.app.state.file_storage
            s3_file_storage.load_templates(template_dir, BASE_DIR, db)

            static_file_1 = f'{template_dir}/templating/{get_local_static_file_path(file_name="abc_1", template_id="0")}'
            static_file_2 = f'{template_dir}/templating/{get_local_static_file_path(file_name="abc_2", template_id="0")}'
            template_file_1 = f'{template_dir}/templating/{get_local_template_file_path(template_id="0")}'

            assert pathlib.Path(static_file_1).is_file()
            assert pathlib.Path(static_file_2).is_file()
            assert pathlib.Path(template_file_1).is_file()

        calls = [call(path=f"{BASE_DIR}/static", template_directory=BASE_DIR),
                 call(path=f"{BASE_DIR}/templates/0/0", template_directory=BASE_DIR)]
        mock_s3_get_file.assert_has_calls(calls, any_order=True)
        # when debugging, the mocked iterator calls __len__() for some reason. this is why any_order is set to True
        # to, at least, guarantee that the calls we want actually are present in mock_iter_bucket.mock_calls

    @pytest.mark.usefixtures("populate_db")
    @mock.patch.object(S3FileStorage, "get_file")
    def test_file_storage_load_templates_no_template_file_found(self, mock_s3_get_file,
                                                                fastapi_client_s3_storage: TestClient, db: Session):
        mock_s3_get_file.side_effect = [{"templating/static/0/abc_1": b"static content",
                                         "templating/static/0/abc_2": b"static content"},
                                        {}]

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            s3_file_storage = fastapi_client_s3_storage.app.state.file_storage
            with pytest.raises(NoIndexTemplateFound):
                s3_file_storage.load_templates(template_dir, BASE_DIR, db)

            static_file_1 = f'{template_dir}/templating/{get_local_static_file_path(file_name="abc_1", template_id="0")}'
            static_file_2 = f'{template_dir}/templating/{get_local_static_file_path(file_name="abc_2", template_id="0")}'
            template_file_1 = f'{template_dir}/templating/{get_local_template_file_path(template_id="0")}'

            assert pathlib.Path(static_file_1).is_file()
            assert pathlib.Path(static_file_2).is_file()
            assert not pathlib.Path(template_file_1).is_file()

        calls = [call(path=f"{BASE_DIR}/static", template_directory=BASE_DIR),
                 call(path=f"{BASE_DIR}/templates/0/0", template_directory=BASE_DIR)]
        mock_s3_get_file.assert_has_calls(calls, any_order=True)
        # when debugging, the mocked iterator calls __len__() for some reason. this is why any_order is set to True
        # to, at least, guarantee that the calls we want actually are present in mock_iter_bucket.mock_calls

    @mock.patch('app.file_storage.s3.iter_bucket')
    def test_file_storage_get_file_s3(self, mock_iter_bucket, fastapi_client_s3_storage: TestClient):
        mock_iter_bucket.side_effect = [
            [('templating/static/0/abc_1', b'static content'), ('templating/static/0/abc_2', b'static content'),],
            [('templating/templates/0/0', b'file content'),]
        ]

        s3_file_storage = fastapi_client_s3_storage.app.state.file_storage
        static_files_dict = s3_file_storage.get_file(f"{BASE_DIR}/static", BASE_DIR)
        assert static_files_dict == {"/static/0/abc_1": b"static content",
                                     "/static/0/abc_2": b"static content"}

        template_files_dict = s3_file_storage.get_file(f"{BASE_DIR}/templates", BASE_DIR)
        assert template_files_dict == {"/templates/0/0": b'file content'}

        calls = [call(bucket_name="test_template_bucket", prefix=f"{BASE_DIR}/static", **s3_file_storage.aws_credentials_dict),
                 call(bucket_name="test_template_bucket", prefix=f"{BASE_DIR}/templates", **s3_file_storage.aws_credentials_dict)]
        mock_iter_bucket.assert_has_calls(calls, any_order=True)
        # when debugging, the mocked iterator calls __len__() for some reason. this is why any_order is set to True
        # to, at least, guarantee that the calls we want actually are present in mock_iter_bucket.mock_calls

    @mock.patch("app.file_storage.S3FileStorage.get_aws_credentials")
    def test_get_aws_credentials(self, mock_get_aws_credentials, fastapi_client_s3_storage: TestClient):
        mock_get_aws_credentials.return_value = {"aws_access_key_id": "test_aws_key_unit_test",
                                                 "aws_secret_access_key": "test_secret_key_unit_test",
                                                 "region_name": "test_region_unit_test"}
        s3_file_storage = fastapi_client_s3_storage.app.state.file_storage
        assert s3_file_storage.get_aws_credentials(f"path_to_aws_credentials/") == mock_get_aws_credentials.return_value


    def test_file_storage_get_file_gcs(self, fastapi_client_gcs_storage: TestClient):
        gcs_file_storage = fastapi_client_gcs_storage.app.state.file_storage
        template_blob = MagicMock(Blob)
        static_blob_1 = MagicMock(Blob)
        static_blob_2 = MagicMock(Blob)

        template_blob.name, static_blob_1.name, static_blob_2.name = ["templating/templates/0/0", "templating/static/0/abc_1", "templating/static/0/abc_2"]
        template_blob.download_as_bytes.return_value = b'file content'
        static_blob_1.download_as_bytes.return_value = b'static content'
        static_blob_2.download_as_bytes.return_value = b'static content'

        bucket = fastapi_client_gcs_storage.app.state.mocked_bucket
        bucket.list_blobs.side_effect = [[static_blob_1, static_blob_2], [template_blob]]

        static_files_dict = gcs_file_storage.get_file(f"{BASE_DIR}/static", BASE_DIR)
        assert static_files_dict == {"/static/0/abc_1": b"static content",
                                     "/static/0/abc_2": b"static content"}

        template_files_dict = gcs_file_storage.get_file(f"{BASE_DIR}/templates", BASE_DIR)
        assert template_files_dict == {"/templates/0/0": b'file content'}

        calls = [call(prefix=f"{BASE_DIR}/static"),
                 call(prefix=f"{BASE_DIR}/templates")]
        bucket.list_blobs.assert_has_calls(calls)

