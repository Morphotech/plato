from typing import Optional

import typer
from sqlalchemy.orm import Session

from app.models.template import Template
from app.deps import get_db
from app.schemas.template_detail import TemplateDetailSchema
from app.settings import get_settings
from app.util.setup_util import initialize_file_storage

app_cli = typer.Typer()
settings = get_settings()


def get_session() -> Session:
    return next(get_db())


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
        template_schema = TemplateDetailSchema.model_validate(template)
        f.write(template_schema.model_dump_json())
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