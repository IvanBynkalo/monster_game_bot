
import random

DUNGEON_KEYS = {
    "forest_key": {"name": "🗝 Лесной ключ", "dungeon": "dark_forest"},
    "stone_key": {"name": "🗝 Каменный ключ", "dungeon": "stone_hills"},
    "marsh_key": {"name": "🗝 Болотный ключ", "dungeon": "shadow_marsh"},
}

KEY_DISCOVERY_CHANCE = 0.08

def roll_dungeon_key():
    if random.random() > KEY_DISCOVERY_CHANCE:
        return None
    return random.choice(list(DUNGEON_KEYS.keys()))

def get_key_name(key):
    data = DUNGEON_KEYS.get(key)
    return data["name"] if data else key
