import pytest
from jinja2 import DictLoader, Environment as JinjaEnv, select_autoescape
from jsonschema import ValidationError

from app.compose.renderer import CONVERTERS, RendererNotFound, compose, to_html
from app.models.template import Template


def _make_jinja_env():
    return JinjaEnv(loader=DictLoader({}), autoescape=select_autoescape(["html", "xml"]))


class TestRenderer:
    @pytest.mark.parametrize("mime_type", [
        "application/pdf",
        "text/html",
    ])
    def test_converters_registered(self, mime_type):
        assert mime_type in CONVERTERS

    def test_compose_renderer_not_found(self):
        template = Template(id_="test_template", schema={}, type_="text/html",
                            tags=[], metadata={}, example_composition={})

        jinja_env = _make_jinja_env()
        with pytest.raises(RendererNotFound):
            compose(template, {}, "application/unsupported-mime-type", jinja_env)

    def test_to_html(self):
        assert to_html("<p>hello</p>") == b"<p>hello</p>"

    @pytest.mark.parametrize("mime_type", [
        "application/pdf",
        "text/html",
    ])
    def test_compose_invalid_data(self, mime_type):
        schema = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}
        template = template = Template(id_="test_template", schema=schema, type_="text/html",
                                       tags=[], metadata={}, example_composition={})

        jinja_env = _make_jinja_env()
        with pytest.raises(ValidationError):
            compose(template, {}, mime_type, jinja_env)
