"""
travel_service.py — Система перемещения между локациями.

Текущий режим для разработки:
- Все переходы длятся фиксированно 5 секунд.
- Экран путешествия успевает показаться.
- Игрок не ждёт долго во время тестов.

Важно:
- Таблица расстояний оставлена на будущее.
- Позже можно легко вернуть "реальные" времена,
  если снова захочешь привязку к дистанции и ловкости.
"""

import time
from database.repositories import get_connection

# ──────────────────────────────────────────────────────────────────────────────
# Настройки времени переходов
# ──────────────────────────────────────────────────────────────────────────────

# Режим быстрой разработки:
# все переходы занимают ровно 5 секунд.
FIXED_TRAVEL_SECONDS = 5

# Если позже захочешь вернуть старую систему,
# можно поставить False и снова использовать DISTANCES + agility.
USE_FIXED_TRAVEL_TIME = True


# ──────────────────────────────────────────────────────────────────────────────
# Расстояния между локациями (сохранены на будущее)
# ──────────────────────────────────────────────────────────────────────────────

DISTANCES: dict[tuple[str, str], int] = {
    ("silver_city", "dark_forest"): 90,
    ("dark_forest", "emerald_fields"): 120,

    ("dark_forest", "shadow_marsh"): 180,
    ("emerald_fields", "stone_hills"): 180,
    ("shadow_marsh", "shadow_swamp"): 240,
    ("stone_hills", "ancient_ruins"): 240,

    ("shadow_swamp", "bone_desert"): 360,
    ("ancient_ruins", "bone_desert"): 360,

    ("bone_desert", "volcano_wrath"): 480,
    ("volcano_wrath", "storm_ridge"): 420,
    ("storm_ridge", "emotion_rift"): 600,
}

LOCATION_NAMES = {
    "silver_city": "🏙 Сереброград",
    "dark_forest": "🌲 Тёмный лес",
    "emerald_fields": "🌿 Изумрудные поля",
    "stone_hills": "⛰ Каменные холмы",
    "shadow_marsh": "🕸 Болота теней",
    "shadow_swamp": "🌫 Болото теней",
    "ancient_ruins": "🏛 Древние руины",
    "bone_desert": "🏜 Пустыня костей",
    "volcano_wrath": "🔥 Вулкан ярости",
    "storm_ridge": "🏔 Хребет бурь",
    "emotion_rift": "🌌 Разлом эмоций",
}


def get_distance(from_slug: str, to_slug: str) -> int:
    """Возвращает базовую дистанцию между локациями."""
    key = (from_slug, to_slug)
    rev = (to_slug, from_slug)
    return DISTANCES.get(key) or DISTANCES.get(rev) or FIXED_TRAVEL_SECONDS


def get_travel_seconds(from_slug: str, to_slug: str, agility: int = 0) -> int:
    """
    Возвращает время перехода в секундах.

    Текущий режим:
    - фиксированные 5 секунд для всех переходов.

    Резервный режим:
    - расчёт от дистанции и ловкости.
    """
    if USE_FIXED_TRAVEL_TIME:
        return FIXED_TRAVEL_SECONDS

    base_seconds = get_distance(from_slug, to_slug)
    agility_discount = min(0.70, (agility // 5) * 0.10)
    return max(4, int(base_seconds * (1 - agility_discount)))


def format_travel_time(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} сек."
    minutes = seconds // 60
    secs = seconds % 60
    if secs == 0:
        return f"{minutes} мин."
    return f"{minutes} мин. {secs} сек."


def _ensure_travel_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_travel (
                telegram_id   INTEGER PRIMARY KEY,
                from_slug     TEXT NOT NULL,
                to_slug       TEXT NOT NULL,
                arrive_at     INTEGER NOT NULL,
                notified      INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


_travel_table_ok = False


def _lazy():
    global _travel_table_ok
    if not _travel_table_ok:
        _ensure_travel_table()
        _travel_table_ok = True


def start_travel(
    telegram_id: int,
    from_slug: str,
    to_slug: str,
    agility: int = 0,
    extra_speed_bonus: float = 0.0,
) -> dict:
    """
    Начинает переход. Возвращает данные о путешествии.

    В режиме фиксированного времени бонусы скорости не применяются,
    чтобы переход всегда оставался равным 5 секундам.
    """
    _lazy()

    seconds = get_travel_seconds(from_slug, to_slug, agility)

    if not USE_FIXED_TRAVEL_TIME and extra_speed_bonus > 0:
        seconds = max(4, int(seconds * (1 - min(0.50, extra_speed_bonus))))

    arrive_at = int(time.time()) + seconds

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO player_travel
            (telegram_id, from_slug, to_slug, arrive_at, notified)
            VALUES (?,?,?,?,0)
            """,
            (telegram_id, from_slug, to_slug, arrive_at),
        )
        conn.commit()

    return {
        "from_slug": from_slug,
        "to_slug": to_slug,
        "seconds": seconds,
        "arrive_at": arrive_at,
        "time_text": format_travel_time(seconds),
    }


def get_travel(telegram_id: int) -> dict | None:
    """Возвращает текущее путешествие или None, если игрок не в пути."""
    _lazy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_travel WHERE telegram_id=?",
            (telegram_id,),
        ).fetchone()

    if not row:
        return None

    return dict(row)


def is_traveling(telegram_id: int) -> bool:
    """Игрок сейчас в пути?"""
    travel = get_travel(telegram_id)
    if not travel:
        return False
    return int(time.time()) < travel["arrive_at"]


def check_arrival(telegram_id: int) -> dict | None:
    """
    Проверяет прибытие.
    Если игрок прибыл — обновляет локацию и удаляет запись о путешествии.
    """
    _lazy()
    travel = get_travel(telegram_id)
    if not travel:
        return None

    now = int(time.time())
    if now < travel["arrive_at"]:
        remaining = travel["arrive_at"] - now
        return {
            "in_progress": True,
            "remaining": remaining,
            "to_slug": travel["to_slug"],
            "travel": travel,
        }

    from database.repositories import update_player_location

    update_player_location(telegram_id, travel["to_slug"])

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM player_travel WHERE telegram_id=?",
            (telegram_id,),
        )
        conn.commit()

    return {
        "arrived": True,
        "to_slug": travel["to_slug"],
        "from_slug": travel["from_slug"],
    }


def render_travel_status(travel: dict) -> str:
    """Текст статуса путешествия."""
    remaining = max(0, travel["arrive_at"] - int(time.time()))
    from_name = LOCATION_NAMES.get(travel["from_slug"], travel["from_slug"])
    to_name = LOCATION_NAMES.get(travel["to_slug"], travel["to_slug"])

    return (
        f"🚶 В пути: {from_name} → {to_name}\n"
        f"⏱ До прибытия: {format_travel_time(remaining)}"
    )


def get_pending_arrivals() -> list[dict]:
    """Все путешествия, которые завершились, но ещё не были уведомлены."""
    _lazy()
    now = int(time.time())

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM player_travel WHERE arrive_at <= ? AND notified = 0",
            (now,),
        ).fetchall()

    return [dict(r) for r in rows]


def mark_notified(telegram_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_travel SET notified=1 WHERE telegram_id=?",
            (telegram_id,),
        )
        conn.commit()
