import random

WORLD_BOSSES = [
    {
        "id": "forest_guardian",
        "name": "🌲 Древний страж леса",
        "location_slug": "dark_forest",
        "hp": 120,
        "attack": 18,
        "rarity": "legendary",
        "mood": "fear",
        "monster_type": "nature",
        "reward_gold": 120,
        "reward_exp": 55,
        "text": "Из глубины чащи выходит колосс из корней и мха.",
    },
    {
        "id": "stone_colossus",
        "name": "⛰ Колосс камня",
        "location_slug": "stone_hills",
        "hp": 145,
        "attack": 20,
        "rarity": "legendary",
        "mood": "instinct",
        "monster_type": "bone",
        "reward_gold": 135,
        "reward_exp": 60,
        "text": "Каменные плиты сходятся в одно тело, и перед тобой поднимается гигант.",
    },
    {
        "id": "marsh_king",
        "name": "🕸 Повелитель болот",
        "location_slug": "shadow_marsh",
        "hp": 130,
        "attack": 19,
        "rarity": "legendary",
        "mood": "fear",
        "monster_type": "shadow",
        "reward_gold": 128,
        "reward_exp": 58,
        "text": "Из тумана проступает древнее болотное существо, будто сотканное из смолы и шёпота.",
    },
]

WORLD_EVENTS = {
    "dark_forest": [
        {"title": "🍄 Споровый дождь", "description": "В лесу выпадает споровый дождь. Шанс на редкую траву повышен."},
        {"title": "👁 Шёпот у корней", "description": "Лес становится тревожнее. Монстры страха появляются чаще."},
    ],
    "emerald_fields": [
        {"title": "🌼 Цветение равнин", "description": "Поля полны аромата. Собиратели находят больше обычных ресурсов."},
        {"title": "💨 Ветер охотника", "description": "Ветер несёт следы зверей. Шанс удачной поимки немного выше."},
    ],
    "stone_hills": [
        {"title": "💎 Вспышка жилы", "description": "В склонах открываются редкие кристальные жилы."},
        {"title": "🪨 Каменная дрожь", "description": "Старые шахты гудят. Геологи чувствуют себя увереннее."},
    ],
    "shadow_marsh": [
        {"title": "🌫 Сгущение тумана", "description": "Туман скрывает редких и опасных существ."},
        {"title": "🕯 Смоляные огни", "description": "На болотах вспыхивают странные огни. Можно найти редкие болотные материалы."},
    ],
}

def roll_world_boss(location_slug: str):
    pool = [boss for boss in WORLD_BOSSES if boss["location_slug"] == location_slug]
    if not pool:
        return None
    if random.random() <= 0.08:
        return random.choice(pool).copy()
    return None

def get_world_event(location_slug: str):
    pool = WORLD_EVENTS.get(location_slug, [])
    if not pool:
        return None
    return random.choice(pool).copy()
