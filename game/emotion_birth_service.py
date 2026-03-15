from database.repositories import add_captured_monster, get_player_emotions, spend_emotions

BIRTH_RECIPES = [
    {
        "requirements": {"rage": 3, "fear": 2},
        "monster": {"name": "Пепельный Вой", "rarity": "epic", "mood": "rage", "hp": 42, "attack": 11},
    },
    {
        "requirements": {"fear": 3, "inspiration": 2},
        "monster": {"name": "Покровный Наблюдатель", "rarity": "epic", "mood": "fear", "hp": 38, "attack": 10},
    },
    {
        "requirements": {"instinct": 3, "rage": 2},
        "monster": {"name": "Кровавый Следопыт", "rarity": "epic", "mood": "instinct", "hp": 40, "attack": 12},
    },
    {
        "requirements": {"inspiration": 3, "fear": 2},
        "monster": {"name": "Сумрачный Оракул", "rarity": "epic", "mood": "inspiration", "hp": 36, "attack": 11},
    },
    {
        "requirements": {"inspiration": 4, "rage": 2},
        "monster": {"name": "Звёздный Шёпот", "rarity": "legendary", "mood": "inspiration", "hp": 52, "attack": 14},
    },
    {
        "requirements": {"rage": 4, "instinct": 2},
        "monster": {"name": "Угольный Клык", "rarity": "legendary", "mood": "rage", "hp": 54, "attack": 15},
    },
]

def _matches(emotions: dict, requirements: dict):
    for key, needed in requirements.items():
        if emotions.get(key, 0) < needed:
            return False
    return True

def try_birth_emotional_monster(telegram_id: int):
    emotions = get_player_emotions(telegram_id)

    for recipe in BIRTH_RECIPES:
        if _matches(emotions, recipe["requirements"]):
            spend_emotions(telegram_id, recipe["requirements"])
            monster_data = recipe["monster"]
            monster = add_captured_monster(
                telegram_id=telegram_id,
                name=monster_data["name"],
                rarity=monster_data["rarity"],
                mood=monster_data["mood"],
                hp=monster_data["hp"],
                attack=monster_data["attack"],
                source_type="emotion",
            )
            return monster

    return None

def render_birth_text(monster):
    if not monster:
        return ""
    return (
        f"🌌 Твои эмоции сгущаются и обретают форму.\n"
        f"Родился эмоциональный монстр: {monster['name']}!\n"
        f"Редкость: {monster['rarity']}\n"
        f"Эмоция: {monster['mood']}"
    )
