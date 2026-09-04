import json
import pathlib
from tempfile import TemporaryDirectory

from unittest import mock
from unittest.mock import call, MagicMock, mock_open

import pytest
from app.file_storage import DiskFileStorage, S3FileStorage, GCSFileStorage, NoIndexTemplateFound, FileStorageError
from app.models import Template
from app.settings import get_settings
from google.cloud import storage
from google.cloud.storage import Blob, Client
from sqlalchemy.orm import Session

BASE_DIR = 'templating'

def get_local_static_file_path(template_id: str, file_name: str):
    return f"{template_id}/static/{file_name}"

def get_local_template_file_path(template_id: str):
    return f"{template_id}/{template_id}.html"

def create_child_temp_folder(main_directory: str) -> str:
    template_dir_name = f"{main_directory}/abc"
    pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
    return template_dir_name

@pytest.fixture
def s3_file_storage():
    with (TemporaryDirectory() as file_dir,
          mock.patch("app.file_storage.S3FileStorage.get_aws_credentials") as mock_get_aws_credentials):
        mock_get_aws_credentials.return_value = {"aws_access_key_id": "test_aws_key",
                                                 "aws_secret_access_key": "test_secret_key",
                                                 "region_name": "test_region"}
        yield S3FileStorage(file_dir, get_settings().BUCKET_NAME)

@pytest.fixture
def gcs_file_storage():
    with (TemporaryDirectory() as file_dir,
          mock.patch.object(Client, "from_service_account_json") as mock_init_client):
        gcs_client = MagicMock(spec=Client)
        bucket = MagicMock(spec=storage.Bucket)
        gcs_client.bucket.return_value = bucket
        mock_init_client.return_value = gcs_client
        yield GCSFileStorage(file_dir, get_settings().BUCKET_NAME), bucket

@pytest.fixture(scope="function")
def populate_db(db: Session):
    template = Template(id_="0", schema={},
                        type_="text/html", tags=['test_tags'], metadata={},
                        example_composition={'place_holder': 'value'})
    db.add(template)
    db.commit()

    yield

    db.query(Template).delete()
    db.commit()

class TestFileStorage:
    def test_file_storage_write_files(self):
        files = {"templating/0/0.html": b"file content",
                 "templating/0/static/abc_1": b"static content",
                 "templating/0/static/abc_2": b"static content"}

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            DiskFileStorage.write_files(files, template_dir)

            static_file_1 = f'{template_dir}/templating/{get_local_static_file_path(file_name="abc_1", template_id="0")}'
            static_file_2 = f'{template_dir}/templating/{get_local_static_file_path(file_name="abc_2", template_id="0")}'
            template_file_1 = f'{template_dir}/templating/{get_local_template_file_path(template_id="0")}'

            assert pathlib.Path(static_file_1).is_file()
            assert pathlib.Path(static_file_2).is_file()
            assert pathlib.Path(template_file_1).is_file()

    def test_get_aws_credentials(self):
        mock_aws_credentials_data = """\
            {"aws_access_key_id": "test_aws_key_unit_test",
             "aws_secret_access_key": "test_secret_key_unit_test",
             "region_name": "test_region_unit_test"}
             """
        mock_aws_open = mock_open(read_data=mock_aws_credentials_data)

        with mock.patch("builtins.open", mock_aws_open):
            result = S3FileStorage.get_aws_credentials(f"path_to_aws_credentials/aws_credentials.json")

        assert result == {"aws_access_key_id": "test_aws_key_unit_test",
                          "aws_secret_access_key": "test_secret_key_unit_test",
                          "region_name": "test_region_unit_test"}

    def test_get_aws_credentials_no_file_found(self):
        with pytest.raises(FileStorageError):
            S3FileStorage.get_aws_credentials(f"path_to_aws_credentials/aws_credentials.json")

    def test_get_aws_credentials_invalid_json_error(self):
        mock_aws_credentials_data = """\
            {"aws_access_key_id": "test_aws_key_unit_test",
             "aws_secret_access_key": "test_secret_key_unit_test",
             "region_name": "test_region_unit_test",
             invalid_key: invalid_value}
             """
        mock_aws_open = mock_open(read_data=mock_aws_credentials_data)

        with pytest.raises(FileStorageError):
            with mock.patch("builtins.open", mock_aws_open):
                S3FileStorage.get_aws_credentials(f"path_to_aws_credentials/aws_credentials.json")

    def test_get_gcs_client(self):
        fake_client = MagicMock(spec=Client)

        with mock.patch.object(Client, "from_service_account_json", return_value=fake_client) as mock_init_client:
            result = GCSFileStorage.get_gcs_client("path_to_gcs_credentials/service_account_key.json")

        mock_init_client.assert_called_once_with("path_to_gcs_credentials/service_account_key.json")
        assert result is fake_client

    def test_get_gcs_client_no_file_found(self):
        with mock.patch.object(Client, "from_service_account_json", side_effect=FileNotFoundError):
            with pytest.raises(FileStorageError):
                GCSFileStorage.get_gcs_client("path_to_gcs_credentials/service_account_key.json")

    def test_get_gcs_client_invalid_json_error(self):
        with mock.patch.object(Client, "from_service_account_json",
                              side_effect=json.JSONDecodeError("Expecting value", "", 0)):
            with pytest.raises(FileStorageError):
                GCSFileStorage.get_gcs_client("path_to_gcs_credentials/service_account_key.json")

    @pytest.mark.usefixtures("populate_db")
    @mock.patch.object(S3FileStorage, "get_file")
    def test_file_storage_load_templates(self, mock_s3_get_file, s3_file_storage: S3FileStorage, db: Session):
        mock_s3_get_file.return_value = {"/0/0.html": b"file content",
                                         "/0/static/abc_1": b"static content",
                                         "/0/static/abc_2": b"static content"}

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            s3_file_storage.load_templates(template_dir, BASE_DIR, db)

            static_file_1 = f'{template_dir}/{get_local_static_file_path(file_name="abc_1", template_id="0")}'
            static_file_2 = f'{template_dir}/{get_local_static_file_path(file_name="abc_2", template_id="0")}'
            template_file_1 = f'{template_dir}/{get_local_template_file_path(template_id="0")}'

            assert pathlib.Path(static_file_1).is_file()
            assert pathlib.Path(static_file_2).is_file()
            assert pathlib.Path(template_file_1).is_file()

        mock_s3_get_file.assert_called_once_with(path=f"{BASE_DIR}/0", template_directory=BASE_DIR)

    @pytest.mark.usefixtures("populate_db")
    @mock.patch.object(S3FileStorage, "get_file")
    def test_file_storage_load_templates_no_template_file_found(self, mock_s3_get_file,
                                                                s3_file_storage: S3FileStorage, db: Session):
        # folder has static assets but is missing the {id}.html index file
        mock_s3_get_file.return_value = {"/0/static/abc_1": b"static content",
                                         "/0/static/abc_2": b"static content"}

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            with pytest.raises(NoIndexTemplateFound):
                s3_file_storage.load_templates(template_dir, BASE_DIR, db)

            template_file_1 = f'{template_dir}/{get_local_template_file_path(template_id="0")}'
            assert not pathlib.Path(template_file_1).is_file()

        mock_s3_get_file.assert_called_once_with(path=f"{BASE_DIR}/0", template_directory=BASE_DIR)

    @mock.patch('app.file_storage.s3.iter_bucket')
    def test_file_storage_get_file_s3(self, mock_iter_bucket, s3_file_storage: S3FileStorage):
        mock_iter_bucket.side_effect = [
            [('templating/static/0/abc_1', b'static content'), ('templating/static/0/abc_2', b'static content'),],
            [('templating/templates/0/0', b'file content'),]
        ]

        static_files_dict = s3_file_storage.get_file(f"{BASE_DIR}/static", BASE_DIR)
        assert static_files_dict == {"/static/0/abc_1": b"static content",
                                     "/static/0/abc_2": b"static content"}

        template_files_dict = s3_file_storage.get_file(f"{BASE_DIR}/templates", BASE_DIR)
        assert template_files_dict == {"/templates/0/0": b'file content'}

        calls = [call(bucket_name="test_template_bucket", prefix=f"{BASE_DIR}/static", session_kwargs=s3_file_storage.aws_credentials_dict),
                 call(bucket_name="test_template_bucket", prefix=f"{BASE_DIR}/templates", session_kwargs=s3_file_storage.aws_credentials_dict)]
        mock_iter_bucket.assert_has_calls(calls, any_order=True)
        # when debugging, the mocked iterator calls __len__() for some reason. this is why any_order is set to True
        # to, at least, guarantee that the calls we want actually are present in mock_iter_bucket.mock_calls

    def test_file_storage_get_file_gcs(self, gcs_file_storage: tuple[GCSFileStorage, MagicMock]):
        gcs_storage, bucket = gcs_file_storage
        template_blob = MagicMock(Blob)
        static_blob_1 = MagicMock(Blob)
        static_blob_2 = MagicMock(Blob)

        template_blob.name, static_blob_1.name, static_blob_2.name = ["templating/templates/0/0", "templating/static/0/abc_1", "templating/static/0/abc_2"]
        template_blob.download_as_bytes.return_value = b'file content'
        static_blob_1.download_as_bytes.return_value = b'static content'
        static_blob_2.download_as_bytes.return_value = b'static content'

        bucket.list_blobs.side_effect = [[static_blob_1, static_blob_2], [template_blob]]

        static_files_dict = gcs_storage.get_file(f"{BASE_DIR}/static", BASE_DIR)
        assert static_files_dict == {"/static/0/abc_1": b"static content",
                                     "/static/0/abc_2": b"static content"}

        template_files_dict = gcs_storage.get_file(f"{BASE_DIR}/templates", BASE_DIR)
        assert template_files_dict == {"/templates/0/0": b'file content'}

        calls = [call(prefix=f"{BASE_DIR}/static"),
                 call(prefix=f"{BASE_DIR}/templates")]
        bucket.list_blobs.assert_has_calls(calls)
