"""
error_tracker.py — Система логирования ошибок игры.

Собирает:
- Несработавшие кнопки (callback без обработчика)
- Исключения в хендлерах
- Логические ошибки (нет монстра, нет кристалла и т.д.)
- Warnings (deprecated пути, fallback-ы)

Хранится в SQLite, сбрасывается командой /errors_clear.
Просмотр через /errors (только для админов).
"""
import time
import traceback
from database.repositories import get_connection


def _ensure_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS error_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type  TEXT NOT NULL,
                context     TEXT NOT NULL,
                detail      TEXT,
                user_id     INTEGER,
                count       INTEGER NOT NULL DEFAULT 1,
                first_seen  INTEGER NOT NULL,
                last_seen   INTEGER NOT NULL,
                resolved    INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS error_log_meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()


_ok = False
def _lazy():
    global _ok
    if not _ok:
        _ensure_table()
        _ok = True


# ── Типы ошибок ───────────────────────────────────────────────────────────────

class ErrType:
    CALLBACK    = "callback_unhandled"   # кнопка без обработчика
    EXCEPTION   = "exception"            # исключение в хендлере
    LOGIC       = "logic_error"          # логическая ошибка (нет данных)
    WARNING     = "warning"              # предупреждение / fallback
    IMPORT_ERR  = "import_error"         # ошибка импорта модуля


# ── Запись ошибки ─────────────────────────────────────────────────────────────

def log_error(error_type: str, context: str, detail: str = None,
              user_id: int = None):
    """
    Записывает ошибку. Если такая же (тип+контекст) уже есть — 
    увеличивает счётчик и обновляет last_seen.
    """
    try:
        _lazy()
        now = int(time.time())
        with get_connection() as conn:
            existing = conn.execute("""
                SELECT id, count FROM error_log
                WHERE error_type=? AND context=? AND resolved=0
            """, (error_type, context)).fetchone()

            if existing:
                conn.execute("""
                    UPDATE error_log
                    SET count=count+1, last_seen=?,
                        detail=COALESCE(?, detail),
                        user_id=COALESCE(?, user_id)
                    WHERE id=?
                """, (now, detail, user_id, existing["id"]))
            else:
                conn.execute("""
                    INSERT INTO error_log
                    (error_type, context, detail, user_id, count, first_seen, last_seen)
                    VALUES (?,?,?,?,1,?,?)
                """, (error_type, context, detail, user_id, now, now))
            conn.commit()
    except Exception:
        pass  # никогда не падаем из-за логгера


def log_callback_error(callback_data: str, user_id: int = None):
    """Несработавшая inline-кнопка."""
    log_error(ErrType.CALLBACK, f"callback:{callback_data}",
              f"Кнопка без обработчика: {callback_data}", user_id)


def log_exception(context: str, exc: Exception, user_id: int = None):
    """Исключение в хендлере."""
    tb = traceback.format_exc()[-500:]  # последние 500 символов traceback
    log_error(ErrType.EXCEPTION, f"exc:{context}",
              f"{type(exc).__name__}: {exc}\n{tb}", user_id)


def log_logic_error(context: str, detail: str, user_id: int = None):
    """Логическая ошибка (нет монстра, нет кристалла и т.д.)."""
    log_error(ErrType.LOGIC, f"logic:{context}", detail, user_id)


def log_warning(context: str, detail: str, user_id: int = None):
    """Предупреждение / использован fallback."""
    log_error(ErrType.WARNING, f"warn:{context}", detail, user_id)


# ── Получение ошибок ──────────────────────────────────────────────────────────

def get_errors(limit: int = 30, error_type: str = None,
               resolved: bool = False) -> list[dict]:
    _lazy()
    with get_connection() as conn:
        if error_type:
            rows = conn.execute("""
                SELECT * FROM error_log
                WHERE resolved=? AND error_type=?
                ORDER BY last_seen DESC LIMIT ?
            """, (1 if resolved else 0, error_type, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM error_log
                WHERE resolved=?
                ORDER BY count DESC, last_seen DESC LIMIT ?
            """, (1 if resolved else 0, limit)).fetchall()
    return [dict(r) for r in rows]


def get_error_summary() -> dict:
    _lazy()
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*), SUM(count) FROM error_log WHERE resolved=0"
        ).fetchone()
        by_type = conn.execute("""
            SELECT error_type, COUNT(*) as unique_count, SUM(count) as total_count
            FROM error_log WHERE resolved=0
            GROUP BY error_type ORDER BY total_count DESC
        """).fetchall()
    return {
        "unique_errors": total[0] or 0,
        "total_occurrences": total[1] or 0,
        "by_type": [dict(r) for r in by_type],
    }


def mark_resolved(error_id: int = None, all_errors: bool = False):
    """Помечает ошибки как решённые (сброс)."""
    _lazy()
    with get_connection() as conn:
        if all_errors:
            conn.execute("UPDATE error_log SET resolved=1")
            # Запоминаем версию/время сброса
            conn.execute("""
                INSERT OR REPLACE INTO error_log_meta (key, value)
                VALUES ('last_clear', ?)
            """, (str(int(time.time())),))
        elif error_id:
            conn.execute("UPDATE error_log SET resolved=1 WHERE id=?", (error_id,))
        conn.commit()


def get_last_clear_time() -> int | None:
    _lazy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM error_log_meta WHERE key='last_clear'"
        ).fetchone()
    return int(row["value"]) if row else None


# ── Рендер ────────────────────────────────────────────────────────────────────

TYPE_ICONS = {
    ErrType.CALLBACK:   "🔘",
    ErrType.EXCEPTION:  "💥",
    ErrType.LOGIC:      "⚙️",
    ErrType.WARNING:    "⚠️",
    ErrType.IMPORT_ERR: "📦",
}

def render_errors(limit: int = 20) -> str:
    summary = get_error_summary()
    errors = get_errors(limit=limit)

    if not errors:
        last_clear = get_last_clear_time()
        if last_clear:
            import datetime
            dt = datetime.datetime.fromtimestamp(last_clear).strftime("%d.%m %H:%M")
            return f"✅ Ошибок нет.\nПоследний сброс: {dt}"
        return "✅ Ошибок нет."

    import datetime
    lines = [
        f"🐛 Журнал ошибок\n",
        f"Уникальных: {summary['unique_errors']} | "
        f"Всего вхождений: {summary['total_occurrences']}\n",
    ]

    # По типам
    for t in summary["by_type"]:
        icon = TYPE_ICONS.get(t["error_type"], "❓")
        lines.append(f"{icon} {t['error_type']}: {t['unique_count']} ун. / {t['total_count']} раз")
    lines.append("")

    # Топ ошибок
    lines.append("── Топ ошибок ──")
    for err in errors[:15]:
        icon = TYPE_ICONS.get(err["error_type"], "❓")
        dt = datetime.datetime.fromtimestamp(err["last_seen"]).strftime("%d.%m %H:%M")
        ctx = err["context"].replace("callback:", "").replace("exc:", "").replace("logic:", "").replace("warn:", "")
        detail_short = (err["detail"] or "")[:60].replace("\n", " ")
        uid_str = f" u:{err['user_id']}" if err.get("user_id") else ""
        lines.append(
            f"{icon} [{err['count']}x] {ctx}{uid_str}\n"
            f"   {detail_short}\n"
            f"   Последний: {dt} | ID:{err['id']}"
        )

    return "\n".join(lines)
