from app.log_config import configure_logging

configure_logging()

from app.fastapi_app import get_app  # noqa: E402

app = get_app()
