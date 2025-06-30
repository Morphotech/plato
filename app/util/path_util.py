
def template_path(template_dir: str, template_id: str) -> str:
    """
        Returns a path for a certain template
    """
    return f"{template_dir}/templates/{template_id}/{template_id}"


def static_file_path(template_dir: str, template_id: str, static_file: str) -> str:
    """
        Returns a path for a static file of a certain template
    """
    return f"{base_static_path(template_dir)}/{template_id}/{static_file}"


def static_path(template_dir: str, template_id: str) -> str:
    """
        Returns a path for static files of a certain template
    """
    return f"{base_static_path(template_dir)}/{template_id}"


def base_static_path(template_dir: str) -> str:
    """
        Returns the base path for the static content
    """
    return f"{template_dir}/static"


def tmp_path(file_name: str) -> str:
    """
        Returns the tmp path where the file (without its extension) can be stored
    """
    return f"/tmp/{file_name}"


def tmp_zipfile_path(zip_file_name: str) -> str:
    """
        Returns the tmp path where the zip file is going to be stored
    """
    return f"{tmp_path(zip_file_name)}.zip"
