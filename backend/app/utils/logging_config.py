"""
Centralized application logging configuration.
Does NOT log passwords, API keys, or OAuth tokens.
"""
import logging
import sys

from app.config.settings import settings


def setup_logging() -> None:
    level = logging.DEBUG if not settings.is_production else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if settings.is_production else logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)

    logging.getLogger(__name__).info(
        "Logging initialized. env=%s level=%s", settings.app_env, level
    )
