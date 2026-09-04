def template_path(template_dir: str, template_id: str) -> str:
    """
        Returns the folder path for a certain template, containing its index HTML file
        and its static/ subfolder
    """
    return f"{template_dir}/{template_id}"
