"""
bestiary_service.py — Бестиарий.

Бестиарий объединяет три раздела:
1. Монстры (эмоциональные существа) — из encounter_service
2. Звери (обычные животные) — из wildlife_service
3. Боссы подземелий — из dungeon_service

Логика регистрации:
- При каждой встрече вызывается register_bestiary_seen()
- Запись в таблице player_bestiary (telegram_id, creature_name, creature_type, count)
- В кодексе отображается что видел и сколько раз встречал
"""
from database.repositories import get_connection

# Все виды существ с данными для отображения
from game.wildlife_service import WILDLIFE_BY_LOCATION

LOCATION_NAMES = {
    "dark_forest":    "🌲 Тёмный лес",
    "emerald_fields": "🌿 Изумрудные поля",
    "stone_hills":    "⛰ Каменные холмы",
    "shadow_marsh":   "🕸 Болота теней",
    "shadow_swamp":   "🌫 Болото теней",
    "volcano_wrath":  "🔥 Вулкан ярости",
}

# Справочник всех зверей
BESTIARY_WILDLIFE: dict[str, dict] = {}
for _loc, _pool in WILDLIFE_BY_LOCATION.items():
    for _a in _pool:
        BESTIARY_WILDLIFE[_a["name"]] = {
            "type":     "wildlife",
            "location": _loc,
            "hp":       _a["hp"],
            "attack":   _a["attack"],
            "loot":     _a.get("loot"),
        }

# Трофейные реликвии за редких зверей (макс. вес 2 — самые редкие)
WILDLIFE_TROPHIES: dict[str, str] = {
    "Золотой орёл":       "golden_eagle_feather",
    "Лесной великан":     "forest_giant_claw",
    "Магматический кабан":"magma_tusk",
    "Болотный крокодил":  "swamp_croc_scale",
    "Горный лев":         "mountain_lion_fang",
    "Степной тур":        "ancient_horn",
}


# ── БД ────────────────────────────────────────────────────────────────────────

def register_bestiary_seen(telegram_id: int, name: str, creature_type: str = "wildlife"):
    """Записывает встречу с существом. creature_type: wildlife | monster | boss"""
    # Ленивая миграция — таблица создаётся при первом обращении
    from game.exploration_service import _lazy_ensure
    _lazy_ensure()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO player_bestiary (telegram_id, creature_name, creature_type, encounter_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(telegram_id, creature_name)
            DO UPDATE SET encounter_count = encounter_count + 1
        """, (telegram_id, name, creature_type))
        conn.commit()


def get_bestiary(telegram_id: int) -> dict[str, dict]:
    """Возвращает всё что видел игрок: {name: {type, count}}"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT creature_name, creature_type, encounter_count FROM player_bestiary WHERE telegram_id=?",
            (telegram_id,)
        ).fetchall()
    return {r["creature_name"]: {"type": r["creature_type"], "count": r["encounter_count"]} for r in rows}


def get_bestiary_count(telegram_id: int) -> dict:
    """Статистика: сколько видов открыто по типам."""
    seen = get_bestiary(telegram_id)
    return {
        "wildlife": sum(1 for v in seen.values() if v["type"] == "wildlife"),
        "monster":  sum(1 for v in seen.values() if v["type"] == "monster"),
        "boss":     sum(1 for v in seen.values() if v["type"] == "boss"),
        "total":    len(seen),
        "wildlife_total": len(BESTIARY_WILDLIFE),
    }


# ── Рендер ────────────────────────────────────────────────────────────────────

def render_bestiary(telegram_id: int, section: str = "wildlife") -> str:
    seen = get_bestiary(telegram_id)
    lines = []

    if section == "wildlife":
        lines.append("🐾 Бестиарий — Звери\n")
        by_location: dict[str, list] = {}
        for name, data in BESTIARY_WILDLIFE.items():
            loc = data["location"]
            by_location.setdefault(loc, []).append(name)

        for loc, animals in sorted(by_location.items()):
            loc_name = LOCATION_NAMES.get(loc, loc)
            lines.append(f"{loc_name}:")
            for name in sorted(animals):
                if name in seen:
                    count = seen[name]["count"]
                    trophy = "🏆" if name in WILDLIFE_TROPHIES else ""
                    lines.append(f"  ✅ {name} {trophy}— встречен {count}×")
                else:
                    lines.append(f"  ❓ ???")
            lines.append("")

    elif section == "monsters":
        lines.append("👾 Бестиарий — Монстры\n")
        monster_seen = {n: d for n, d in seen.items() if d["type"] == "monster"}
        if not monster_seen:
            lines.append("Ты ещё не встречал эмоциональных монстров.")
            lines.append("Исследуй локации чтобы встретить их — они редки.")
        else:
            for name, data in sorted(monster_seen.items()):
                lines.append(f"✅ {name} — встречен {data['count']}×")

    elif section == "bosses":
        lines.append("💀 Бестиарий — Боссы\n")
        boss_seen = {n: d for n, d in seen.items() if d["type"] == "boss"}
        if not boss_seen:
            lines.append("Ты ещё не встречал боссов подземелий.")
        else:
            for name, data in sorted(boss_seen.items()):
                lines.append(f"✅ {name} — повержен {data['count']}×")

    stats = get_bestiary_count(telegram_id)
    lines.append(
        f"📊 Открыто зверей: {stats['wildlife']}/{stats['wildlife_total']} | "
        f"Монстров: {stats['monster']} | Боссов: {stats['boss']}"
    )
    return "\n".join(lines)


def check_trophy_drop(creature_name: str) -> str | None:
    """Проверяет: падает ли трофей с этого зверя. Шанс 15%."""
    import random
    if creature_name in WILDLIFE_TROPHIES and random.random() < 0.15:
        return WILDLIFE_TROPHIES[creature_name]
    return None
