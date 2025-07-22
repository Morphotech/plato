from jinja2 import Environment as JinjaEnv, FileSystemLoader, select_autoescape

from app.compose import FILTERS
from ..file_storage import PlatoFileStorage, S3FileStorage, DiskFileStorage, StorageType


class InvalidFileStorageTypeException(Exception):
    """
    Exception raised when attempting to initialize the File Storage with an invalid type
    """
    def __init__(self, type_: str):
        """
        Constructor method
        """
        super(InvalidFileStorageTypeException, self).__init__(type_)


def create_template_environment(template_directory_path: str) -> JinjaEnv:
    """
    Setup jinja2 templating engine from a given directory path.
    Also adds all available filters to the JinjaEnv, which are available to be directly used within the template HTML files.
    Example usage of filter: {{ p.date | filter_function(args) }}

    Args:
        template_directory_path: Path to the directory where templates are stored

    Returns:
        JinjaEnv: Jinja2 Environment with templating
    """
    env = JinjaEnv(
        loader=FileSystemLoader(f"{template_directory_path}/templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    env.filters.update({filter_.__name__: filter_ for filter_ in FILTERS})
    return env


def initialize_file_storage(storage_type: str, data_dir: str, s3_bucket: str | None) -> PlatoFileStorage:
    """
    Initializes a correct instance of the Plato File Storage, depending on the env values.

    Args:
        storage_type (str): The type of file storage to be used, either 'disk' or 's3'.
        data_dir (str): The data directory for the file storage.
        s3_bucket (str): The S3 bucket name for the file storage.

    Raises:
        InvalidFileStorageTypeException: If the given file storage type doesn't exist.

    Returns:
        PlatoFileStorage: An instance of PlatoFileStorage.

    """
    file_storage: PlatoFileStorage
    if storage_type == StorageType.DISK:
        file_storage = DiskFileStorage(data_dir)
    elif storage_type == StorageType.S3:
        file_storage = S3FileStorage(data_dir, s3_bucket)
    else:
        raise InvalidFileStorageTypeException(storage_type)
    return file_storage
