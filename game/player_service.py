"""
player_service.py — утилиты для работы с игроком.
"""
from database.repositories import get_player_monsters, add_captured_monster

# Стартовые монстры — выдаётся один случайным образом при первом входе
STARTER_MONSTERS = [
    {"name": "Лесной спрайт",    "rarity": "common", "mood": "inspiration", "hp": 22, "attack": 5},
    {"name": "Болотный охотник", "rarity": "common", "mood": "instinct",    "hp": 20, "attack": 6},
    {"name": "Угольный клык",    "rarity": "common", "mood": "rage",        "hp": 18, "attack": 7},
]


def ensure_starter_monster(telegram_id: int) -> tuple[dict | None, bool]:
    """
    Убеждается что у игрока есть хотя бы один монстр.
    Если нет — выдаёт случайного стартового.

    Возвращает (monster_dict, was_created: bool).
    """
    monsters = get_player_monsters(telegram_id)
    if monsters:
        return monsters[0], False

    import random
    template = random.choice(STARTER_MONSTERS)
    monster = add_captured_monster(
        telegram_id=telegram_id,
        name=template["name"],
        rarity=template["rarity"],
        mood=template["mood"],
        hp=template["hp"],
        attack=template["attack"],
        source_type="starter",
    )
    # Помещаем стартового монстра в кристалл
    try:
        from game.crystal_service import auto_store_new_monster as _cs, ensure_starter_crystal
        ensure_starter_crystal(telegram_id)
        _cs(telegram_id, monster["id"])
    except Exception:
        pass
    return monster, True
