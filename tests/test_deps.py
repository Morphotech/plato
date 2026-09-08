from contextlib import contextmanager
from unittest import mock
from unittest.mock import MagicMock

import pytest
from jinja2 import Environment as JinjaEnv, FileSystemLoader

from app.deps import get_db, get_jinja_env
from app.settings import get_settings


class TestDependencies:
    def test_get_db_yields_and_closes_session(self):
        fake_session = MagicMock()
        exited = False

        @contextmanager
        def fake_db_session():
            nonlocal exited
            yield fake_session
            exited = True

        with mock.patch("app.deps.db_session", fake_db_session):
            generator = get_db()
            db = next(generator)

            assert db is fake_session
            assert exited is False

            with pytest.raises(StopIteration):
                next(generator)

        assert exited is True

    def test_get_jinja_env_returns_configured_environment(self):
        env = get_jinja_env()

        assert isinstance(env, JinjaEnv)
        assert isinstance(env.loader, FileSystemLoader)

    def test_get_jinja_env_is_cached(self):
        get_jinja_env.cache_clear()

        with mock.patch("app.deps.create_template_environment") as mock_create_env:
            mock_create_env.return_value = JinjaEnv()

            first = get_jinja_env()
            second = get_jinja_env()

        mock_create_env.assert_called_once_with(get_settings().TEMPLATE_DIRECTORY)
        assert first is second

