"""
world_events.py — Мировые события: Аномалии эмоций, Кристаллическая буря.

Аномалии:
- Появляются в локациях на 6-24 часа
- Усиливают монстров соответствующей эмоции
- Повышают шанс редких встреч
- Дестабилизируют кристаллы

Кристаллическая буря:
- Раз в 3-7 дней случайное событие
- Повышает шанс редких кристаллов при встречах
- Снижает стабильность призванных монстров
- Даёт особые ресурсы при победе в бою
"""
import random
import time
from database.repositories import get_connection

# ── Типы аномалий ─────────────────────────────────────────────────────────────

ANOMALY_TYPES = {
    "rage": {
        "name": "🔥 Аномалия Ярости",
        "desc": "Монстры ярости сильнее. Враги агрессивнее. Редкие встречи чаще.",
        "monster_bonus": {"rage": 1.20},
        "rare_chance_bonus": 0.10,
        "crystal_destab": 0.15,
        "eligible_locations": ["volcano_wrath", "stone_hills", "dark_forest"],
    },
    "fear": {
        "name": "😱 Аномалия Страха",
        "desc": "Монстры страха появляются из теней. Туман скрывает опасность.",
        "monster_bonus": {"fear": 1.15},
        "rare_chance_bonus": 0.08,
        "crystal_destab": 0.10,
        "eligible_locations": ["shadow_marsh", "shadow_swamp", "ancient_ruins"],
    },
    "sadness": {
        "name": "💧 Аномалия Скорби",
        "desc": "Тихие монстры становятся сильнее в этой тоскливой зоне.",
        "monster_bonus": {"sadness": 1.12},
        "rare_chance_bonus": 0.07,
        "crystal_destab": 0.08,
        "eligible_locations": ["shadow_swamp", "bone_desert", "ancient_ruins"],
    },
    "chaos": {
        "name": "🌀 Аномалия Хаоса",
        "desc": "Все эмоции смешаны. Монстры непредсказуемы. Опасность повсюду.",
        "monster_bonus": {"rage": 1.10, "fear": 1.10, "instinct": 1.10},
        "rare_chance_bonus": 0.15,
        "crystal_destab": 0.20,
        "eligible_locations": ["emotion_rift", "storm_ridge", "volcano_wrath"],
    },
}

CRYSTAL_STORM = {
    "name": "💎 Кристаллическая буря",
    "desc": "Редкие кристаллы выходят на поверхность. Монстры нестабильны.",
    "rare_crystal_bonus": 0.25,
    "monster_instability": 0.15,
    "special_drop": "storm_crystal_shard",
    "duration_hours": 12,
}


def _ensure_events_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS world_events (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type   TEXT NOT NULL,
                event_subtype TEXT,
                location_slug TEXT,
                started_at   INTEGER NOT NULL,
                ends_at      INTEGER NOT NULL,
                is_active    INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.commit()


_events_ok = False
def _lazy():
    global _events_ok
    if not _events_ok:
        _ensure_events_tables()
        _events_ok = True


# ── Управление событиями ──────────────────────────────────────────────────────

def get_active_events() -> list[dict]:
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM world_events WHERE is_active=1 AND ends_at > ? ORDER BY started_at DESC",
            (now,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_location_anomaly(location_slug: str) -> dict | None:
    """Возвращает активную аномалию в локации или None."""
    events = get_active_events()
    for e in events:
        if e["event_type"] == "anomaly" and e["location_slug"] == location_slug:
            return {**e, "data": ANOMALY_TYPES.get(e["event_subtype"], {})}
    return None


def get_crystal_storm() -> dict | None:
    """Возвращает активную Кристаллическую бурю или None."""
    events = get_active_events()
    for e in events:
        if e["event_type"] == "crystal_storm":
            return e
    return None


def try_spawn_anomaly():
    """Случайно создаёт аномалию (вызывается из фонового цикла)."""
    _lazy()
    now = int(time.time())
    # Не более 2 аномалий одновременно
    active = get_active_events()
    current_anomalies = [e for e in active if e["event_type"] == "anomaly"]
    if len(current_anomalies) >= 2:
        return None

    # 15% шанс при вызове
    if random.random() > 0.15:
        return None

    atype = random.choice(list(ANOMALY_TYPES.keys()))
    adata = ANOMALY_TYPES[atype]
    location = random.choice(adata["eligible_locations"])
    duration = random.randint(6, 24) * 3600

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO world_events
            (event_type, event_subtype, location_slug, started_at, ends_at, is_active)
            VALUES (?,?,?,?,?,1)
        """, ("anomaly", atype, location, now, now + duration))
        conn.commit()

    return {"type": atype, "location": location, "duration_h": duration // 3600}


def try_spawn_crystal_storm():
    """Создаёт Кристаллическую бурю (раз в 3-7 дней)."""
    _lazy()
    now = int(time.time())
    active = get_active_events()
    if any(e["event_type"] == "crystal_storm" for e in active):
        return None

    # Проверяем когда была последняя буря
    with get_connection() as conn:
        last = conn.execute(
            "SELECT ends_at FROM world_events WHERE event_type='crystal_storm' ORDER BY ends_at DESC LIMIT 1"
        ).fetchone()

    min_interval = 3 * 86400  # минимум 3 дня
    if last and (now - last["ends_at"]) < min_interval:
        return None

    if random.random() > 0.05:  # 5% шанс при вызове (раз в 30 сек = ~раз в 10 мин)
        return None

    duration = CRYSTAL_STORM["duration_hours"] * 3600
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO world_events
            (event_type, started_at, ends_at, is_active)
            VALUES (?,?,?,1)
        """, ("crystal_storm", now, now + duration))
        conn.commit()
    return True


def expire_old_events():
    """Деактивирует истёкшие события."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        conn.execute(
            "UPDATE world_events SET is_active=0 WHERE ends_at <= ? AND is_active=1",
            (now,)
        )
        conn.commit()


# ── Применение бонусов ────────────────────────────────────────────────────────

def get_location_event_bonuses(location_slug: str) -> dict:
    """Возвращает боевые бонусы от событий в локации."""
    bonuses = {
        "monster_multipliers": {},  # mood: multiplier
        "rare_chance_bonus": 0.0,
        "crystal_destab": 0.0,
        "crystal_storm_active": False,
        "storm_drop": False,
    }

    anomaly = get_location_anomaly(location_slug)
    if anomaly and anomaly.get("data"):
        data = anomaly["data"]
        bonuses["monster_multipliers"].update(data.get("monster_bonus", {}))
        bonuses["rare_chance_bonus"] += data.get("rare_chance_bonus", 0.0)
        bonuses["crystal_destab"] += data.get("crystal_destab", 0.0)

    storm = get_crystal_storm()
    if storm:
        bonuses["crystal_storm_active"] = True
        bonuses["rare_chance_bonus"] += CRYSTAL_STORM["rare_crystal_bonus"]
        bonuses["storm_drop"] = random.random() < 0.20  # 20% на особый дроп

    return bonuses


def render_active_events() -> str:
    """Текст активных мировых событий для показа игроку."""
    events = get_active_events()
    if not events:
        return ""
    lines = []
    now = int(time.time())
    for e in events:
        remaining = max(0, e["ends_at"] - now)
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        time_str = f"{hours}ч {mins}м" if hours else f"{mins}м"
        if e["event_type"] == "anomaly":
            adata = ANOMALY_TYPES.get(e["event_subtype"], {})
            lines.append(f"{adata.get('name','Аномалия')} в {e['location_slug']} ({time_str})")
        elif e["event_type"] == "crystal_storm":
            lines.append(f"{CRYSTAL_STORM['name']} ({time_str})")
    return "🌍 " + " | ".join(lines) if lines else ""
