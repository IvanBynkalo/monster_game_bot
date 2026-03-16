from database.models import Player

PLAYERS = {}
PENDING_ENCOUNTERS = {}
PLAYER_MONSTERS = {}
PLAYER_EMOTIONS = {}
PLAYER_QUESTS = {}
PLAYER_STORY = {}
NEXT_MONSTER_ID = 1

DEFAULT_EMOTIONS = {"rage": 0, "fear": 0, "instinct": 0, "inspiration": 0}

STARTER_QUESTS = {
    "first_steps": {"title": "Первые шаги", "description": "Исследуй мир 3 раза.", "target_type": "explore", "target_value": 3, "reward_gold": 20, "reward_exp": 10},
    "first_hunt": {"title": "Первая охота", "description": "Победи 2 монстров в бою.", "target_type": "win", "target_value": 2, "reward_gold": 25, "reward_exp": 12},
    "collector": {"title": "Коллекционер", "description": "Поймай 2 монстров.", "target_type": "capture", "target_value": 2, "reward_gold": 30, "reward_exp": 15},
}

STORY_QUESTS = [
    {"id": "forest_echo", "title": "Шёпот леса", "description": "Исследуй Тёмный лес 2 раза.", "requirements": {"location_slug": "dark_forest", "explore_count": 2}, "reward_gold": 25, "reward_exp": 12, "reward_text": "След уходит в Болото теней."},
    {"id": "swamp_sign", "title": "Тени у воды", "description": "Доберись до Болота теней и исследуй его 1 раз.", "requirements": {"location_slug": "shadow_swamp", "explore_count": 1}, "reward_gold": 35, "reward_exp": 16, "reward_text": "Голоса ведут к Вулкану ярости."},
    {"id": "volcano_trial", "title": "Испытание жаром", "description": "Доберись до Вулкана ярости и победи там 1 монстра.", "requirements": {"location_slug": "volcano_wrath", "win_count": 1}, "reward_gold": 50, "reward_exp": 25, "reward_text": "Первый акт истории региона завершён."},
]

def _default_story():
    return {
        "current_index": 0,
        "completed_ids": [],
        "forest_echo": {"explore_count": 0, "win_count": 0, "visited": False},
        "swamp_sign": {"explore_count": 0, "win_count": 0, "visited": False},
        "volcano_trial": {"explore_count": 0, "win_count": 0, "visited": False},
    }

def get_player(telegram_id: int):
    return PLAYERS.get(telegram_id)

def create_player(telegram_id: int, name: str):
    player = Player(telegram_id=telegram_id, name=name)
    PLAYERS[telegram_id] = player
    PLAYER_MONSTERS[telegram_id] = []
    PLAYER_EMOTIONS[telegram_id] = DEFAULT_EMOTIONS.copy()
    PLAYER_QUESTS[telegram_id] = {k: {"progress": 0, "completed": False, **v} for k, v in STARTER_QUESTS.items()}
    PLAYER_STORY[telegram_id] = _default_story()
    return player

def reset_player_state(telegram_id: int, name: str = "Игрок"):
    PLAYERS[telegram_id] = Player(telegram_id=telegram_id, name=name)
    PLAYER_MONSTERS[telegram_id] = []
    PLAYER_EMOTIONS[telegram_id] = DEFAULT_EMOTIONS.copy()
    PLAYER_QUESTS[telegram_id] = {k: {"progress": 0, "completed": False, **v} for k, v in STARTER_QUESTS.items()}
    PLAYER_STORY[telegram_id] = _default_story()
    PENDING_ENCOUNTERS.pop(telegram_id, None)
    return PLAYERS[telegram_id]

def get_or_create_player(telegram_id: int, name: str):
    player = get_player(telegram_id)
    if player:
        PLAYER_MONSTERS.setdefault(telegram_id, [])
        PLAYER_EMOTIONS.setdefault(telegram_id, DEFAULT_EMOTIONS.copy())
        PLAYER_QUESTS.setdefault(telegram_id, {k: {"progress": 0, "completed": False, **v} for k, v in STARTER_QUESTS.items()})
        PLAYER_STORY.setdefault(telegram_id, _default_story())
        return player, False
    return create_player(telegram_id, name), True

def get_player_story(telegram_id: int):
    return PLAYER_STORY.setdefault(telegram_id, _default_story())

def get_current_story_quest(telegram_id: int):
    story = get_player_story(telegram_id)
    idx = story["current_index"]
    if idx >= len(STORY_QUESTS):
        return None
    return STORY_QUESTS[idx]

def update_story_progress(telegram_id: int, action_type: str, current_location_slug: str):
    story = get_player_story(telegram_id)
    quest = get_current_story_quest(telegram_id)
    if not quest:
        return None
    state = story[quest["id"]]
    state["visited"] = state["visited"] or current_location_slug == quest["requirements"]["location_slug"]
    if current_location_slug == quest["requirements"]["location_slug"]:
        if action_type == "explore":
            state["explore_count"] += 1
        elif action_type == "win":
            state["win_count"] += 1
    req = quest["requirements"]
    if (state["visited"]
        and state["explore_count"] >= req.get("explore_count", 0)
        and state["win_count"] >= req.get("win_count", 0)):
        story["completed_ids"].append(quest["id"])
        story["current_index"] += 1
        return quest
    return None

def get_player_quests(telegram_id: int):
    return PLAYER_QUESTS.setdefault(telegram_id, {k: {"progress": 0, "completed": False, **v} for k, v in STARTER_QUESTS.items()})

def progress_quests(telegram_id: int, action_type: str):
    quests = get_player_quests(telegram_id)
    completed_now = []
    for quest_id, quest in quests.items():
        if quest["completed"] or quest["target_type"] != action_type:
            continue
        quest["progress"] += 1
        if quest["progress"] >= quest["target_value"]:
            quest["completed"] = True
            completed_now.append((quest_id, quest))
    return completed_now

def get_player_emotions(telegram_id: int):
    return PLAYER_EMOTIONS.setdefault(telegram_id, DEFAULT_EMOTIONS.copy())

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
    defaults = {"dark_forest": "mushroom_path", "shadow_swamp": "black_water", "volcano_wrath": "ash_slope", "bone_desert": "", "ancient_ruins": "", "emotion_rift": "", "storm_ridge": ""}
    player.current_district_slug = defaults.get(location_slug, "")
    return player

def update_player_district(telegram_id: int, district_slug: str):
    player = PLAYERS.get(telegram_id)
    if player:
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
    if player:
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
    if player:
        player.energy = min(max_energy, player.energy + amount)
    return player

def spend_player_energy(telegram_id: int, amount: int):
    player = PLAYERS.get(telegram_id)
    if not player or player.energy < amount:
        return False
    player.energy -= amount
    return True

def add_captured_monster(telegram_id: int, name: str, rarity: str, mood: str, hp: int, attack: int, source_type: str = "wild"):
    global NEXT_MONSTER_ID
    PLAYER_MONSTERS.setdefault(telegram_id, [])
    is_first = len(PLAYER_MONSTERS[telegram_id]) == 0
    monster = {"id": NEXT_MONSTER_ID, "name": name, "rarity": rarity, "mood": mood, "hp": hp, "max_hp": hp, "current_hp": hp, "attack": attack, "level": 1, "experience": 0, "is_active": is_first, "infection_type": None, "infection_stage": 0, "corruption": 0, "source_type": source_type, "evolution_stage": 0}
    NEXT_MONSTER_ID += 1
    PLAYER_MONSTERS[telegram_id].append(monster)
    return monster

def get_player_monsters(telegram_id: int):
    return PLAYER_MONSTERS.get(telegram_id, [])

def get_active_monster(telegram_id: int):
    for monster in PLAYER_MONSTERS.get(telegram_id, []):
        if monster.get("is_active"):
            monster.setdefault("current_hp", monster.get("hp", 1))
            monster.setdefault("max_hp", monster.get("hp", 1))
            monster.setdefault("experience", 0)
            monster.setdefault("evolution_stage", 0)
            return monster
    return None

def damage_active_monster(telegram_id: int, amount: int):
    monster = get_active_monster(telegram_id)
    if monster:
        monster["current_hp"] = max(0, monster["current_hp"] - amount)
    return monster

def heal_active_monster(telegram_id: int, amount: int = 999):
    monster = get_active_monster(telegram_id)
    if monster:
        monster["current_hp"] = min(monster["max_hp"], monster["current_hp"] + amount)
    return monster

def heal_all_monsters(telegram_id: int):
    monsters = PLAYER_MONSTERS.get(telegram_id, [])
    for monster in monsters:
        monster["current_hp"] = monster.get("max_hp", monster.get("hp", 1))
    return monsters

def add_active_monster_experience(telegram_id: int, amount: int):
    monster = get_active_monster(telegram_id)
    if not monster:
        return None, []
    monster["experience"] += amount
    level_ups = []
    while monster["experience"] >= monster["level"] * 5:
        monster["experience"] -= monster["level"] * 5
        monster["level"] += 1
        monster["max_hp"] += 4
        monster["attack"] += 1
        monster["current_hp"] = monster["max_hp"]
        level_ups.append({"level": monster["level"], "max_hp": monster["max_hp"], "attack": monster["attack"]})
    return monster, level_ups

def set_active_monster(telegram_id: int, monster_id: int):
    target = None
    for monster in PLAYER_MONSTERS.get(telegram_id, []):
        monster["is_active"] = False
        monster.setdefault("current_hp", monster.get("hp", 1))
        monster.setdefault("max_hp", monster.get("hp", 1))
        monster.setdefault("experience", 0)
        monster.setdefault("evolution_stage", 0)
        if monster["id"] == monster_id:
            target = monster
    if target:
        target["is_active"] = True
    return target

def get_monster_by_id(telegram_id: int, monster_id: int):
    for monster in PLAYER_MONSTERS.get(telegram_id, []):
        if monster["id"] == monster_id:
            monster.setdefault("current_hp", monster.get("hp", 1))
            monster.setdefault("max_hp", monster.get("hp", 1))
            monster.setdefault("experience", 0)
            monster.setdefault("evolution_stage", 0)
            return monster
    return None
