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
from google.cloud.storage import Blob
from google.cloud import storage
from google.cloud.storage import Client
from sqlalchemy.orm import Session
import pytest

from app.file_storage import DiskFileStorage, S3FileStorage, GCSFileStorage, NoIndexTemplateFound, FileStorageError
from app.models import Template
from app.file_storage import DiskFileStorage
from app.settings import get_settings

BASE_DIR = 'templates'
settings = get_settings()


def get_local_static_file_path(template_id: str, file_name: str):
    return f"{template_id}/static/{file_name}"

def get_local_template_file_path(template_id: str):
    return f"{template_id}/{template_id}.html"

def create_child_temp_folder(main_directory: str) -> str:
    template_dir_name = f"{main_directory}/{BASE_DIR}"
    pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
    return template_dir_name


@pytest.fixture
def s3_file_storage():
    with mock.patch("app.file_storage.S3FileStorage.get_aws_credentials") as mock_get_aws_credentials:
        mock_get_aws_credentials.return_value = {
            "aws_access_key_id": "test_aws_key",
            "aws_secret_access_key": "test_secret_key",
            "region_name": "test_region",
        }
        yield S3FileStorage("test_bucket")
        mock_get_aws_credentials.assert_called_once_with(f"{settings.CREDENTIALS_DIR}/aws_credentials.json")


@pytest.fixture
def gcs_file_storage():
    with mock.patch.object(Client, "from_service_account_json") as mock_init_client:
        gcs_client = MagicMock(spec=Client)
        bucket = MagicMock(spec=storage.Bucket)
        gcs_client.bucket.return_value = bucket
        mock_init_client.return_value = gcs_client
        yield GCSFileStorage("test_bucket"), bucket
        mock_init_client.assert_called_once_with(f"{settings.CREDENTIALS_DIR}/service_account_key.json")

@pytest.fixture(scope="function")
def populate_db(db: Session):
    template = Template(id_="certificate_template", schema={},
                        type_="text/html", tags=['test_tags'], metadata={},
                        example_composition={'place_holder': 'value'})
    db.add(template)
    db.commit()

    yield

    db.query(Template).delete()
    db.commit()

class TestFileStorage:
    def test_file_storage_write_files(self):
        files = {"certificate_template/certificate_template.html": b"file content",
                 "certificate_template/static/icon.png": b"static content",
                 "certificate_template/static/logo.jpeg": b"static content"}

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            DiskFileStorage.write_files(files, template_dir)

            static_file_1 = f'{template_dir}/{get_local_static_file_path(file_name="icon.png", template_id="certificate_template")}'
            static_file_2 = f'{template_dir}/{get_local_static_file_path(file_name="logo.jpeg", template_id="certificate_template")}'
            template_file_1 = f'{template_dir}/{get_local_template_file_path(template_id="certificate_template")}'

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
            result = S3FileStorage.get_aws_credentials("path_to_aws_credentials/aws_credentials.json")

        assert result == {"aws_access_key_id": "test_aws_key_unit_test",
                          "aws_secret_access_key": "test_secret_key_unit_test",
                          "region_name": "test_region_unit_test"}

    def test_get_aws_credentials_no_file_found(self):
        with pytest.raises(FileStorageError) as exc:
            S3FileStorage.get_aws_credentials("path_to_aws_credentials/aws_credentials.json")

        assert exc.value.args[0] == f"AWS credentials file not found at 'path_to_aws_credentials/aws_credentials.json'. Expected a UTF-8 encoded JSON file containing AWS credential key/value pairs."

    def test_get_aws_credentials_invalid_json_error(self):
        mock_aws_credentials_data = """\
            {"aws_access_key_id": "test_aws_key_unit_test",
             "aws_secret_access_key": "test_secret_key_unit_test",
             "region_name": "test_region_unit_test",
             invalid_key: invalid_value}
             """
        mock_aws_open = mock_open(read_data=mock_aws_credentials_data)

        with mock.patch("builtins.open", mock_aws_open):
            with pytest.raises(FileStorageError) as exc:
                S3FileStorage.get_aws_credentials("path_to_aws_credentials/aws_credentials.json")
        assert exc.value.args[0] == f"Invalid JSON in AWS credentials file at 'path_to_aws_credentials/aws_credentials.json'. Expected a UTF-8 encoded JSON object containing AWS credential key/value pairs."

    def test_get_gcs_client(self):
        fake_client = MagicMock(spec=Client)

        with mock.patch.object(Client, "from_service_account_json", return_value=fake_client) as mock_init_client:
            result = GCSFileStorage.get_gcs_client("path_to_gcs_credentials/service_account_key.json")

        mock_init_client.assert_called_once_with("path_to_gcs_credentials/service_account_key.json")
        assert result is fake_client

    def test_get_gcs_client_no_file_found(self):
        with mock.patch.object(Client, "from_service_account_json", side_effect=FileNotFoundError):
            with pytest.raises(FileStorageError) as exc:
                GCSFileStorage.get_gcs_client("path_to_gcs_credentials/service_account_key.json")

            assert exc.value.args[0] == f"GCS service account key file not found at 'path_to_gcs_credentials/service_account_key.json'. Expected a UTF-8 encoded JSON file containing GCS service account credentials."

    def test_get_gcs_client_invalid_json_error(self):
        with mock.patch.object(Client, "from_service_account_json",
                              side_effect=json.JSONDecodeError("Expecting value", "", 0)):
            with pytest.raises(FileStorageError) as exc:
                GCSFileStorage.get_gcs_client("path_to_gcs_credentials/service_account_key.json")

        assert exc.value.args[0] == f"Invalid JSON in GCS service account key file at 'path_to_gcs_credentials/service_account_key.json'. Expected a UTF-8 encoded JSON object containing GCS service account credentials."

    @pytest.mark.usefixtures("populate_db")
    @mock.patch.object(S3FileStorage, "get_file")
    def test_file_storage_load_templates(self, mock_s3_get_file, s3_file_storage, db: Session):
        mock_s3_get_file.return_value = {"/certificate_template/certificate_template.html": b"file content",
                                         "/certificate_template/static/icon.png": b"static content",
                                         "/certificate_template/static/logo.jpeg": b"static content"}

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            s3_file_storage.load_templates(template_dir, BASE_DIR, db)

            static_file_1 = f'{template_dir}/{get_local_static_file_path(file_name="icon.png", template_id="certificate_template")}'
            static_file_2 = f'{template_dir}/{get_local_static_file_path(file_name="logo.jpeg", template_id="certificate_template")}'
            template_file_1 = f'{template_dir}/{get_local_template_file_path(template_id="certificate_template")}'

            assert pathlib.Path(static_file_1).is_file()
            assert pathlib.Path(static_file_2).is_file()
            assert pathlib.Path(template_file_1).is_file()

        mock_s3_get_file.assert_called_once_with(path=f"{BASE_DIR}/certificate_template", template_directory=BASE_DIR)

    @pytest.mark.usefixtures("populate_db")
    @mock.patch.object(S3FileStorage, "get_file")
    def test_file_storage_load_templates_no_template_file_found(self, mock_s3_get_file, s3_file_storage, db: Session):
        # folder has static assets but is missing the {id}.html index file
        mock_s3_get_file.return_value = {"/certificate_template/static/icon.png": b"static content",
                                         "/certificate_template/static/logo.jpeg": b"static content"}

        with TemporaryDirectory() as temp:
            # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
            template_dir = create_child_temp_folder(temp)

            with pytest.raises(NoIndexTemplateFound):
                s3_file_storage.load_templates(template_dir, BASE_DIR, db)

            template_file_1 = f'{template_dir}/{get_local_template_file_path(template_id="certificate_template")}'
            assert not pathlib.Path(template_file_1).is_file()

        mock_s3_get_file.assert_called_once_with(path=f"{BASE_DIR}/certificate_template", template_directory=BASE_DIR)

    @mock.patch('app.file_storage.s3.iter_bucket')
    def test_file_storage_get_file_s3(self, mock_iter_bucket, s3_file_storage):
        mock_iter_bucket.return_value = [
            (f'{BASE_DIR}/certificate_template/static/icon.png', b'static content'),
            (f'{BASE_DIR}/certificate_template/static/logo.jpeg', b'static content'),
            (f'{BASE_DIR}/certificate_template/certificate_template.html', b'file content'),
        ]

        template_files_dict = s3_file_storage.get_file(f"{BASE_DIR}/certificate_template", BASE_DIR)
        assert template_files_dict == {
            "/certificate_template/static/icon.png": b"static content",
            "/certificate_template/static/logo.jpeg": b"static content",
            "/certificate_template/certificate_template.html": b'file content',
        }

        mock_iter_bucket.assert_called_once_with(bucket_name="test_bucket", prefix=f"{BASE_DIR}/certificate_template", session_kwargs=s3_file_storage.aws_credentials_dict)

    def test_file_storage_get_file_gcs(self, gcs_file_storage):
        template_blob = MagicMock(Blob)
        static_blob_1 = MagicMock(Blob)
        static_blob_2 = MagicMock(Blob)

        template_blob.name, static_blob_1.name, static_blob_2.name = [
            f"{BASE_DIR}/certificate_template/certificate_template.html",
            f"{BASE_DIR}/certificate_template/static/icon.png",
            f"{BASE_DIR}/certificate_template/static/logo.jpeg",
        ]
        template_blob.download_as_bytes.return_value = b'file content'
        static_blob_1.download_as_bytes.return_value = b'static content'
        static_blob_2.download_as_bytes.return_value = b'static content'

        bucket = gcs_file_storage[1]
        bucket.list_blobs.return_value = [static_blob_1, static_blob_2, template_blob]

        template_files_dict = gcs_file_storage[0].get_file(f"{BASE_DIR}/certificate_template", BASE_DIR)
        assert template_files_dict == {
            "/certificate_template/static/icon.png": b"static content",
            "/certificate_template/static/logo.jpeg": b"static content",
            "/certificate_template/certificate_template.html": b'file content',
        }

        bucket.list_blobs.assert_called_once_with(prefix=f"{BASE_DIR}/certificate_template")
