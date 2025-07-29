import pathlib
import shutil
from abc import ABC
from enum import Enum
from typing import Dict, Any

from smart_open import s3
from google.cloud.storage import Client
from sqlalchemy.orm import Session

from app.models.template import Template
from app.settings import get_settings
from app.util.path_util import base_static_path, template_path


class StorageType(str, Enum):
    S3 = 's3'
    DISK = 'disk'
    GCS = 'gcs'


class FileStorageError(Exception):
    """
    Error for any setup Exception to occur when running this module's functions.
    """
    ...


class NoIndexTemplateFound(FileStorageError):
    """
    Raised when no template found on file storage
    """

    def __init__(self, template_id: str):
        """
        Exception initialization

        Args:
            template_id (str): the id of the template
        """
        super().__init__(f"No index template file found. Template_id: {template_id}")


class PlatoFileStorage(ABC):
    def __init__(self, data_directory: str):
        self.files_directory_name = data_directory

    @staticmethod
    def write_files(files: Dict[str, Any], target_directory: str) -> None:
        """
        Write files to a supplied target directory

        Args:
            files (Dict[str, Any]): a dict representing files needing to be written in the target directory
                with key as the file url and the value as file content
            target_directory (str): the directory all the files will reside in
        """
        for key, content in files.items():
            path = pathlib.Path(f"{target_directory}/{key}")
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, mode="wb") as file:
                file.write(content)

    def get_file(self, path: str, template_directory: str) -> Dict[str, Any]:
        """
        Get files from a storage service and save them in the form of a dict. If a folder is inserted as the url,
            all files in that folder will be returned

        Args:
            path (str): the url leading to the file/folder
            template_directory (str): the s3-bucket path for the templates directory

        Returns:
         A dictionary with key as file's relative location on s3-bucket and value as file's content
        """
        pass

    def load_templates(self, target_directory: str, template_directory_name: str, db: Session) -> None:
        """
        Gets templates from the bucket which are associated with ones available in the DB.
        Expected directory structure is {template_directory_name}/{template_id}
        Args:
            target_directory: Target directory to store the templates in
            template_directory_name: Base directory
            db (Session): The database session to query templates from
        """
        old_templates_path = pathlib.Path(target_directory)
        if old_templates_path.exists():
            shutil.rmtree(old_templates_path)

        # get static files
        static_files = self.get_file(path=base_static_path(template_directory_name),
                                     template_directory=template_directory_name)

        self.write_files(files=static_files, target_directory=target_directory)

        templates = db.query(Template).all()
        for template in templates:
            # get template content
            template_files = self.get_file(path=template_path(template_directory_name, template.id),
                                           template_directory=template_directory_name)
            if not template_files:
                raise NoIndexTemplateFound(template.id)
            self.write_files(files=template_files, target_directory=target_directory)


class DiskFileStorage(PlatoFileStorage):
    def __init__(self, data_directory: str):
        super().__init__(data_directory)


class S3FileStorage(PlatoFileStorage):
    def __init__(self, data_directory: str, bucket_name: str):
        super().__init__(data_directory)
        self.bucket_name = bucket_name

    def get_file(self, path: str, template_directory: str) -> Dict[str, Any]:
        """
        Get files from S3 and save them in the form of a dict. If a folder is inserted as the url, all files in that folder
            will be returned

        Args:
            path (str): the url leading to the file/folder
            template_directory (str): the s3-bucket path for the templates directory

        Returns:
         A dictionary with key as file's relative location on s3-bucket and value as file's content
        """
        key_content_mapping: dict = {}
        for key, content in s3.iter_bucket(bucket_name=self.bucket_name, prefix=path):
            if key[-1] == '/' or not content:
                # Is a directory
                continue
            # based on https://www.python.org/dev/peps/pep-0616/
            new_key = key[len(template_directory):]
            key_content_mapping[new_key] = content
        return key_content_mapping


class GCSFileStorage(PlatoFileStorage):
    def __init__(self, data_directory: str, bucket_name: str):
        super().__init__(data_directory)
        self.bucket_name = bucket_name
        self.gcs_client = Client.from_service_account_json(f"{get_settings().CREDENTIALS_DIR}/service_account_key.json")

    def get_file(self, path: str, template_directory: str) -> Dict[str, Any]:
        """
        Get files from GCS and save them in the form of a dict. If a folder is inserted as the url, all files in that folder
            will be returned

        Args:
            path (str): the url leading to the file/folder
            template_directory (str): the gcs-bucket path for the templates directory

        Returns:
         A dictionary with key as file's relative location on gcs-bucket and value as file's content
        """
        key_content_mapping: dict = {}
        blobs = list(self.gcs_client.bucket(self.bucket_name).list_blobs(prefix=path))
        for blob in blobs:
            # based on https://www.python.org/dev/peps/pep-0616/
            new_key = blob.name[len(template_directory):]
            key_content_mapping[new_key] = blob.download_as_bytes()
        return key_content_mapping


