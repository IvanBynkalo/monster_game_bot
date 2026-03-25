import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"
EVENT_LOG_FILE = LOG_DIR / "events.log"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)

    app_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(log_format)

    error_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)

    logger.addHandler(console_handler)
    logger.addHandler(app_handler)
    logger.addHandler(error_handler)

    # Отдельный логгер игровых событий
    events_logger = logging.getLogger("game_events")
    events_logger.setLevel(logging.INFO)
    events_logger.propagate = False

    if not events_logger.handlers:
        events_handler = RotatingFileHandler(
            EVENT_LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        events_handler.setLevel(logging.INFO)
        events_handler.setFormatter(log_format)
        events_logger.addHandler(events_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_events_logger() -> logging.Logger:
    return logging.getLogger("game_events")
