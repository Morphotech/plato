import os
import pathlib
import shutil
import zipfile
from abc import ABC, abstractmethod
from enum import Enum
from typing import BinaryIO, Dict, Any
from pathlib import Path

from smart_open import s3
from sqlalchemy.orm import Session

from app.util.path_util import base_static_path, static_file_path, static_path, template_path, tmp_path, tmp_zipfile_path
from app.models.template import Template


class StorageType(str, Enum):
    S3 = 's3'
    DISK = 'disk'


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

    def save_template_files(self, template_id: str, template_dir: str, zip_file_name: str) -> None:
        """
        Uploads template related files (static and template) to their respective file directories

        Args:
            template_id (str): the template id
            template_dir (str): The template directory
            zip_file_name (str): the filename for the zipfile
        """
        base_tmp_path = tmp_path(zip_file_name)
        # extract files to temporary directory
        file = zipfile.ZipFile(tmp_zipfile_path(zip_file_name))
        file.extractall(path=base_tmp_path)

        local_template = Path(template_path(base_tmp_path, template_id))
        with local_template.open(mode='rb') as tmp_file:
            self.save_file(tmp_file, template_path(template_dir, template_id))

        static_files = os.listdir(static_path(base_tmp_path, template_id))
        for static_file in static_files:
            tmp_static_sys_path = Path(static_file_path(base_tmp_path, template_id, static_file))
            with tmp_static_sys_path.open(mode='rb') as tmp_file:
                self.save_file(tmp_file, static_file_path(template_dir, template_id, static_file))

    @abstractmethod
    def save_file(self, input_file: BinaryIO, path: str) -> None:
        """
        Write file into storage folder

        Args:
            input_file (BinaryIO): the input file
            path (str): the storage path
        """
        raise NotImplementedError

    def write_file_locally(self, input_file: BinaryIO, path: str):
        """
        Writes a file to the defined target directory inside the project's data folder

        Args:
            input_file (BinaryIO): the file
            path (str): the target directory path
        """

        path = pathlib.Path(f"{self.files_directory_name}/{path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode="wb") as file:
            input_file.seek(0)
            file.write(input_file.read())

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

    def load_templates(self, target_directory: str, template_directory: str, db: Session) -> None:
        """
        Args:
            target_directory: Target directory to store the templates in
            template_directory: Base directory
        """
        pass


class DiskFileStorage(PlatoFileStorage):
    def __init__(self, data_directory: str):
        super().__init__(data_directory)

    def save_file(self, input_file: BinaryIO, path: str) -> None:
        """
        Write file into local storage folder

        Args:
            input_file (BinaryIO): the input file
            path (str): the local storage path
        """
        self.write_file_locally(input_file, path)


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

    def save_file(self, input_file: BinaryIO, path: str) -> None:
        """
        Write file to S3 Bucket Path and then write it into local folder

        Args:
            input_file (BinaryIO): the input file
            path (str): the S3 Bucket path
        """
        with s3.open(self.bucket_name, path, mode='wb') as file:
            file.write(input_file.read())

        self.write_file_locally(input_file, path)

    def load_templates(self, target_directory: str, template_directory_name: str, db: Session) -> None:
        """
        Gets templates from the AWS S3 bucket which are associated with ones available in the DB.
        Expected directory structure is {template_directory_name}/{template_id}

        Args:
            target_directory: Target directory to store the templates in
            template_directory_name: Base directory name for S3 Bucket
            db (Session): The database session to query templates from

        Raises:
            NoIndexTemplateFound: If no index template file is found for a given template id
        """
        old_templates_path = pathlib.Path(target_directory)
        if old_templates_path.exists():
            shutil.rmtree(old_templates_path)

        # get static files
        static_files = self.get_file(path=base_static_path(template_directory_name),
                                     template_directory=template_directory_name)

        self.write_files(files=static_files, target_directory=target_directory)

        templates = db.query(Template).all() # todo use template
        for template in templates:
            # get template content
            template_files = self.get_file(path=template_path(template_directory_name, template.id),
                                           template_directory=template_directory_name)
            if not template_files:
                raise NoIndexTemplateFound(template.id)
            self.write_files(files=template_files, target_directory=target_directory)
