"""
notification_service.py — Внутриигровые уведомления и рассылки.
"""
import time
from database.repositories import get_connection
from game.analytics_service import _lazy as _analytics_lazy, log_admin_action


def _lazy():
    _analytics_lazy()  # tables are created there


# ── Уведомления игрока ────────────────────────────────────────────────────────

def create_notification(telegram_id: int, title: str, text: str,
                        notif_type: str = "news", expires_days: int = 30) -> int:
    """Создаёт уведомление для конкретного игрока."""
    _lazy()
    now = int(time.time())
    expires = now + expires_days * 86400
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO player_notifications
            (telegram_id, type, title, text, is_read, created_at, expires_at)
            VALUES (?,?,?,?,0,?,?)
        """, (telegram_id, notif_type, title, text, now, expires))
        nid = cur.lastrowid
        conn.commit()
    return nid


def get_notifications(telegram_id: int, unread_only: bool = False) -> list[dict]:
    """Список уведомлений игрока."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        if unread_only:
            rows = conn.execute("""
                SELECT * FROM player_notifications
                WHERE telegram_id=? AND is_read=0
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC
            """, (telegram_id, now)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM player_notifications
                WHERE telegram_id=?
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC LIMIT 20
            """, (telegram_id, now)).fetchall()
    return [dict(r) for r in rows]


def get_unread_count(telegram_id: int) -> int:
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        return conn.execute("""
            SELECT COUNT(*) FROM player_notifications
            WHERE telegram_id=? AND is_read=0
            AND (expires_at IS NULL OR expires_at > ?)
        """, (telegram_id, now)).fetchone()[0]


def mark_read(notification_id: int, telegram_id: int):
    _lazy()
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_notifications SET is_read=1 WHERE id=? AND telegram_id=?",
            (notification_id, telegram_id)
        )
        conn.commit()


def mark_all_read(telegram_id: int):
    _lazy()
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_notifications SET is_read=1 WHERE telegram_id=?",
            (telegram_id,)
        )
        conn.commit()


# ── Сегменты для рассылки ─────────────────────────────────────────────────────

SEGMENT_LABELS = {
    "all":           "👥 Всем игрокам",
    "online_30m":    "🟢 Онлайн (30 мин)",
    "inactive_3d":   "💤 Не заходили 3+ дней",
    "inactive_7d":   "💤 Не заходили 7+ дней",
    "inactive_14d":  "💤 Не заходили 14+ дней",
    "level_1_5":     "📊 Уровни 1–5",
    "level_6_10":    "📊 Уровни 6–10",
    "level_10plus":  "📊 Уровни 10+",
    "no_monsters":   "🐲 Без монстров",
    "low_gold":      "💰 Мало золота (<50)",
    "new_7d":        "🆕 Новички (7 дней)",
}


def get_segment_players(segment: str, param: str = None) -> list[int]:
    """Возвращает telegram_id игроков по сегменту."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        if segment == "all":
            rows = conn.execute("SELECT telegram_id FROM players WHERE is_banned=0").fetchall()
        elif segment == "online_30m":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE last_active_at >= ? AND is_banned=0",
                (now - 1800,)
            ).fetchall()
        elif segment == "inactive_3d":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE (last_active_at IS NULL OR last_active_at < ?) AND is_banned=0",
                (now - 259200,)
            ).fetchall()
        elif segment == "inactive_7d":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE (last_active_at IS NULL OR last_active_at < ?) AND is_banned=0",
                (now - 604800,)
            ).fetchall()
        elif segment == "inactive_14d":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE (last_active_at IS NULL OR last_active_at < ?) AND is_banned=0",
                (now - 1209600,)
            ).fetchall()
        elif segment == "level_1_5":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE level BETWEEN 1 AND 5 AND is_banned=0"
            ).fetchall()
        elif segment == "level_6_10":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE level BETWEEN 6 AND 10 AND is_banned=0"
            ).fetchall()
        elif segment == "level_10plus":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE level >= 10 AND is_banned=0"
            ).fetchall()
        elif segment == "no_monsters":
            rows = conn.execute("""
                SELECT p.telegram_id FROM players p
                LEFT JOIN player_monsters m ON p.telegram_id=m.telegram_id AND m.is_active=1
                WHERE m.telegram_id IS NULL AND p.is_banned=0
            """).fetchall()
        elif segment == "low_gold":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE gold < 50 AND is_banned=0"
            ).fetchall()
        elif segment == "new_7d":
            rows = conn.execute(
                "SELECT telegram_id FROM players WHERE created_at_ts >= ? AND is_banned=0",
                (now - 604800,)
            ).fetchall()
        else:
            rows = []

    return [r["telegram_id"] for r in rows]


# ── Создание и отправка объявлений ────────────────────────────────────────────

def create_announcement(admin_id: int, title: str, text: str,
                        segment: str = "all") -> dict:
    """Создаёт глобальное объявление."""
    _lazy()
    now = int(time.time())
    players = get_segment_players(segment)
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO global_announcements
            (title, text, segment_type, created_by, created_at, is_active, sent_count)
            VALUES (?,?,?,?,?,1,0)
        """, (title, text, segment, admin_id, now))
        ann_id = cur.lastrowid
        conn.commit()

    log_admin_action(admin_id, "create_announcement", "announcement", ann_id,
                     f"segment={segment} players={len(players)}")
    return {"id": ann_id, "title": title, "segment": segment, "players_count": len(players)}


def send_announcement(ann_id: int, bot=None) -> int:
    """
    Отправляет объявление всем игрокам сегмента.
    Создаёт уведомления в player_notifications.
    Возвращает количество отправленных.
    """
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        ann = conn.execute(
            "SELECT * FROM global_announcements WHERE id=? AND is_active=1",
            (ann_id,)
        ).fetchone()
    if not ann:
        return 0

    ann = dict(ann)
    players = get_segment_players(ann["segment_type"])
    sent = 0

    with get_connection() as conn:
        for uid in players:
            # Проверяем не отправляли ли уже
            exists = conn.execute(
                "SELECT id FROM broadcast_log WHERE announcement_id=? AND telegram_id=?",
                (ann_id, uid)
            ).fetchone()
            if exists:
                continue
            # Создаём уведомление
            conn.execute("""
                INSERT INTO player_notifications
                (telegram_id, type, title, text, is_read, created_at)
                VALUES (?,?,?,?,0,?)
            """, (uid, "news", ann["title"], ann["text"], now))
            # Лог доставки
            conn.execute("""
                INSERT INTO broadcast_log (announcement_id, telegram_id, delivered_at)
                VALUES (?,?,?)
            """, (ann_id, uid, now))
            sent += 1
        conn.execute(
            "UPDATE global_announcements SET sent_count=sent_count+? WHERE id=?",
            (sent, ann_id)
        )
        conn.commit()

    return sent


def get_announcements(limit: int = 10) -> list[dict]:
    _lazy()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM global_announcements ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Отображение уведомлений игрока ───────────────────────────────────────────

def render_notifications(telegram_id: int) -> str:
    notifs = get_notifications(telegram_id)
    if not notifs:
        return "🔔 Нет уведомлений."
    lines = [f"🔔 Уведомления ({len(notifs)})\n"]
    for n in notifs:
        read_icon = "🔵" if not n["is_read"] else "⚪"
        import datetime
        dt = datetime.datetime.fromtimestamp(n["created_at"]).strftime("%d.%m %H:%M")
        lines.append(f"{read_icon} [{dt}] {n['title']}\n  {n['text'][:80]}{'...' if len(n['text'])>80 else ''}")
    return "\n\n".join(lines)
