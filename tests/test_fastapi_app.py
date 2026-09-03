from contextlib import contextmanager
from unittest import mock
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from google.cloud.storage import Client

from app.fastapi_app import get_app
from app.file_storage import FileStorageError, NoIndexTemplateFound, S3FileStorage, StorageType
from app.models import Template
from app.settings import get_settings
from app.util.setup_util import InvalidFileStorageTypeException

settings = get_settings()


@pytest.fixture
def restore_storage_type():
    original = settings.STORAGE_TYPE
    yield
    settings.STORAGE_TYPE = original


class TestGetApp:
    def test_get_app_disk_storage(self, restore_storage_type, db):
        settings.STORAGE_TYPE = StorageType.DISK

        with mock.patch("app.fastapi_app.db_session", return_value=db):
            app = get_app()

        assert isinstance(app, FastAPI)

    def test_get_app_s3_storage(self, restore_storage_type, db):
        settings.STORAGE_TYPE = StorageType.S3

        with mock.patch("app.file_storage.S3FileStorage.get_aws_credentials") as mock_get_aws_credentials, \
             mock.patch("app.fastapi_app.db_session", return_value=db):
            mock_get_aws_credentials.return_value = {"aws_access_key_id": "test_aws_key",
                                                     "aws_secret_access_key": "test_secret_key",
                                                     "region_name": "test_region"}
            app = get_app()

        assert isinstance(app, FastAPI)
        mock_get_aws_credentials.assert_called_once()

    def test_get_app_gcs_storage(self, restore_storage_type, db):
        settings.STORAGE_TYPE = StorageType.GCS

        with mock.patch.object(Client, "from_service_account_json") as mock_init_client, \
             mock.patch("app.fastapi_app.db_session", return_value=db):
            mock_init_client.return_value = MagicMock(spec=Client)
            app = get_app()

        assert isinstance(app, FastAPI)
        mock_init_client.assert_called_once()

    def test_get_app_invalid_storage_type(self, restore_storage_type, db):
        settings.STORAGE_TYPE = "not_a_real_storage_type"

        with mock.patch("app.fastapi_app.db_session", return_value=db):
            with pytest.raises(InvalidFileStorageTypeException):
                get_app()

    def test_get_app_s3_missing_credentials(self, restore_storage_type, db):
        settings.STORAGE_TYPE = StorageType.S3

        with mock.patch("builtins.open", side_effect=FileNotFoundError), \
             mock.patch("app.fastapi_app.db_session", return_value=db):
            with pytest.raises(FileStorageError):
                get_app()

    def test_get_app_gcs_missing_credentials(self, restore_storage_type, db):
        settings.STORAGE_TYPE = StorageType.GCS

        with mock.patch.object(Client, "from_service_account_json", side_effect=FileNotFoundError), \
             mock.patch("app.fastapi_app.db_session", return_value=db):
            with pytest.raises(FileStorageError):
                get_app()

    @mock.patch.object(S3FileStorage, "get_file")
    def test_get_app_s3_no_index_template_found(self, mock_s3_get_file, restore_storage_type, db):
        settings.STORAGE_TYPE = StorageType.S3
        # folder has static assets but is missing the {id}.html index file
        mock_s3_get_file.return_value = {"/example_template/static/abc_1": b"static content"}
        template = Template(id_="example_template", schema={}, type_="text/html", tags=[], metadata={},
                            example_composition={})

        db.add(template)
        db.commit()
        try:
            with mock.patch("app.file_storage.S3FileStorage.get_aws_credentials") as mock_get_aws_credentials, \
                 mock.patch("app.fastapi_app.db_session", return_value=db):
                mock_get_aws_credentials.return_value = {"aws_access_key_id": "test_aws_key",
                                                         "aws_secret_access_key": "test_secret_key",
                                                         "region_name": "test_region"}
                with pytest.raises(NoIndexTemplateFound):
                    get_app()
        finally:
            db.query(Template).filter_by(id="example_template").delete()
            db.commit()
