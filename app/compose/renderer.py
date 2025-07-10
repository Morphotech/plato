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

PDF_MIME = "application/pdf"
HTML_MIME = "text/html"
PNG_MIME = "image/png"
OCTET_STREAM = "application/octet-stream"


class RendererNotFound(Exception):
    """
    Exception to be raised when there is no renderer for the requested MIME type
    """
    ...


class InvalidPageNumber(ValueError):
    """
    Exception to be raised when the given page number is invalid, either by being a negative number or by
    being higher than the number of pages on the template
    """
    message: str

    def __init__(self, message: str):
        self.message = message
        super().__init__()


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
    mime_type = OCTET_STREAM
    """MIME type for the renderer. Should be implemented by subclass. e.g: 'text/plain', 'application/pdf'
    """
    renderers: ClassVar[Dict[str, 'Renderer']] = dict()

    def __init__(self, template_model: Template, jinja_env: JinjaEnv, template_static_directory: str):
        self.template_model = template_model
        self.jinja_env = jinja_env
        self.template_static_directory = template_static_directory

    def compose_html(self, compose_data: dict) -> str:
        """
        Creates the template HTML string using the Jinja2 environment.

        Args:
            compose_data:

        Returns:
            str: HTML string for composed file.
        """
        template_static_directory = f"{self.template_static_directory}/{self.template_model.id}/"
        base_static_directory = f"{self.template_static_directory}/"

        jinja_template = self.jinja_env.get_template(
            name=f"{self.template_model.id}/{self.template_model.id}"
        )  # template id works for the file as well

        return jinja_template.render(p=compose_data,
                                     base_static=base_static_directory,
                                     template_static=template_static_directory)

    def render(self, compose_data: dict) -> io.BytesIO:
        """
        Renders Template onto a stream according to the Renderer's MIME type.

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
    def build_renderer(cls, mime_type: str, *args, **kwargs) -> Type['Renderer'] | None:
        """
        Factory method for 'Renderer' subclasses registered with @Renderer.renderer()

        Args:
            mime_type: the desired renderer output as a MIME type. e.g 'application/PDF'
            *args: the arguments to be passed to the specific constructor, by default same as Renderer.__init__.
        Raises:
            RendererNotFound: When there is no Renderer for the given mime_type
        Returns:
            Renderer: renderer for the desired mime_type output.
        """

        if mime_type not in cls.renderers:
            raise RendererNotFound(mime_type)
        sub_renderer = cls.renderers.get(mime_type)

        return sub_renderer(*args, **kwargs)

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

    def qr_render(self, output_folder: str, compose_data: dict):
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

    mime_type = PDF_MIME

    def print(self, html_string: str) -> io.BytesIO:

        with tempfile.NamedTemporaryFile() as target_file_html:
            html = HTML(string=html_string)
            html.write_pdf(target_file_html.name)
            with open(target_file_html.name, mode='rb') as temp_file_stream:
                return io.BytesIO(temp_file_stream.read())


@Renderer.renderer()
class PNGRenderer(Renderer):
    """
    PNG Renderer which uses weasyprint to generate PNG documents.
    """

    mime_type = PNG_MIME
    _width: int | None = None
    _height: int | None = None
    _page: int = 0

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if self.width is not None and value is not None:
            raise ValueError("Unable to use both height and width in order to maintain aspect ratio")
        self._height = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        if self.height is not None and value is not None:
            raise ValueError("Unable to use both height and width in order to maintain aspect ratio")
        self._width = value

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        if value < 0:
            raise InvalidPageNumber(f"A negative number is not allowed as a page value: {value}")
        self._page = value

    def __init__(self, template_model: Template,
                 jinja_env: JinjaEnv, 
                 template_static_directory: str,
                 height: int | None = None,
                 width: int | None = None,
                 page: int = 0):
        self.height = height
        self.width = width
        self.page = page
        super().__init__(template_model, jinja_env, template_static_directory)

    def print(self, html_string: str) -> io.BytesIO:

        with tempfile.NamedTemporaryFile() as target_file_html:
            html = HTML(string=html_string)
            weasy_doc = html.render(enable_hinting=True)

            if self.page >= len(weasy_doc.pages):
                raise InvalidPageNumber(f"Page number ({self.page}) is larger than the maximum page number ({len(weasy_doc.pages)-1})")

            page_to_print = weasy_doc.pages[self.page]   # Print only the requested page
            resolution_multiplier = 1

            if self.height is not None:
                resolution_multiplier = self.height / page_to_print.height
            elif self.width is not None:
                resolution_multiplier = self.width / page_to_print.width

            # 96 is the default resolution provided by weasyprint to maintain aspect ratio
            weasy_doc.copy([page_to_print]).write_png(target=target_file_html.name, resolution=resolution_multiplier * 96)
            with open(target_file_html.name, mode='rb') as temp_file_stream:
                return io.BytesIO(temp_file_stream.read())


@Renderer.renderer()
class HTMLRenderer(Renderer):
    """
    HTML Renderer which uses does nothing but return the plain HTML.
    """

    mime_type = HTML_MIME

    def print(self, html_string: str) -> io.BytesIO:
        return io.BytesIO(bytes(html_string, encoding="utf-8"))


def compose(template: Template, compose_data: dict, mime_type: str, jinja_env: JinjaEnv, template_static_directory:str, *args, **kwargs) -> io.BytesIO:
    """
    Composes a file of the given mime_type using the compose_data to fill the given template.

    Args:
        template: The Template model to be used in the composition
        mime_type: The desired output MIME type.
        compose_data: The dict with the data to fill the template.
        args: Additional arguments to be given to the specific renderer
        kwargs: Additional keyword arguments to be given to the specific renderer
    Raises:
        jsonschema.exceptions.ValidationError: When the compose_data is not valid for a given template
        RendererNotFound: When there is no Renderer for the given mime_type
    Returns:
        io.BytesIO: The Byte stream for the composed file.
    """
    validate_schema(instance=compose_data, schema=template.schema)
    renderer = Renderer.build_renderer(mime_type, template_model=template, jinja_env=jinja_env, template_static_directory=template_static_directory, *args, **kwargs)

    return renderer.render(compose_data)
