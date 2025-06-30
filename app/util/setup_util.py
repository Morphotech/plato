import os

from jinja2 import Environment as JinjaEnv, FileSystemLoader, select_autoescape
from app.compose import FILTERS
from ..file_storage import PlatoFileStorage, S3FileStorage, DiskFileStorage, StorageType
from .. import settings


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


def setup_swagger_ui(project_name: str, project_version: str) -> dict:
    """
    Configurations to be used on the Swagger-ui page.

    Args:
        project_name: The project name to be displayed
        project_version: The project version to be displayed
    Returns:
        dict: The swagger ui configuration to be used with Flasgger
    """
    swagger_ui_config = {
        'title': project_name,
        'version': project_version,
        'uiversion': 3,
        'swagger': '2.0',
        'favicon': "/static/favicon-32x32.png",
        'swagger_ui_css': "/static/swagger-ui.css",
        'swagger_ui_standalone_preset_js': '/static/swagger-ui-standalone-preset.js',
        'description': ''
    }

    return swagger_ui_config


def initialize_file_storage(storage_type: str, data_dir: str, s3_bucket: str) -> PlatoFileStorage:
    """
    Initializes a correct instance of the Plato File Storage, depending on the env values

    :param storage_type: The storage type
    :type storage_type: str

    :raises InvalidFileStorageTypeException: If the given file storage type doesn't exist

    :return: An instance of FileStorage
    :rtype: class:`FileStorage`
    """
    file_storage: PlatoFileStorage
    if storage_type == StorageType.DISK:
        file_storage = DiskFileStorage(data_dir)
    elif storage_type == StorageType.S3:
        file_storage = S3FileStorage(data_dir, s3_bucket)
    else:
        raise InvalidFileStorageTypeException(storage_type)
    return file_storage


def inside_container():
    """
    Returns true if we are running inside a container.
    Copied from testcontainers library as testcontainers are a dev dependency.

    https://github.com/docker/docker/blob/a9fa38b1edf30b23cae3eade0be48b3d4b1de14b/daemon/initlayer/setup_unix.go#L25
    """
    return os.path.exists('/.dockerenv')
