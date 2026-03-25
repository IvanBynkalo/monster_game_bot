from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Старые и новые файлы логов
LOG_FILE = LOG_DIR / "game.log"
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"
EVENT_LOG_FILE = LOG_DIR / "events.log"


def setup_logging() -> logging.Logger:
    """Единая настройка логирования для всего проекта.

    Совместима со старым кодом (через log_event) и с новым (через logging).
    Безопасно вызывается много раз.
    """
    root = logging.getLogger()
    if getattr(root, "_monster_game_logging_configured", False):
        return logging.getLogger(__name__)

    root.handlers.clear()
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    app_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(fmt)

    error_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(fmt)

    root.addHandler(console_handler)
    root.addHandler(app_handler)
    root.addHandler(error_handler)

    events_logger = logging.getLogger("game_events")
    events_logger.handlers.clear()
    events_logger.setLevel(logging.INFO)
    events_logger.propagate = False

    events_handler = RotatingFileHandler(
        EVENT_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    events_handler.setLevel(logging.INFO)
    events_handler.setFormatter(fmt)
    events_logger.addHandler(events_handler)

    root._monster_game_logging_configured = True
    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def get_events_logger() -> logging.Logger:
    setup_logging()
    return logging.getLogger("game_events")


def log_event(event_type: str, telegram_id: Optional[int] = None, details: str = "") -> None:
    """Совместимость со старым проектом.

    Пишет событие и в legacy game.log, и в новый events.log.
    Ничего не роняет даже если файловая запись не удалась.
    """
    timestamp = datetime.utcnow().isoformat()
    line = f"[{timestamp}] {event_type}"
    if telegram_id is not None:
        line += f" user={telegram_id}"
    if details:
        line += f" | {details}"

    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # Не мешаем игровой логике, просто пытаемся продублировать через logging
        pass

    try:
        setup_logging()
        logging.getLogger("game_events").info(line)
    except Exception:
        pass


def log_exception(context: str, exception: Exception, telegram_id: Optional[int] = None) -> None:
    """Удобная запись исключений в общий лог ошибок."""
    setup_logging()
    logger = logging.getLogger("exceptions")
    logger.exception(
        "EXCEPTION | context=%s | user_id=%s | error=%r",
        context,
        telegram_id,
        exception,
    )


def log_debug_event(event_type: str, details: str = "") -> None:
    """Вспомогательная функция для ручной диагностики."""
    setup_logging()
    logger = logging.getLogger("debug_events")
    logger.info("DEBUG_EVENT | type=%s | %s", event_type, details)
