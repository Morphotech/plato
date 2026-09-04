import io

import pytest
from jinja2 import DictLoader, Environment as JinjaEnv, select_autoescape
from jsonschema import ValidationError

from app.compose.renderer import HTMLRenderer, PdfRenderer, Renderer, RendererNotFound, compose, PNGRenderer
from app.models.template import Template
from app.schemas.template_detail import MIMETypeEnum


def _make_jinja_env():
    return JinjaEnv(loader=DictLoader({}), autoescape=select_autoescape(["html", "xml"]))


class TestRenderer:
    def test_build_renderer_renderer_not_found(self):
        with pytest.raises(RendererNotFound):
            Renderer.build_renderer("application/unsupported-mime-type")

    @pytest.mark.parametrize("mime_type, renderer_class", [
        ("application/pdf", PdfRenderer),
        ("text/html", HTMLRenderer),
        ("image/png", PNGRenderer),
    ])
    def test_build_renderer(self, mime_type, renderer_class):
        template = Template(id_="test_template", schema={}, type_="text/html",
                            tags=[], metadata={}, example_composition={})
        renderer = Renderer.build_renderer(mime_type,
                                           template_model=template, jinja_env=_make_jinja_env())

        assert isinstance(renderer, renderer_class)

    @pytest.mark.parametrize("extension, renderer_class", [
        (".pdf", PdfRenderer),
        (".html", HTMLRenderer),
        (".png", PNGRenderer),
    ])
    def test_file_extension_pdf(self, extension, renderer_class):
        assert renderer_class.file_extension() == extension

    def test_print(self):
        template = Template(id_="test_template", schema={}, type_="text/html",
                            tags=[], metadata={}, example_composition={})
        renderer = HTMLRenderer(template_model=template, jinja_env=_make_jinja_env())

        result = renderer.print("<p>hello</p>")

        assert isinstance(result, io.BytesIO)
        assert result.read() == b"<p>hello</p>"

    @pytest.mark.parametrize("mime_type", [
        "application/pdf",
        "text/html",
        "image/png",
    ])
    def test_compose_invalid_data(self, mime_type):
        schema = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}
        template = template = Template(id_="test_template", schema=schema, type_="text/html",
                                       tags=[], metadata={}, example_composition={})

        with pytest.raises(ValidationError):
            compose(template, {}, mime_type, _make_jinja_env())
