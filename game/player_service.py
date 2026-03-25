"""
player_service.py — утилиты для работы с игроком и стартовой миграции кристаллов.
"""

from database.repositories import get_player_monsters, add_captured_monster

# Стартовые монстры — выдаётся один случайным образом при первом входе
STARTER_MONSTERS = [
    {"name": "Лесной спрайт",    "rarity": "common", "mood": "inspiration", "hp": 22, "attack": 5},
    {"name": "Болотный охотник", "rarity": "common", "mood": "instinct",    "hp": 20, "attack": 6},
    {"name": "Угольный клык",    "rarity": "common", "mood": "rage",        "hp": 18, "attack": 7},
]


def _monster_has_crystal(monster: dict) -> bool:
    """
    Универсальная проверка, привязан ли монстр к кристаллу.
    Поддерживает разные формы данных из репозитория.
    """
    crystal_id = monster.get("crystal_id")
    if crystal_id not in (None, "", 0, "0"):
        return True

    crystal_slug = monster.get("crystal_slug")
    if crystal_slug not in (None, ""):
        return True

    return False


def ensure_starter_monster(telegram_id: int) -> tuple[dict | None, bool]:
    """
    Убеждается, что у игрока есть хотя бы один монстр.
    Если нет — выдаёт случайного стартового.

    Возвращает:
        (monster_dict, was_created: bool)
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

    # Пытаемся сразу поместить стартового монстра в стартовый кристалл
    try:
        from game.crystal_service import ensure_starter_crystal, auto_store_new_monster

        ensure_starter_crystal(telegram_id)
        auto_store_new_monster(telegram_id, monster["id"])
    except Exception:
        pass

    return monster, True


def ensure_player_crystal_state(telegram_id: int) -> dict:
    """
    Приводит игрока к корректному состоянию системы кристаллов.

    Что делает:
    1. Гарантирует наличие стартового кристалла.
    2. Гарантирует наличие хотя бы одного стартового монстра.
    3. Пытается разложить старых монстров без кристаллов по доступным кристаллам.

    Возвращает словарь с итогом миграции:
    {
        "starter_created": bool,
        "moved_to_crystals": int,
        "left_unstored": int,
    }
    """
    starter_created = False
    moved_to_crystals = 0
    left_unstored = 0

    try:
        from game.crystal_service import ensure_starter_crystal, auto_store_new_monster
    except Exception:
        # Если crystal_service временно недоступен, хотя бы выдадим стартового монстра
        _, starter_created = ensure_starter_monster(telegram_id)
        return {
            "starter_created": starter_created,
            "moved_to_crystals": 0,
            "left_unstored": 0,
        }

    # 1. Гарантируем наличие стартового кристалла
    try:
        ensure_starter_crystal(telegram_id)
    except Exception:
        pass

    # 2. Гарантируем наличие стартового монстра
    _, starter_created = ensure_starter_monster(telegram_id)

    # 3. Пытаемся разложить всех старых монстров без кристалла
    monsters = get_player_monsters(telegram_id)
    for monster in monsters:
        if _monster_has_crystal(monster):
            continue

        try:
            ok, _msg = auto_store_new_monster(telegram_id, monster["id"])
            if ok:
                moved_to_crystals += 1
            else:
                left_unstored += 1
        except Exception:
            left_unstored += 1

    return {
        "starter_created": starter_created,
        "moved_to_crystals": moved_to_crystals,
        "left_unstored": left_unstored,
    }
