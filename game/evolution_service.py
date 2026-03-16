from database.repositories import get_active_monster

RARITY_LABELS = {
    "common": "Обычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
    "mythic": "Мифический",
}

EVOLUTION_RECIPES = [
    {"base_name": "Эхо-Лис", "min_level": 3, "min_infection_stage": 2, "infection_type": "inspiration", "result_name": "Эфирный Эхо-Лис", "rarity": "epic", "hp_bonus": 8, "attack_bonus": 2},
    {"base_name": "Эхо-Лис", "min_level": 3, "min_infection_stage": 2, "infection_type": "fear", "result_name": "Сумрачный Эхо-Лис", "rarity": "epic", "hp_bonus": 10, "attack_bonus": 1},
    {"base_name_contains": "Клык", "min_level": 4, "min_infection_stage": 3, "infection_type": "rage", "result_name": "Багровый Клык", "rarity": "legendary", "hp_bonus": 12, "attack_bonus": 3},
    {"base_name_contains": "Следопыт", "min_level": 4, "min_infection_stage": 3, "infection_type": "instinct", "result_name": "Кровавый Альфа-Следопыт", "rarity": "legendary", "hp_bonus": 10, "attack_bonus": 4},
]

def _matches(monster: dict, recipe: dict) -> bool:
    if monster.get("evolution_stage", 0) >= 1:
        return False
    if monster.get("level", 1) < recipe["min_level"]:
        return False
    if monster.get("infection_type") != recipe["infection_type"]:
        return False
    if monster.get("infection_stage", 0) < recipe.get("min_infection_stage", 1):
        return False
    if "base_name" in recipe and monster.get("name") != recipe["base_name"]:
        return False
    if "base_name_contains" in recipe and recipe["base_name_contains"] not in monster.get("name", ""):
        return False
    return True

def try_evolve_active_monster(telegram_id: int):
    monster = get_active_monster(telegram_id)
    if not monster:
        return None
    for recipe in EVOLUTION_RECIPES:
        if _matches(monster, recipe):
            monster["name"] = recipe["result_name"]
            monster["rarity"] = recipe["rarity"]
            monster["max_hp"] = monster.get("max_hp", monster.get("hp", 1)) + recipe["hp_bonus"]
            monster["hp"] = monster["max_hp"]
            monster["current_hp"] = monster["max_hp"]
            monster["attack"] = monster.get("attack", 1) + recipe["attack_bonus"]
            monster["evolution_stage"] = monster.get("evolution_stage", 0) + 1
            return monster
    return None

def render_evolution_text(monster):
    if not monster:
        return ""
    return (
        f"Эволюция!\n"
        f"Твой монстр принимает новую форму: {monster['name']}\n"
        f"Редкость: {RARITY_LABELS.get(monster['rarity'], monster['rarity'])}\n"
        f"HP: {monster['current_hp']}/{monster['max_hp']}\n"
        f"Атака: {monster['attack']}"
    )
