"""
crystal_workshop.py — Мастерская кристаллов (NPC Гемма).

Услуги:
- Ремонт треснутых/разбитых кристаллов
- Улучшение вместимости (+1 объём за золото)
- Смена резонанса (эмоциональной аффинности)
- Раскрытие свойств редкого кристалла (идентификация)
- Скупка осколков (broken кристаллы → осколки → материалы)
"""
from database.repositories import get_connection, _update_player_field
from game.crystal_service import (
    get_crystal, get_player_crystals, CRYSTAL_TEMPLATES,
    recalculate_crystal_load,
)

NPC_NAME = "💎 Гемма"
NPC_DESC = "Мастер кристаллов. Чинит, улучшает и раскрывает тайны кристальных сосудов."

# ── Прайс-лист ────────────────────────────────────────────────────────────────

REPAIR_COSTS = {
    "common":    {"cracked": 40,  "broken": 80},
    "uncommon":  {"cracked": 70,  "broken": 140},
    "rare":      {"cracked": 120, "broken": 240},
    "epic":      {"cracked": 200, "broken": 400},
    "legendary": {"cracked": 350, "broken": 700},
}

UPGRADE_COSTS = {
    "common":    150,
    "uncommon":  250,
    "rare":      400,
    "epic":      700,
    "legendary": 1200,
}

RESONANCE_CHANGE_COST = 300  # смена аффинности

IDENTIFY_COST = 80  # раскрытие скрытых свойств

SHARD_BUY_PRICE = 15  # цена осколка от сломанного кристалла


# ── Услуги ────────────────────────────────────────────────────────────────────

def repair_crystal(telegram_id: int, crystal_id: int, gold: int) -> tuple[bool, str, int]:
    """Ремонт кристалла."""
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден.", gold
    if crystal["state"] == "normal":
        return False, "Кристалл в порядке.", gold

    costs = REPAIR_COSTS.get(crystal["rarity"], REPAIR_COSTS["common"])
    cost = costs.get(crystal["state"], 80)
    if gold < cost:
        return False, f"Нужно {cost}з. У тебя {gold}з", gold

    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET state='normal', crack_count=0 WHERE id=?",
            (crystal_id,)
        )
        conn.commit()
    return True, f"✅ {crystal['name']} восстановлен!", gold - cost


def upgrade_volume(telegram_id: int, crystal_id: int, gold: int) -> tuple[bool, str, int]:
    """Увеличивает max_volume кристалла на 1."""
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден.", gold
    if crystal["state"] != "normal":
        return False, "Сначала почини кристалл.", gold

    cost = UPGRADE_COSTS.get(crystal["rarity"], 200)
    max_upgrades = {"common": 3, "uncommon": 3, "rare": 4, "epic": 4, "legendary": 5}
    base_vol = CRYSTAL_TEMPLATES.get(crystal["template_code"], {}).get("max_volume", 5)
    if crystal["max_volume"] >= base_vol + max_upgrades.get(crystal["rarity"], 3):
        return False, "Достигнут максимум улучшений для этого кристалла.", gold

    if gold < cost:
        return False, f"Нужно {cost}з. У тебя {gold}з", gold

    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET max_volume=max_volume+1 WHERE id=?",
            (crystal_id,)
        )
        conn.commit()
    new_vol = crystal["max_volume"] + 1
    return True, f"✅ {crystal['name']}: объём {crystal['max_volume']} → {new_vol}", gold - cost


RESONANCE_OPTIONS = {
    "neutral":     "⚪ Нейтральный",
    "rage":        "🔥 Ярость",
    "joy":         "🌟 Радость",
    "fear":        "😱 Страх",
    "sadness":     "💧 Грусть",
    "instinct":    "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение",
}


def change_resonance(telegram_id: int, crystal_id: int,
                     new_affinity: str, gold: int) -> tuple[bool, str, int]:
    """Меняет эмоциональный резонанс кристалла."""
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден.", gold
    if crystal["state"] != "normal":
        return False, "Сначала почини кристалл.", gold
    if new_affinity not in RESONANCE_OPTIONS:
        return False, "Неизвестная аффинность.", gold
    if crystal["emotion_affinity"] == new_affinity:
        return False, "Кристалл уже имеет этот резонанс.", gold

    cost = RESONANCE_CHANGE_COST
    if gold < cost:
        return False, f"Нужно {cost}з. У тебя {gold}з", gold

    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET emotion_affinity=? WHERE id=?",
            (new_affinity, crystal_id)
        )
        conn.commit()
    label = RESONANCE_OPTIONS[new_affinity]
    return True, f"✅ Резонанс {crystal['name']} изменён на {label}!", gold - cost


def identify_crystal(telegram_id: int, crystal_id: int, gold: int) -> tuple[bool, str, int]:
    """Раскрывает скрытые свойства кристалла."""
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден.", gold

    cost = IDENTIFY_COST
    if gold < cost:
        return False, f"Нужно {cost}з.", gold

    from game.crystal_service import get_bond_level, get_monsters_in_crystal
    monsters = get_monsters_in_crystal(crystal_id)
    bonds = [(m["name"], get_bond_level(m["id"], crystal_id)) for m in monsters]

    lines = [f"🔍 Анализ: {crystal['name']}\n"]
    lines.append(f"Редкость: {crystal['rarity']} | Резонанс: {crystal['emotion_affinity']}")
    lines.append(f"Объём: {crystal['current_volume']}/{crystal['max_volume']}")
    lines.append(f"Состояние: {crystal['state']} | Боёв: {crystal.get('battle_count', 0)}")
    if bonds:
        lines.append("\n🔗 Связи:")
        for name, lvl in bonds:
            bar = "★" * lvl + "☆" * (5 - lvl)
            lines.append(f"  {name}: [{bar}] ур.{lvl}")

    # Скрытое свойство (генерируется детерминированно по ID)
    import hashlib
    h = int(hashlib.md5(str(crystal_id).encode()).hexdigest(), 16)
    hidden_props = [
        "🌟 Скрытое: этот кристалл резонирует с монстрами ночного типа (+3% ATK в ночное время)",
        "💫 Скрытое: кристалл хранит эхо предыдущего владельца (+5% к опыту монстров)",
        "🔥 Скрытое: трещины в прошлом закалили структуру (+1 к броне монстра)",
        "❄️ Скрытое: охлаждающий эффект (-15% время охлаждения между боями)",
        "⚡ Скрытое: проводящая структура (+2% к шансу критического удара)",
    ]
    lines.append(f"\n{hidden_props[h % len(hidden_props)]}")

    return True, "\n".join(lines), gold - cost


def buy_shards(telegram_id: int, crystal_id: int, gold: int) -> tuple[bool, str, int]:
    """Гемма скупает сломанные кристаллы за осколки."""
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден.", gold
    if crystal["state"] != "broken":
        return False, "Гемма принимает только сломанные кристаллы.", gold
    if crystal["current_monsters"] > 0:
        return False, "Сначала перемести монстров из кристалла.", gold

    price = SHARD_BUY_PRICE * {"common": 1, "uncommon": 2, "rare": 3,
                                 "epic": 5, "legendary": 8}.get(crystal["rarity"], 1)
    with get_connection() as conn:
        conn.execute("DELETE FROM player_crystals WHERE id=?", (crystal_id,))
        conn.commit()

    from database.repositories import add_resource
    add_resource(telegram_id, "crystal_shard", 1)
    return True, f"✅ Гемма купила {crystal['name']} за {price}з + 1 осколок кристалла.", gold + price


def render_workshop_menu(telegram_id: int) -> str:
    """Текст меню мастерской."""
    crystals = get_player_crystals(telegram_id)
    damaged = [c for c in crystals if c.get("state") in ("cracked", "broken")]
    lines = [
        f"🔨 Мастерская Геммы\n",
        f"«Каждый кристалл имеет душу. Я лишь помогаю ей раскрыться.»\n",
        f"Твои кристаллы: {len(crystals)}",
    ]
    if damaged:
        lines.append(f"⚠️ Требуют ремонта: {len(damaged)}")
    lines.extend([
        "\nУслуги:",
        f"🔧 Ремонт — от {REPAIR_COSTS['common']['cracked']}з",
        f"⬆️ Улучшение объёма — от {UPGRADE_COSTS['common']}з",
        f"🔄 Смена резонанса — {RESONANCE_CHANGE_COST}з",
        f"🔍 Идентификация — {IDENTIFY_COST}з",
        f"🪨 Скупка осколков — от {SHARD_BUY_PRICE}з",
    ])
    return "\n".join(lines)
