import random

DUNGEONS = {
    "dark_forest": {
        "name": "🕳 Корни забытой чащи",
        "rooms": 4,
        "theme": "forest",
        "boss": {"name": "🌲 Хозяин корней", "hp": 60, "attack": 12, "reward_gold": 70, "reward_exp": 28},
    },
    "stone_hills": {
        "name": "🕳 Глубинная жила",
        "rooms": 4,
        "theme": "stone",
        "boss": {"name": "⛰ Сердце монолита", "hp": 66, "attack": 13, "reward_gold": 80, "reward_exp": 30},
    },
    "shadow_marsh": {
        "name": "🕳 Омут безмолвия",
        "rooms": 4,
        "theme": "marsh",
        "boss": {"name": "🕸 Тёмный омутник", "hp": 64, "attack": 13, "reward_gold": 78, "reward_exp": 30},
    },
}

THEME_TREASURES = {
    "forest": {"gold": 16, "items": {"small_potion": 1}},
    "stone": {"gold": 18, "items": {"energy_capsule": 1}},
    "marsh": {"gold": 17, "items": {"basic_trap": 1}},
}

def get_dungeon(location_slug: str):
    data = DUNGEONS.get(location_slug)
    return data.copy() if data else None

def start_dungeon_state(location_slug: str):
    dungeon = get_dungeon(location_slug)
    if not dungeon:
        return None
    return {
        "location_slug": location_slug,
        "name": dungeon["name"],
        "theme": dungeon["theme"],
        "room_index": 0,
        "rooms_total": dungeon["rooms"],
        "boss": dungeon["boss"].copy(),
        "current_room": None,
        "completed": False,
    }

def generate_room(state: dict):
    next_index = state["room_index"] + 1
    if next_index >= state["rooms_total"]:
        return {
            "type": "boss",
            "title": "👑 Зал босса",
            "text": f"Ты входишь в последний зал. Здесь тебя ждёт {state['boss']['name']}.",
            "enemy": state["boss"].copy(),
        }

    roll = random.random()
    if roll < 0.45:
        enemy_names = {
            "forest": [("Корневой хищник", 28, 7), ("Чащобный зверь", 30, 8)],
            "stone": [("Каменный бур", 30, 8), ("Пещерный ломатель", 32, 9)],
            "marsh": [("Болотный пастух", 29, 8), ("Смоляной охотник", 31, 9)],
        }
        name, hp, attack = random.choice(enemy_names[state["theme"]])
        return {
            "type": "combat",
            "title": "⚔️ Враждебная комната",
            "text": f"В проходе тебя перехватывает {name}.",
            "enemy": {"name": name, "hp": hp, "attack": attack, "reward_gold": 18, "reward_exp": 10},
        }
    if roll < 0.70:
        treasure = THEME_TREASURES[state["theme"]]
        return {
            "type": "treasure",
            "title": "🏺 Тайник",
            "text": "Ты находишь скрытый тайник между стенами подземелья.",
            "gold": treasure["gold"],
            "items": treasure["items"].copy(),
        }
    if roll < 0.85:
        return {
            "type": "rest",
            "title": "⛲ Безопасный зал",
            "text": "Здесь можно перевести дух. Воздух тихий и спокойный.",
            "heal": 10,
            "energy": 1,
        }
    return {
        "type": "event",
        "title": "📜 Странная находка",
        "text": "Ты находишь древние символы и получаешь опыт исследователя.",
        "reward_exp": 8,
        "reward_gold": 10,
    }

def render_dungeon_state(state: dict):
    room = state.get("current_room")
    lines = [
        f"{state['name']}",
        "",
        f"Комната: {state['room_index']} / {state['rooms_total']}",
    ]
    if room:
        lines.extend(["", room["title"], room["text"]])
        if room["type"] in {"combat", "boss"}:
            lines.append(f"Враг: {room['enemy']['name']} | HP: {room['enemy']['hp']} | Атака: {room['enemy']['attack']}")
    else:
        lines.append("")
        lines.append("Подземелье ждёт следующего шага.")
    return "\n".join(lines)
