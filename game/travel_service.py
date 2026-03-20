"""
travel_service.py — Система перемещения между локациями.

Механика:
- У каждого перехода есть расстояние в у.е. (условных единицах)
- Базовое время: расстояние × 60 секунд
- Ловкость героя сокращает время: каждые 5 очков ловкости = −10% времени
- Во время перехода герой «в пути» — нельзя исследовать/сражаться
- По прибытии — push-уведомление
"""
import time
from database.repositories import get_connection

# Расстояния между локациями (симметричные)
# Единица ≈ 1 минута базового времени
DISTANCES: dict[tuple[str, str], int] = {
    ("silver_city",    "dark_forest"):    3,
    ("dark_forest",    "emerald_fields"): 5,
    ("dark_forest",    "shadow_marsh"):   7,
    ("dark_forest",    "ancient_ruins"):  8,
    ("emerald_fields", "stone_hills"):    6,
    ("emerald_fields", "shadow_swamp"):   9,
    ("stone_hills",    "volcano_wrath"):  12,
    ("stone_hills",    "bone_desert"):    10,
    ("shadow_marsh",   "shadow_swamp"):   4,
    ("shadow_swamp",   "volcano_wrath"):  11,
    ("bone_desert",    "storm_ridge"):    8,
    ("volcano_wrath",  "emotion_rift"):   15,
    ("storm_ridge",    "emotion_rift"):   10,
}

LOCATION_NAMES = {
    "silver_city":    "🏙 Сереброград",
    "dark_forest":    "🌲 Тёмный лес",
    "emerald_fields": "🌿 Изумрудные поля",
    "stone_hills":    "⛰ Каменные холмы",
    "shadow_marsh":   "🕸 Болота теней",
    "shadow_swamp":   "🌫 Болото теней",
    "ancient_ruins":  "🏛 Древние руины",
    "bone_desert":    "🏜 Пустыня костей",
    "volcano_wrath":  "🔥 Вулкан ярости",
    "storm_ridge":    "🏔 Хребет бурь",
    "emotion_rift":   "🌌 Разлом эмоций",
}


def get_distance(from_slug: str, to_slug: str) -> int:
    """Возвращает расстояние между локациями в у.е."""
    key = (from_slug, to_slug)
    rev = (to_slug, from_slug)
    return DISTANCES.get(key) or DISTANCES.get(rev) or 5


def get_travel_seconds(from_slug: str, to_slug: str, agility: int = 0) -> int:
    """
    Время перехода в секундах.
    Базовое: расстояние × 60 сек.
    Ловкость: каждые 5 очков = −10%, максимум −70%.
    """
    distance = get_distance(from_slug, to_slug)
    base_seconds = distance * 60
    agility_discount = min(0.70, (agility // 5) * 0.10)
    return max(10, int(base_seconds * (1 - agility_discount)))


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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_travel (
                telegram_id   INTEGER PRIMARY KEY,
                from_slug     TEXT NOT NULL,
                to_slug       TEXT NOT NULL,
                arrive_at     INTEGER NOT NULL,
                notified      INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()


_travel_table_ok = False
def _lazy():
    global _travel_table_ok
    if not _travel_table_ok:
        _ensure_travel_table()
        _travel_table_ok = True


def start_travel(telegram_id: int, from_slug: str, to_slug: str, agility: int = 0) -> dict:
    """Начинает переход. Возвращает данные о путешествии."""
    _lazy()
    seconds = get_travel_seconds(from_slug, to_slug, agility)
    arrive_at = int(time.time()) + seconds
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO player_travel
            (telegram_id, from_slug, to_slug, arrive_at, notified)
            VALUES (?,?,?,?,0)
        """, (telegram_id, from_slug, to_slug, arrive_at))
        conn.commit()
    return {
        "from_slug": from_slug,
        "to_slug": to_slug,
        "seconds": seconds,
        "arrive_at": arrive_at,
        "time_text": format_travel_time(seconds),
    }


def get_travel(telegram_id: int) -> dict | None:
    """Возвращает текущее путешествие или None если не в пути."""
    _lazy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_travel WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()
    if not row:
        return None
    return dict(row)


def is_traveling(telegram_id: int) -> bool:
    """Герой в пути прямо сейчас?"""
    travel = get_travel(telegram_id)
    if not travel:
        return False
    return int(time.time()) < travel["arrive_at"]


def check_arrival(telegram_id: int) -> dict | None:
    """
    Проверяет прибытие. Если прибыл — обновляет локацию и удаляет запись.
    Возвращает данные о прибытии или None.
    """
    _lazy()
    travel = get_travel(telegram_id)
    if not travel:
        return None
    if int(time.time()) < travel["arrive_at"]:
        # Ещё в пути
        remaining = travel["arrive_at"] - int(time.time())
        return {"in_progress": True, "remaining": remaining,
                "to_slug": travel["to_slug"], "travel": travel}
    # Прибыл
    from database.repositories import update_player_location
    update_player_location(telegram_id, travel["to_slug"])
    with get_connection() as conn:
        conn.execute("DELETE FROM player_travel WHERE telegram_id=?", (telegram_id,))
        conn.commit()
    return {"arrived": True, "to_slug": travel["to_slug"],
            "from_slug": travel["from_slug"]}


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
    """Все путешествия которые завершились но не были уведомлены."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM player_travel WHERE arrive_at <= ? AND notified = 0",
            (now,)
        ).fetchall()
    return [dict(r) for r in rows]


def mark_notified(telegram_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_travel SET notified=1 WHERE telegram_id=?",
            (telegram_id,)
        )
        conn.commit()
