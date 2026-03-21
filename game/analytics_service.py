"""
analytics_service.py — Аналитика игры для админки.
"""
import time
from database.repositories import get_connection

# ── Lazy migration ────────────────────────────────────────────────────────────

def _ensure_analytics_tables():
    with get_connection() as conn:
        # Добавляем поля к players если нет
        cols = [r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()]
        if "last_active_at" not in cols:
            conn.execute("ALTER TABLE players ADD COLUMN last_active_at INTEGER DEFAULT NULL")
        if "created_at_ts" not in cols:
            conn.execute("ALTER TABLE players ADD COLUMN created_at_ts INTEGER DEFAULT NULL")
        if "is_banned" not in cols:
            conn.execute("ALTER TABLE players ADD COLUMN is_banned INTEGER NOT NULL DEFAULT 0")
        if "username" not in cols:
            conn.execute("ALTER TABLE players ADD COLUMN username TEXT DEFAULT NULL")

        # Таблица уведомлений игрока
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_notifications (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                type        TEXT NOT NULL DEFAULT 'news',
                title       TEXT NOT NULL,
                text        TEXT NOT NULL,
                payload     TEXT DEFAULT NULL,
                is_read     INTEGER NOT NULL DEFAULT 0,
                created_at  INTEGER NOT NULL,
                expires_at  INTEGER DEFAULT NULL
            )
        """)

        # Глобальные объявления
        conn.execute("""
            CREATE TABLE IF NOT EXISTS global_announcements (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                title         TEXT NOT NULL,
                text          TEXT NOT NULL,
                segment_type  TEXT NOT NULL DEFAULT 'all',
                segment_param TEXT DEFAULT NULL,
                created_by    INTEGER NOT NULL,
                created_at    INTEGER NOT NULL,
                starts_at     INTEGER DEFAULT NULL,
                ends_at       INTEGER DEFAULT NULL,
                is_active     INTEGER NOT NULL DEFAULT 1,
                sent_count    INTEGER NOT NULL DEFAULT 0
            )
        """)

        # Лог рассылок
        conn.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                announcement_id INTEGER NOT NULL,
                telegram_id     INTEGER NOT NULL,
                delivered_at    INTEGER NOT NULL,
                read_at         INTEGER DEFAULT NULL
            )
        """)

        # Лог действий админа
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id    INTEGER NOT NULL,
                action      TEXT NOT NULL,
                target_type TEXT DEFAULT NULL,
                target_id   INTEGER DEFAULT NULL,
                detail      TEXT DEFAULT NULL,
                created_at  INTEGER NOT NULL
            )
        """)
        conn.commit()


_analytics_ok = False
def _lazy():
    global _analytics_ok
    if not _analytics_ok:
        _ensure_analytics_tables()
        _analytics_ok = True


# ── Обновление активности ─────────────────────────────────────────────────────

def touch_player_activity(telegram_id: int, username: str = None):
    """Обновляет last_active_at при каждом действии игрока."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        if username:
            conn.execute(
                "UPDATE players SET last_active_at=?, username=? WHERE telegram_id=?",
                (now, username, telegram_id)
            )
        else:
            conn.execute(
                "UPDATE players SET last_active_at=? WHERE telegram_id=?",
                (now, telegram_id)
            )
        # Устанавливаем created_at_ts если не задан
        conn.execute(
            "UPDATE players SET created_at_ts=? WHERE telegram_id=? AND created_at_ts IS NULL",
            (now, telegram_id)
        )
        conn.commit()


# ── Метрики ───────────────────────────────────────────────────────────────────

def get_online_stats() -> dict:
    """Онлайн статистика."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        online_5m = conn.execute(
            "SELECT COUNT(*) FROM players WHERE last_active_at >= ?",
            (now - 300,)
        ).fetchone()[0]
        online_30m = conn.execute(
            "SELECT COUNT(*) FROM players WHERE last_active_at >= ?",
            (now - 1800,)
        ).fetchone()[0]
        online_24h = conn.execute(
            "SELECT COUNT(*) FROM players WHERE last_active_at >= ?",
            (now - 86400,)
        ).fetchone()[0]
        online_7d = conn.execute(
            "SELECT COUNT(*) FROM players WHERE last_active_at >= ?",
            (now - 604800,)
        ).fetchone()[0]
        new_today = conn.execute(
            "SELECT COUNT(*) FROM players WHERE created_at_ts >= ?",
            (now - 86400,)
        ).fetchone()[0]
        new_7d = conn.execute(
            "SELECT COUNT(*) FROM players WHERE created_at_ts >= ?",
            (now - 604800,)
        ).fetchone()[0]
        new_30d = conn.execute(
            "SELECT COUNT(*) FROM players WHERE created_at_ts >= ?",
            (now - 2592000,)
        ).fetchone()[0]

    return {
        "total": total,
        "online_5m": online_5m,
        "online_30m": online_30m,
        "online_24h": online_24h,
        "online_7d": online_7d,
        "new_today": new_today,
        "new_7d": new_7d,
        "new_30d": new_30d,
    }


def get_level_distribution() -> dict:
    """Распределение игроков по уровням."""
    _lazy()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT level, COUNT(*) as cnt FROM players GROUP BY level ORDER BY level"
        ).fetchall()

    dist = {"1-5": 0, "6-10": 0, "11-20": 0, "21-30": 0, "31+": 0}
    for row in rows:
        lvl, cnt = row["level"], row["cnt"]
        if lvl <= 5:    dist["1-5"] += cnt
        elif lvl <= 10: dist["6-10"] += cnt
        elif lvl <= 20: dist["11-20"] += cnt
        elif lvl <= 30: dist["21-30"] += cnt
        else:           dist["31+"] += cnt
    return dist


def get_inactive_players(days: int = 7, limit: int = 20, offset: int = 0) -> list[dict]:
    """Список игроков не заходивших N дней."""
    _lazy()
    threshold = int(time.time()) - days * 86400
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT telegram_id, name, username, level, gold,
                   last_active_at, location_slug
            FROM players
            WHERE (last_active_at IS NULL OR last_active_at < ?)
            AND is_banned = 0
            ORDER BY last_active_at DESC NULLS LAST
            LIMIT ? OFFSET ?
        """, (threshold, limit, offset)).fetchall()
    now = int(time.time())
    result = []
    for row in rows:
        d = dict(row)
        if d["last_active_at"]:
            d["days_absent"] = (now - d["last_active_at"]) // 86400
        else:
            d["days_absent"] = 999
        result.append(d)
    return result


def get_top_players(by: str = "level", limit: int = 10) -> list[dict]:
    """Топ игроков по параметру."""
    _lazy()
    field = {"level": "level", "gold": "gold", "experience": "experience"}.get(by, "level")
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT telegram_id, name, username, level, gold, experience "
            f"FROM players WHERE is_banned=0 ORDER BY {field} DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_new_players(limit: int = 10) -> list[dict]:
    """Последние зарегистрированные игроки."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT telegram_id, name, username, level, created_at_ts
            FROM players
            WHERE created_at_ts IS NOT NULL
            ORDER BY created_at_ts DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def render_analytics_text() -> str:
    """Текст для экрана аналитики в админке."""
    stats = get_online_stats()
    dist = get_level_distribution()
    return (
        f"📊 Аналитика игры\n\n"
        f"👥 Игроков всего: {stats['total']}\n"
        f"🟢 Онлайн сейчас: {stats['online_5m']}\n"
        f"🕐 За 30 минут: {stats['online_30m']}\n"
        f"📅 За 24 часа: {stats['online_24h']}\n"
        f"📆 За 7 дней: {stats['online_7d']}\n\n"
        f"🆕 Новых сегодня: {stats['new_today']}\n"
        f"🆕 За 7 дней: {stats['new_7d']}\n"
        f"🆕 За 30 дней: {stats['new_30d']}\n\n"
        f"📈 Распределение по уровням:\n"
        f"  1–5:   {dist['1-5']}\n"
        f"  6–10:  {dist['6-10']}\n"
        f"  11–20: {dist['11-20']}\n"
        f"  21–30: {dist['21-30']}\n"
        f"  31+:   {dist['31+']}"
    )


# ── Лог действий админа ───────────────────────────────────────────────────────

def log_admin_action(admin_id: int, action: str, target_type: str = None,
                     target_id: int = None, detail: str = None):
    _lazy()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO admin_log (admin_id, action, target_type, target_id, detail, created_at)
            VALUES (?,?,?,?,?,?)
        """, (admin_id, action, target_type, target_id, detail, int(time.time())))
        conn.commit()


def get_admin_log(limit: int = 20) -> list[dict]:
    _lazy()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM admin_log ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]
