from pythonjsonlogger.jsonlogger import JsonFormatter

from app.config import config


class RenameJsonFormatter(JsonFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            rename_fields={"asctime": "timestamp", "levelname": "severity"} | kwargs.get("rename_fields", {}),
            **kwargs,
        )


def logger_config(logger_name: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "class": "app.config.logger.RenameJsonFormatter",
                "format": "%(asctime)s %(name)s %(module)s %(funcName)s %(lineno)s %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            }
        },
        "handlers": {
            "console": {
                "formatter": "structured",
                "class": "picologging.StreamHandler",
                "level": config.LOG_LEVEL,
            },
        },
        "loggers": {
            "": {"level": config.LOG_LEVEL, "handlers": ["console"], "propagate": False},
        },
    }
