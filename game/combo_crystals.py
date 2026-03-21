"""
combo_crystals.py — Комбо-кристаллы: бонус за пару монстров одной эмоции/стихии.

Механика:
- Если в кристалле 2+ монстра одной эмоции → Эмоциональный резонанс (+8% ATK всем)
- Если 2+ монстра одной стихии → Стихийная синергия (+5% ATK, +1 защита)
- "Охотничья связка" (один ловец + один боевой) → +10% к шансу поимки
"""
from game.crystal_service import get_monsters_in_crystal, get_crystal


COMBO_BONUSES = {
    "emotion_resonance": {
        "name": "🎵 Эмоциональный резонанс",
        "condition": "2+ монстра одной эмоции",
        "atk_bonus": 0.08,
        "desc": "+8% ATK всем монстрам в кристалле",
    },
    "elemental_synergy": {
        "name": "⚡ Стихийная синергия",
        "condition": "2+ монстра одного типа",
        "atk_bonus": 0.05,
        "def_bonus": 1,
        "desc": "+5% ATK, +1 защита",
    },
    "hunters_bond": {
        "name": "🎯 Охотничья связка",
        "condition": "Монстр-охотник + боевой монстр",
        "capture_bonus": 0.10,
        "desc": "+10% к шансу поимки",
    },
}

HUNTER_MOODS = {"instinct", "inspiration"}
BATTLE_TYPES = {"flame", "storm", "bone", "void"}


def get_combo_bonuses(crystal_id: int) -> dict:
    """
    Анализирует монстров в кристалле и возвращает активные комбо-бонусы.
    Возвращает dict с суммарными модификаторами.
    """
    monsters = get_monsters_in_crystal(crystal_id)
    active = [m for m in monsters if not m.get("is_dead") and m.get("current_hp", 1) > 0]

    if len(active) < 2:
        return {"atk_bonus": 0.0, "def_bonus": 0, "capture_bonus": 0.0, "combos": []}

    bonuses = {"atk_bonus": 0.0, "def_bonus": 0, "capture_bonus": 0.0, "combos": []}

    # Эмоциональный резонанс
    from collections import Counter
    moods = Counter(m.get("mood", "instinct") for m in active)
    if moods.most_common(1)[0][1] >= 2:
        bonuses["atk_bonus"] += COMBO_BONUSES["emotion_resonance"]["atk_bonus"]
        bonuses["combos"].append(COMBO_BONUSES["emotion_resonance"]["name"])

    # Стихийная синергия
    types = Counter(m.get("monster_type", "void") for m in active)
    if types.most_common(1)[0][1] >= 2:
        bonuses["atk_bonus"] += COMBO_BONUSES["elemental_synergy"]["atk_bonus"]
        bonuses["def_bonus"] += COMBO_BONUSES["elemental_synergy"]["def_bonus"]
        bonuses["combos"].append(COMBO_BONUSES["elemental_synergy"]["name"])

    # Охотничья связка
    has_hunter = any(m.get("mood") in HUNTER_MOODS for m in active)
    has_battle = any(m.get("monster_type") in BATTLE_TYPES for m in active)
    if has_hunter and has_battle:
        bonuses["capture_bonus"] += COMBO_BONUSES["hunters_bond"]["capture_bonus"]
        bonuses["combos"].append(COMBO_BONUSES["hunters_bond"]["name"])

    return bonuses


def get_summoned_crystal_combos(telegram_id: int) -> dict:
    """
    Возвращает комбо-бонусы кристалла где находится активный (призванный) монстр.
    """
    from database.repositories import get_connection
    with get_connection() as conn:
        row = conn.execute(
            "SELECT crystal_id FROM player_monsters WHERE telegram_id=? AND is_summoned=1 LIMIT 1",
            (telegram_id,)
        ).fetchone()
    if not row or not row["crystal_id"]:
        return {"atk_bonus": 0.0, "def_bonus": 0, "capture_bonus": 0.0, "combos": []}
    return get_combo_bonuses(row["crystal_id"])


def render_combo_status(crystal_id: int) -> str:
    """Текст комбо-бонусов для показа в детале кристалла."""
    bonuses = get_combo_bonuses(crystal_id)
    if not bonuses["combos"]:
        return ""
    lines = ["\n✨ Активные комбо:"]
    for combo in bonuses["combos"]:
        lines.append(f"  {combo}")
    if bonuses["atk_bonus"]:
        lines.append(f"  → +{int(bonuses['atk_bonus']*100)}% ATK")
    if bonuses["capture_bonus"]:
        lines.append(f"  → +{int(bonuses['capture_bonus']*100)}% поимка")
    return "\n".join(lines)
