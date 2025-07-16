import json
from typing import Optional

import typer
from sqlalchemy.orm import Session

from app.models.template import Template
from app.deps import get_db
from app.settings import get_settings
from app.util.setup_util import initialize_file_storage

app_cli = typer.Typer()
settings = get_settings()


def get_session() -> Session:
    return next(get_db())

@app_cli.command()
def register_new_template(json_file_path: str):
    """
    Imports new template from json file and inserts it in database.

    Args:
        json_file_path (str): Path to the JSON file containing the template definition.
    """
    session = get_session()
    with open(json_file_path, "r") as f:
        template_entry_json = json.load(f)
    new_template = Template.from_json_dict(template_entry_json)
    session.add(new_template)
    session.commit()
    typer.echo("Template registered.")

@app_cli.command()
def export_template(output: str, template_id: Optional[str] = None):
    """
    Export template to file.

    If template_id is not provided, it will list all available templates and prompt for selection.

    Args:
        output (str): The output file path where the template will be saved.
        template_id (Optional[str]): The ID of the template to export. If None, it will prompt for selection.
    """
    session = get_session()
    if template_id is None:
        templates = session.query(Template).all()
        template_options = "\n".join([template.id for template in templates])
        typer.echo(template_options)
        template_id = typer.prompt("Please enter the id for the template you wish to export")
    template = session.query(Template).filter_by(id=template_id).one()
    with open(output, "w") as f:
        json.dump(template.json_dict(), f)
    typer.echo(f"Template {template_id} exported to {output}.")

@app_cli.command()
def refresh():
    """
    Refresh local templates by loading the templates from file storage.
    """
    file_storage = initialize_file_storage(settings.STORAGE_TYPE, settings.DATA_DIR, settings.S3_BUCKET)
    with get_session() as db_session:
        file_storage.load_templates(settings.TEMPLATE_DIRECTORY, settings.TEMPLATE_DIRECTORY_NAME, db_session)
    typer.echo("Templates refreshed.")


if __name__ == "__main__":
    app_cli()