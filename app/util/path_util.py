def template_path(template_dir: str, template_id: str) -> str:
    """
        Returns a path for a certain template
    """
    return f"{template_dir}/templates/{template_id}/{template_id}"


def base_static_path(template_dir: str) -> str:
    """
        Returns the base path for the static content
    """
    return f"{template_dir}/static"
