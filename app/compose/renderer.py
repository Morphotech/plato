import io
import tempfile
from abc import abstractmethod, ABC
from jmespath import search
from mimetypes import guess_extension
from typing import Type, ClassVar, Dict, List
from qrcode import make
from tempfile import TemporaryDirectory
from weasyprint import HTML
from jsonschema import validate as validate_schema
from jinja2 import Environment as JinjaEnv

from app.models.template import Template
from app.schemas.template_detail import MIMETypeEnum
from app.settings import get_settings


class RendererNotFound(Exception):
    """
    Exception to be raised when there is no renderer for the requested MIME type
    """
    ...


class Renderer(ABC):
    """
    Renderer is a factory for every Renderer subclass.

        Typical usage:

            Renderer.build_renderer('application/pdf')

        You may also create your own renderer by extending 'Renderer' and registering it in the factory by using the
        'renderer' decorator like so:

        @Renderer.renderer()
        class MyRenderer(Renderer):
        ...

    """
    mime_type = MIMETypeEnum.OCTET_STREAM.value
    """
    MIME type for the renderer. Should be implemented by subclass. e.g: 'text/plain', 'application/pdf'
    """
    renderers: ClassVar[Dict[str, 'Renderer']] = dict()

    def __init__(self, template_model: Template, jinja_env: JinjaEnv):
        self.template_model = template_model
        self.jinja_env = jinja_env

    def compose_html(self, compose_data: dict) -> str:
        """
        Creates the template HTML string using the Jinja2 environment.

        Args:
            compose_data: The data to fill the template with.

        Returns:
            str: HTML string for composed file.
        """
        template_static_directory = f"{get_settings().TEMPLATE_DIRECTORY}/{self.template_model.id}/static/"

        jinja_template = self.jinja_env.get_template(
            name=f"{self.template_model.id}/{self.template_model.id}.html"
        )

        return jinja_template.render(p=compose_data,
                                     template_static=template_static_directory)

    def render(self, compose_data: dict) -> io.BytesIO:
        """
        Renders Template onto a stream according to the Renderer's MIME type.

        Args:
            compose_data: The data to fill the template with.

        Returns:
            io.BytesIO: A file stream with the Renderer's MIME type.
        """
        with TemporaryDirectory() as temp_render_directory:
            compose_data = self.qr_render(temp_render_directory, compose_data)
            html_string = self.compose_html(compose_data)
            return self.print(html_string)

    @abstractmethod
    def print(self, html: str) -> io.BytesIO:
        """
        Print the file according to the Renderer MIME type.

        Args:
            html: The HTML to be printed

        Returns:
            io.BytesIO: A file stream with the Renderer's MIME type.
        """
        ...

    @classmethod
    def file_extension(cls) -> str:
        """
        File extension for the renderer. Guesses it using mimetypes.py library.
        e.g: 'text/plain', 'application/pdf'
        """
        return guess_extension(cls.mime_type)

    @classmethod
    def build_renderer(cls, mime_type: str, template_model: Template, jinja_env: JinjaEnv) -> Type['Renderer'] | None:
        """
        Factory method for 'Renderer' subclasses registered with @Renderer.renderer()

        Args:
            mime_type: the desired renderer output as a MIME type. e.g 'application/PDF'
            template_model: the Template to be used in the composition
            jinja_env: the Jinja2 environment to be used for rendering the template
        Raises:
            RendererNotFound: When there is no Renderer for the given mime_type
        Returns:
            Renderer: renderer for the desired mime_type output.
        """

        if mime_type not in cls.renderers:
            raise RendererNotFound(mime_type)
        sub_renderer = cls.renderers.get(mime_type)

        return sub_renderer(template_model=template_model, jinja_env=jinja_env)

    @classmethod
    def renderer(cls):
        """
        Decorator to be used when registering a new renderer.

        Returns:
            the renderer type
        """
        def wrapper(type_: Type['Renderer']) -> Type['Renderer']:
            assert issubclass(type_, Renderer)
            cls.renderers[type_.mime_type] = type_
            return type_
        return wrapper

    def qr_render(self, output_folder: str, compose_data: dict) -> dict:
        """
        Render QR codes, altering self.compose_data to replace qr_code properties with the filepath to their renders

        Args:
            output_folder: where to store the QR images renderer
            compose_data: the data to fill the template with

        Returns:
            dict: altered compose_data
        """
        qr_schema_paths = self.template_model.get_qr_entries()

        def set_nested(key_list: List[str], dict_: dict, value: str):
            """
            Sets dict_[key1, key2, ...] = value

            Args:
                key_list: Nested key list
                dict_: Dict to be iterated with key_list
                value: Value to be set
            """
            for key in key_list[:-1]:
                dict_ = dict_[key]
            dict_[key_list[-1]] = value

        for i, qr_schema_path in enumerate(qr_schema_paths):
            with open(f"{output_folder}/{i}.png", mode="wb") as qr_file:
                qr_value = search(qr_schema_path, compose_data) 
                if qr_value is not None:
                    img = make(qr_value)
                    img.save(qr_file)
                    set_nested(qr_schema_path.split("."), compose_data, qr_file.name)

        return compose_data


@Renderer.renderer()
class PdfRenderer(Renderer):
    """
    PDF Renderer which uses weasyprint to generate PDF documents.
    """

    mime_type = MIMETypeEnum.PDF_MIME.value

    def print(self, html_string: str) -> io.BytesIO:

        with tempfile.NamedTemporaryFile() as target_file_html:
            html = HTML(string=html_string)
            html.write_pdf(target_file_html.name)
            with open(target_file_html.name, mode='rb') as temp_file_stream:
                return io.BytesIO(temp_file_stream.read())


@Renderer.renderer()
class HTMLRenderer(Renderer):
    """
    HTML Renderer which uses does nothing but return the plain HTML.
    """

    mime_type = MIMETypeEnum.HTML_MIME.value

    def print(self, html_string: str) -> io.BytesIO:
        """
        Converts the given HTML string into a BytesIO stream encoded as UTF-8.

        Args:
            html_string (str): The HTML content to be rendered.

        Returns:
            io.BytesIO: A stream containing the UTF-8 encoded HTML content.
        """
        return io.BytesIO(bytes(html_string, encoding="utf-8"))


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
        RendererNotFound: When there is no Renderer for the given mime_type

    Returns:
        io.BytesIO: The Byte stream for the composed file.
    """
    validate_schema(instance=compose_data, schema=template.schema)
    renderer = Renderer.build_renderer(mime_type, template_model=template, jinja_env=jinja_env)

    return renderer.render(compose_data)
