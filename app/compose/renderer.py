import io
import tempfile
from tempfile import TemporaryDirectory
from typing import Callable, Dict

from weasyprint import HTML
from jsonschema import validate as validate_schema
from jinja2 import Environment as JinjaEnv

from app.compose.qr import render_qr_codes
from app.models.template import Template
from app.schemas.template_detail import MIMETypeEnum
from app.settings import get_settings


class RendererNotFound(Exception):
    """
    Exception to be raised when there is no renderer for the requested MIME type
    """
    ...


def render_html(template: Template, compose_data: dict, jinja_env: JinjaEnv) -> str:
    """
    Creates the template HTML string using the Jinja2 environment.

    Args:
        template: The Template model to be used in the composition
        compose_data: The data to fill the template with.
        jinja_env: The Jinja2 environment to be used for rendering the template

    Returns:
        str: HTML string for composed file.
    """
    template_static_directory = f"{get_settings().TEMPLATE_DIRECTORY}/{template.id}/static/"
    jinja_template = jinja_env.get_template(name=f"{template.id}/{template.id}.html")
    return jinja_template.render(p=compose_data, template_static=template_static_directory)


def to_pdf(html: str) -> bytes:
    """
    Converts the given HTML string into PDF bytes using WeasyPrint.
    """
    with tempfile.NamedTemporaryFile() as target_file_html:
        HTML(string=html).write_pdf(target_file_html.name)
        with open(target_file_html.name, mode='rb') as temp_file_stream:
            return temp_file_stream.read()


def to_html(html: str) -> bytes:
    """
    Converts the given HTML string into UTF-8 encoded bytes.
    """
    return bytes(html, encoding="utf-8")


CONVERTERS: Dict[str, Callable[[str], bytes]] = {
    MIMETypeEnum.PDF_MIME.value: to_pdf,
    MIMETypeEnum.HTML_MIME.value: to_html,
}


def compose(template: Template, compose_data: dict, mime_type: str, jinja_env: JinjaEnv) -> io.BytesIO:
    """
    Composes a file of the given mime_type using the compose_data to fill the given template.

    Args:
        template: The Template model to be used in the composition
        mime_type: The desired output MIME type
        compose_data: The dict with the data to fill the template
        jinja_env: The Jinja2 environment to be used for rendering the template

    Raises:
        jsonschema.exceptions.ValidationError: When the compose_data is not valid for a given template
        RendererNotFound: When there is no converter for the given mime_type

    Returns:
        io.BytesIO: The Byte stream for the composed file.
    """
    validate_schema(instance=compose_data, schema=template.schema)

    if mime_type not in CONVERTERS:
        raise RendererNotFound(mime_type)
    converter = CONVERTERS[mime_type]

    with TemporaryDirectory() as temp_render_directory:
        compose_data = render_qr_codes(template, temp_render_directory, compose_data)
        html_string = render_html(template, compose_data, jinja_env)
        return io.BytesIO(converter(html_string))
