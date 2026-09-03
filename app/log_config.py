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
            "console_formatter": {
                "format": "%(levelname)s %(asctime)s %(message)s",
            },
            "json_formatter": {
                "class": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console_formatter",
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
    Configure the "app" logger with a console handler (timestamp + level + message) and a rotating JSON file handler.
    Must be called once, as early as possible, in every process entry point (app/main.py, app/cli.py, etc) so log output
    is identical regardless of launcher (Docker, `fastapi dev`, PyCharm).
    """
    logging.config.dictConfig(_build_log_config())
