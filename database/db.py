import json
import sqlite3
from pathlib import Path

import os

# DB_PATH читается из переменной окружения DATABASE_URL или DATABASE_PATH
# Это позволяет хранить БД на постоянном томе (Railway Volume, VPS и т.д.)
# Если переменная не задана — используем локальный путь (для разработки)
_db_env = os.environ.get("DATABASE_PATH") or os.environ.get("DATABASE_URL")

if _db_env and not _db_env.startswith("postgresql"):
    # Абсолютный путь из переменной окружения
    DB_PATH = Path(_db_env)
else:
    # Дефолтный путь внутри проекта (только для локальной разработки!)
    DB_PATH = Path(__file__).resolve().parent.parent / "data" / "game.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def json_get(val) -> dict | list:
    if val is None:
        return {}
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return {}


def json_set(val) -> str:
    return json.dumps(val, ensure_ascii=False)
