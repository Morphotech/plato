import logging.config
from pathlib import Path
from typing import Any, Dict

from app.settings import get_settings

APP_LOGGER_NAME = "app"


def _build_log_config() -> Dict[str, Any]:
    settings = get_settings()

    log_file_path = Path(f"{settings.DATA_DIR}/logs/app.log")
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json_formatter": {
                "class": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "json_formatter",
                "level": settings.FILE_LOG_LEVEL,
                "filename": str(log_file_path),
                "when": "midnight",
                "backupCount": settings.LOG_DURATION_DAYS,
            },
        },
        "loggers": {
            APP_LOGGER_NAME: {
                "handlers": ["console", "file"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
        },
    }


def configure_logging() -> None:
    """
    Configure the "app" logger with a console handler (left at logging's
    default format — only the file output is structured) and a rotating
    JSON file handler. Must be called once, as early as possible, in every
    process entry point (app/main.py, app/cli.py) so log output is identical
    regardless of launcher (Docker, `fastapi dev`, PyCharm): uvicorn
    configures its own loggers before importing the app module, so this call
    always runs afterward and has the final say over the "app" logger's
    handlers.
    """
    logging.config.dictConfig(_build_log_config())
