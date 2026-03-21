"""
crystal_heat.py — Перегретые кристаллы.

После тяжёлого боя кристалл накапливает "жар":
- Лёгкий бой: +0 жара
- Средний бой: +1 жара
- Тяжёлый бой (урон > 50% HP): +2 жара
- Поражение: +3 жара

Эффекты жара:
- 0-2: норма
- 3-4: "тёплый" — -5% ATK монстра
- 5-6: "горячий" — -10% ATK, +10% урона по монстру
- 7+: "перегрет" — нельзя использовать в бою

Охлаждение:
- Само по себе: -1 жара каждые 30 минут
- Ускоренное (у Геммы или с предметом "cooling_shard"): мгновенно
"""
import time
from database.repositories import get_connection


def _ensure_heat_table():
    with get_connection() as conn:
        # Добавляем heat_level к player_crystals если нет
        cols = [r[1] for r in conn.execute("PRAGMA table_info(player_crystals)").fetchall()]
        if "heat_level" not in cols:
            conn.execute("ALTER TABLE player_crystals ADD COLUMN heat_level INTEGER NOT NULL DEFAULT 0")
        if "last_cooled_at" not in cols:
            conn.execute("ALTER TABLE player_crystals ADD COLUMN last_cooled_at INTEGER DEFAULT NULL")
        conn.commit()


_heat_ok = False
def _lazy():
    global _heat_ok
    if not _heat_ok:
        _ensure_heat_table()
        _heat_ok = True


def _passive_cooling(crystal_id: int):
    """Применяет пассивное охлаждение (-1 каждые 30 мин)."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        row = conn.execute(
            "SELECT heat_level, last_cooled_at FROM player_crystals WHERE id=?",
            (crystal_id,)
        ).fetchone()
    if not row or row["heat_level"] <= 0:
        return
    last_cooled = row["last_cooled_at"] or now
    ticks = (now - last_cooled) // 1800  # каждые 30 мин
    if ticks <= 0:
        return
    new_heat = max(0, row["heat_level"] - ticks)
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET heat_level=?, last_cooled_at=? WHERE id=?",
            (new_heat, last_cooled + ticks * 1800, crystal_id)
        )
        conn.commit()


def get_heat_level(crystal_id: int) -> int:
    _lazy()
    _passive_cooling(crystal_id)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT heat_level FROM player_crystals WHERE id=?", (crystal_id,)
        ).fetchone()
    return row["heat_level"] if row else 0


def add_heat(crystal_id: int, amount: int):
    """Добавляет жар кристаллу."""
    _lazy()
    _passive_cooling(crystal_id)
    now = int(time.time())
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET heat_level=heat_level+?, last_cooled_at=COALESCE(last_cooled_at,?) WHERE id=?",
            (amount, now, crystal_id)
        )
        conn.commit()


def cool_crystal(telegram_id: int, crystal_id: int, gold: int = 0,
                 use_shard: bool = False) -> tuple[bool, str, int]:
    """Охлаждает кристалл мгновенно (у Геммы или с шардом)."""
    _lazy()
    from game.crystal_service import get_crystal
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден.", gold

    heat = get_heat_level(crystal_id)
    if heat == 0:
        return False, "Кристалл не перегрет.", gold

    if use_shard:
        from database.repositories import get_item_count, add_item
        if get_item_count(telegram_id, "cooling_shard") < 1:
            return False, "Нет Охлаждающего осколка.", gold
        add_item(telegram_id, "cooling_shard", -1)
        msg_end = "Потрачен: Охлаждающий осколок"
    else:
        cost = heat * 20  # 20з за единицу жара
        if gold < cost:
            return False, f"Нужно {cost}з (жар: {heat}).", gold
        gold -= cost
        msg_end = f"Потрачено: {cost}з"

    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET heat_level=0, last_cooled_at=? WHERE id=?",
            (int(time.time()), crystal_id)
        )
        conn.commit()
    return True, f"❄️ {crystal['name']} охлаждён! {msg_end}", gold


def get_heat_modifiers(crystal_id: int) -> dict:
    """Возвращает боевые модификаторы от жара."""
    heat = get_heat_level(crystal_id)
    if heat <= 2:
        return {"atk_penalty": 0.0, "dmg_bonus": 0.0, "blocked": False, "heat": heat, "status": "normal"}
    elif heat <= 4:
        return {"atk_penalty": 0.05, "dmg_bonus": 0.0, "blocked": False, "heat": heat, "status": "warm"}
    elif heat <= 6:
        return {"atk_penalty": 0.10, "dmg_bonus": 0.10, "blocked": False, "heat": heat, "status": "hot"}
    else:
        return {"atk_penalty": 0.0, "dmg_bonus": 0.0, "blocked": True, "heat": heat, "status": "overheated"}


HEAT_STATUS_LABELS = {
    "normal":     "",
    "warm":       "🌡 Тёплый (-5% ATK)",
    "hot":        "🔥 Горячий (-10% ATK, +10% урон по монстру)",
    "overheated": "♨️ ПЕРЕГРЕТ — нельзя использовать в бою!",
}


def calculate_battle_heat(monster_hp: int, max_hp: int, victory: bool) -> int:
    """Считает сколько жара добавить после боя."""
    hp_lost_pct = 1 - (monster_hp / max(1, max_hp))
    if not victory:
        return 3
    elif hp_lost_pct > 0.5:
        return 2
    elif hp_lost_pct > 0.2:
        return 1
    return 0
