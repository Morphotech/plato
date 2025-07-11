from typing import Optional

import click
from flask import Flask
from flask.cli import with_appcontext
import json
from .db import db
from .db.models import Template
from .file_storage import StorageType
from .settings import TEMPLATE_DIRECTORY, TEMPLATE_DIRECTORY_NAME, STORAGE_TYPE
from .util.setup_util import initialize_file_storage


def register_cli_commands(app: Flask):
    @app.shell_context_processor
    def make_shell_context():
        return dict(app=app, db=db, Template=Template)

    @app.cli.command("register_new_template")
    @click.argument("json_file", type=click.File("r"))
    @with_appcontext
    def register_new_template(json_file):
        """
        Imports new template from json file and inserts it in database
        Args:
            json_file: file containing the template json
        """
        template_entry_json = json.load(json_file)
        new_template = Template.from_json_dict(template_entry_json)
        db.session.add(new_template)
        db.session.commit()

    @app.cli.command("export_template")
    @click.argument("output", type=click.File("w"))
    @click.option("--template-id", default=None, type=click.STRING)
    @with_appcontext
    def export_template(output, template_id: Optional[str] = None):
        """
        Export new template to file
        Args:
            output: output file
            template_id: template to be exported
        """
        if template_id is None:
            templates = Template.query.all()
            template_options = "\n".join([template.id for template in templates])
            click.echo(template_options)
            template_id = click.prompt("Please enter the id for the template you wish to export")
        template = Template.query.filter_by(id=template_id).one()
        json.dump(template.json_dict(), output)

    @app.cli.command("refresh")
    @with_appcontext
    def refresh_local_templates():
        """
        Refresh local templates by loading the templates from AWS S3 Bucket
        """
        file_storage = initialize_file_storage(STORAGE_TYPE)
        with app.app_context():
            file_storage.load_templates(TEMPLATE_DIRECTORY, TEMPLATE_DIRECTORY_NAME)
