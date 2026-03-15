from database.models import Player

PLAYERS = {}
PENDING_ENCOUNTERS = {}
PLAYER_MONSTERS = {}
PLAYER_EMOTIONS = {}
PLAYER_QUESTS = {}
NEXT_MONSTER_ID = 1

DEFAULT_EMOTIONS = {
    "rage": 0,
    "fear": 0,
    "instinct": 0,
    "inspiration": 0,
}

STARTER_QUESTS = {
    "first_steps": {
        "title": "Первые шаги",
        "description": "Исследуй мир 3 раза.",
        "target_type": "explore",
        "target_value": 3,
        "reward_gold": 20,
        "reward_exp": 10,
    },
    "first_hunt": {
        "title": "Первая охота",
        "description": "Победи 2 монстров в бою.",
        "target_type": "win",
        "target_value": 2,
        "reward_gold": 25,
        "reward_exp": 12,
    },
    "collector": {
        "title": "Коллекционер",
        "description": "Поймай 2 монстров.",
        "target_type": "capture",
        "target_value": 2,
        "reward_gold": 30,
        "reward_exp": 15,
    },
}

def get_player(telegram_id: int):
    return PLAYERS.get(telegram_id)

def create_player(telegram_id: int, name: str):
    player = Player(telegram_id=telegram_id, name=name)
    PLAYERS[telegram_id] = player
    PLAYER_MONSTERS[telegram_id] = []
    PLAYER_EMOTIONS[telegram_id] = DEFAULT_EMOTIONS.copy()
    PLAYER_QUESTS[telegram_id] = {
        key: {"progress": 0, "completed": False, **value}
        for key, value in STARTER_QUESTS.items()
    }
    return player

def reset_player_state(telegram_id: int, name: str = "Игрок"):
    PLAYERS[telegram_id] = Player(telegram_id=telegram_id, name=name)
    PLAYER_MONSTERS[telegram_id] = []
    PLAYER_EMOTIONS[telegram_id] = DEFAULT_EMOTIONS.copy()
    PLAYER_QUESTS[telegram_id] = {
        key: {"progress": 0, "completed": False, **value}
        for key, value in STARTER_QUESTS.items()
    }
    PENDING_ENCOUNTERS.pop(telegram_id, None)
    return PLAYERS[telegram_id]

def get_or_create_player(telegram_id: int, name: str):
    player = get_player(telegram_id)
    if player:
        if telegram_id not in PLAYER_MONSTERS:
            PLAYER_MONSTERS[telegram_id] = []
        if telegram_id not in PLAYER_EMOTIONS:
            PLAYER_EMOTIONS[telegram_id] = DEFAULT_EMOTIONS.copy()
        if telegram_id not in PLAYER_QUESTS:
            PLAYER_QUESTS[telegram_id] = {
                key: {"progress": 0, "completed": False, **value}
                for key, value in STARTER_QUESTS.items()
            }
        return player, False
    return create_player(telegram_id, name), True

def get_player_quests(telegram_id: int):
    if telegram_id not in PLAYER_QUESTS:
        PLAYER_QUESTS[telegram_id] = {
            key: {"progress": 0, "completed": False, **value}
            for key, value in STARTER_QUESTS.items()
        }
    return PLAYER_QUESTS[telegram_id]

def progress_quests(telegram_id: int, action_type: str):
    quests = get_player_quests(telegram_id)
    completed_now = []
    for quest_id, quest in quests.items():
        if quest["completed"]:
            continue
        if quest["target_type"] != action_type:
            continue
        quest["progress"] += 1
        if quest["progress"] >= quest["target_value"]:
            quest["completed"] = True
            completed_now.append((quest_id, quest))
    return completed_now

def get_player_emotions(telegram_id: int):
    if telegram_id not in PLAYER_EMOTIONS:
        PLAYER_EMOTIONS[telegram_id] = DEFAULT_EMOTIONS.copy()
    return PLAYER_EMOTIONS[telegram_id]

def add_emotions(telegram_id: int, changes: dict):
    emotions = get_player_emotions(telegram_id)
    for key, value in changes.items():
        emotions[key] = emotions.get(key, 0) + value
    return emotions

def spend_emotions(telegram_id: int, changes: dict):
    emotions = get_player_emotions(telegram_id)
    for key, value in changes.items():
        emotions[key] = max(0, emotions.get(key, 0) - value)
    return emotions

def update_player_location(telegram_id: int, location_slug: str):
    player = PLAYERS.get(telegram_id)
    if not player:
        return None
    player.location_slug = location_slug
    location_defaults = {
        "dark_forest": "mushroom_path",
        "shadow_swamp": "black_water",
        "volcano_wrath": "ash_slope",
        "bone_desert": "",
        "ancient_ruins": "",
        "emotion_rift": "",
        "storm_ridge": "",
    }
    player.current_district_slug = location_defaults.get(location_slug, "")
    return player

def update_player_district(telegram_id: int, district_slug: str):
    player = PLAYERS.get(telegram_id)
    if not player:
        return None
    player.current_district_slug = district_slug
    return player

def save_pending_encounter(telegram_id: int, encounter: dict):
    PENDING_ENCOUNTERS[telegram_id] = encounter
    return encounter

def get_pending_encounter(telegram_id: int):
    return PENDING_ENCOUNTERS.get(telegram_id)

def clear_pending_encounter(telegram_id: int):
    return PENDING_ENCOUNTERS.pop(telegram_id, None)

def add_player_gold(telegram_id: int, amount: int):
    player = PLAYERS.get(telegram_id)
    if not player:
        return None
    player.gold += amount
    return player

def add_player_experience(telegram_id: int, amount: int):
    player = PLAYERS.get(telegram_id)
    if not player:
        return None
    player.experience += amount
    while player.experience >= player.level * 10:
        player.experience -= player.level * 10
        player.level += 1
    return player

def restore_player_energy(telegram_id: int, amount: int, max_energy: int = 10):
    player = PLAYERS.get(telegram_id)
    if not player:
        return None
    player.energy = min(max_energy, player.energy + amount)
    return player

def spend_player_energy(telegram_id: int, amount: int):
    player = PLAYERS.get(telegram_id)
    if not player:
        return False
    if player.energy < amount:
        return False
    player.energy -= amount
    return True

def add_captured_monster(telegram_id: int, name: str, rarity: str, mood: str, hp: int, attack: int, source_type: str = "wild"):
    global NEXT_MONSTER_ID
    if telegram_id not in PLAYER_MONSTERS:
        PLAYER_MONSTERS[telegram_id] = []

    player_monsters = PLAYER_MONSTERS[telegram_id]
    is_first = len(player_monsters) == 0

    monster = {
        "id": NEXT_MONSTER_ID,
        "name": name,
        "rarity": rarity,
        "mood": mood,
        "hp": hp,
        "max_hp": hp,
        "current_hp": hp,
        "attack": attack,
        "level": 1,
        "experience": 0,
        "is_active": is_first,
        "infection_type": None,
        "infection_stage": 0,
        "corruption": 0,
        "source_type": source_type,
    }
    NEXT_MONSTER_ID += 1
    player_monsters.append(monster)
    return monster

def get_player_monsters(telegram_id: int):
    return PLAYER_MONSTERS.get(telegram_id, [])

def get_active_monster(telegram_id: int):
    for monster in PLAYER_MONSTERS.get(telegram_id, []):
        if monster.get("is_active"):
            if "current_hp" not in monster:
                monster["current_hp"] = monster.get("hp", 1)
            if "max_hp" not in monster:
                monster["max_hp"] = monster.get("hp", 1)
            return monster
    return None

def damage_active_monster(telegram_id: int, amount: int):
    monster = get_active_monster(telegram_id)
    if not monster:
        return None
    monster["current_hp"] = max(0, monster.get("current_hp", monster["hp"]) - amount)
    return monster

def heal_active_monster(telegram_id: int, amount: int = 999):
    monster = get_active_monster(telegram_id)
    if not monster:
        return None
    monster["current_hp"] = min(monster.get("max_hp", monster["hp"]), monster.get("current_hp", monster["hp"]) + amount)
    return monster

def heal_all_monsters(telegram_id: int):
    monsters = PLAYER_MONSTERS.get(telegram_id, [])
    for monster in monsters:
        monster["current_hp"] = monster.get("max_hp", monster.get("hp", 1))
    return monsters

def set_active_monster(telegram_id: int, monster_id: int):
    monsters = PLAYER_MONSTERS.get(telegram_id, [])
    target = None
    for monster in monsters:
        monster["is_active"] = False
        if "current_hp" not in monster:
            monster["current_hp"] = monster.get("hp", 1)
        if "max_hp" not in monster:
            monster["max_hp"] = monster.get("hp", 1)
        if monster["id"] == monster_id:
            target = monster
    if target:
        target["is_active"] = True
    return target

def get_monster_by_id(telegram_id: int, monster_id: int):
    for monster in PLAYER_MONSTERS.get(telegram_id, []):
        if monster["id"] == monster_id:
            if "current_hp" not in monster:
                monster["current_hp"] = monster.get("hp", 1)
            if "max_hp" not in monster:
                monster["max_hp"] = monster.get("hp", 1)
            return monster
    return None
