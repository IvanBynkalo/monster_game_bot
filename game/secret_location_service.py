
import random

SECRET_LOCATIONS = {
    "ancient_grove": {
        "name": "🌳 Древняя роща",
        "text": "Ты находишь скрытую тропу, ведущую в древнюю рощу.",
        "bonus_capture": 0.15,
        "rare_bonus": 0.10,
    },
    "crystal_cave": {
        "name": "💎 Хрустальная пещера",
        "text": "За водопадом открывается вход в пещеру, усыпанную кристаллами.",
        "rare_bonus": 0.20,
    },
    "forgotten_ruins": {
        "name": "🏛 Заброшенные руины",
        "text": "Среди камней ты замечаешь древние руины, скрытые от карт.",
        "bonus_gold": 30,
    },
}

DISCOVERY_CHANCE = 0.12

def roll_secret_location():
    if random.random() > DISCOVERY_CHANCE:
        return None
    key = random.choice(list(SECRET_LOCATIONS.keys()))
    data = SECRET_LOCATIONS[key].copy()
    data["id"] = key
    return data
