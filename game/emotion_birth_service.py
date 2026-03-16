from database.repositories import (
    add_captured_monster,
    get_player,
    get_player_emotions,
    is_birth_done,
    mark_birth_done,
    spend_emotions,
    start_birth_cooldown,
)

BIRTH_RECIPES = [
    {"emotion": "fear", "threshold": 8, "name": "Покровный Наблюдатель", "rarity": "epic", "mood": "fear", "hp": 38, "attack": 10},
    {"emotion": "rage", "threshold": 8, "name": "Багровый Искролом", "rarity": "epic", "mood": "rage", "hp": 36, "attack": 11},
    {"emotion": "instinct", "threshold": 8, "name": "Первозданный Следопыт", "rarity": "epic", "mood": "instinct", "hp": 34, "attack": 11},
    {"emotion": "inspiration", "threshold": 8, "name": "Эфирный Хранитель Искры", "rarity": "epic", "mood": "inspiration", "hp": 35, "attack": 10},
]

RARITY_LABELS = {"common": "Обычный", "rare": "Редкий", "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический"}
MOOD_LABELS = {"rage": "Ярость", "fear": "Страх", "instinct": "Инстинкт", "inspiration": "Вдохновение"}

def try_birth_emotional_monster(telegram_id: int):
    if is_birth_done(telegram_id):
        return None
    player = get_player(telegram_id)
    if player and getattr(player, "birth_cooldown_actions", 0) > 0:
        return None

    emotions = get_player_emotions(telegram_id)
    for recipe in BIRTH_RECIPES:
        if emotions.get(recipe["emotion"], 0) >= recipe["threshold"]:
            spend_emotions(telegram_id, {recipe["emotion"]: recipe["threshold"]})
            monster = add_captured_monster(
                telegram_id=telegram_id,
                name=recipe["name"],
                rarity=recipe["rarity"],
                mood=recipe["mood"],
                hp=recipe["hp"],
                attack=recipe["attack"],
                source_type="emotion",
            )
            mark_birth_done(telegram_id)
            start_birth_cooldown(telegram_id, actions=3)
            return monster
    return None

def render_birth_text(monster):
    if not monster:
        return ""
    return (
        f"🌌 Твои эмоции сгущаются и обретают форму.\n"
        f"Родился эмоциональный монстр: {monster['name']}\n"
        f"Редкость: {RARITY_LABELS.get(monster['rarity'], monster['rarity'])}\n"
        f"Эмоция: {MOOD_LABELS.get(monster['mood'], monster['mood'])}\n"
        f"Следующее рождение будет доступно через несколько действий."
    )
