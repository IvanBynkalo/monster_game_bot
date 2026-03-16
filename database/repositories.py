from database.models import Player

PLAYERS = {}
PENDING_ENCOUNTERS = {}
PLAYER_MONSTERS = {}
PLAYER_EMOTIONS = {}
PLAYER_QUESTS = {}
PLAYER_STORY = {}
PLAYER_ACTION_FLAGS = {}
PLAYER_ITEMS = {}

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

STORY_QUESTS = [
    {
        "id": "forest_echo",
        "title": "Шёпот леса",
        "description": "Исследуй Тёмный лес 2 раза.",
        "requirements": {
            "location_slug": "dark_forest",
            "explore_count": 2,
        },
        "reward_gold": 25,
        "reward_exp": 12,
        "reward_text": "След уходит в Болото теней.",
    },
    {
        "id": "swamp_sign",
        "title": "Тени у воды",
        "description": "Доберись до Болота теней и исследуй его 1 раз.",
        "requirements": {
            "location_slug": "shadow_swamp",
            "explore_count": 1,
        },
        "reward_gold": 35,
        "reward_exp": 16,
        "reward_text": "Голоса ведут к Вулкану ярости.",
    },
    {
        "id": "volcano_trial",
        "title": "Испытание жаром",
        "description": "Доберись до Вулкана ярости и победи там 1 монстра.",
        "requirements": {
            "location_slug": "volcano_wrath",
            "win_count": 1,
        },
        "reward_gold": 50,
        "reward_exp": 25,
        "reward_text": "Первый акт истории региона завершён.",
    },
]


def _default_story():
    return {
        "current_index": 0,
        "completed_ids": [],
        "forest_echo": {
            "explore_count": 0,
            "win_count": 0,
            "visited": False,
        },
        "swamp_sign": {
            "explore_count": 0,
            "win_count": 0,
            "visited": False,
        },
        "volcano_trial": {
            "explore_count": 0,
            "win_count": 0,
            "visited": False,
        },
    }


def get_player(telegram_id: int):
    return PLAYERS.get(telegram_id)


def _ensure_player_collections(telegram_id: int):
    PLAYER_MONSTERS.setdefault(telegram_id, [])
    PLAYER_EMOTIONS.setdefault(telegram_id, DEFAULT_EMOTIONS.copy())
    PLAYER_QUESTS.setdefault(
        telegram_id,
        {
            k: {"progress": 0, "completed": False, **v}
            for k, v in STARTER_QUESTS.items()
        },
    )
    PLAYER_STORY.setdefault(telegram_id, _default_story())
    PLAYER_ACTION_FLAGS.setdefault(telegram_id, {})
    PLAYER_ITEMS.setdefault(
        telegram_id,
        {
            "small_potion": 2,
            "energy_capsule": 1,
            "basic_trap": 3,
        },
    )


def create_player(telegram_id: int, name: str):
    player = Player(telegram_id=telegram_id, name=name)
    PLAYERS[telegram_id] = player
    _ensure_player_collections(telegram_id)
    return player


def reset_player_state(telegram_id: int, name: str = "Игрок"):
    PLAYERS[telegram_id] = Player(telegram_id=telegram_id, name=name)
    PLAYER_MONSTERS[telegram_id] = []
    PLAYER_EMOTIONS[telegram_id] = DEFAULT_EMOTIONS.copy()
    PLAYER_QUESTS[telegram_id] = {
        k: {"progress": 0, "completed": False, **v}
        for k, v in STARTER_QUESTS.items()
    }
    PLAYER_STORY[telegram_id] = _default_story()
    PLAYER_ACTION_FLAGS[telegram_id] = {}
    PLAYER_ITEMS[telegram_id] = {
        "small_potion": 2,
        "energy_capsule": 1,
        "basic_trap": 3,
    }
    PENDING_ENCOUNTERS.pop(telegram_id, None)
    return PLAYERS[telegram_id]


def get_or_create_player(telegram_id: int, name: str):
    player = get_player(telegram_id)
    if player:
        _ensure_player_collections(telegram_id)
        return player, False
    return create_player(telegram_id, name), True


def begin_action_scope(telegram_id: int, action_key: str):
    flags = PLAYER_ACTION_FLAGS.setdefault(telegram_id, {})
    flags["current_action"] = action_key
    flags["birth_done"] = False
    return flags


def get_action_flags(telegram_id: int):
    return PLAYER_ACTION_FLAGS.setdefault(telegram_id, {})


def mark_birth_done(telegram_id: int):
    flags = PLAYER_ACTION_FLAGS.setdefault(telegram_id, {})
    flags["birth_done"] = True
    return flags


def is_birth_done(telegram_id: int):
    return PLAYER_ACTION_FLAGS.setdefault(telegram_id, {}).get("birth_done", False)


def tick_birth_cooldown(telegram_id: int):
    player = get_player(telegram_id)
    if not player:
        return 0
    if getattr(player, "birth_cooldown_actions", 0) > 0:
        player.birth_cooldown_actions -= 1
    return player.birth_cooldown_actions


def start_birth_cooldown(telegram_id: int, actions: int = 3):
    player = get_player(telegram_id)
    if not player:
        return 0
    player.birth_cooldown_actions = actions
    return player.birth_cooldown_actions


def get_player_story(telegram_id: int):
    _ensure_player_collections(telegram_id)
    return PLAYER_STORY[telegram_id]


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
    required_location = quest["requirements"]["location_slug"]

    state["visited"] = state["visited"] or current_location_slug == required_location

    if current_location_slug == required_location:
        if action_type == "explore":
            state["explore_count"] += 1
        elif action_type == "win":
            state["win_count"] += 1

    req = quest["requirements"]

    if (
        state["visited"]
        and state["explore_count"] >= req.get("explore_count", 0)
        and state["win_count"] >= req.get("win_count", 0)
    ):
        story["completed_ids"].append(quest["id"])
        story["current_index"] += 1
        return quest

    return None


def get_player_quests(telegram_id: int):
    _ensure_player_collections(telegram_id)
    return PLAYER_QUESTS[telegram_id]


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
    _ensure_player_collections(telegram_id)
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
    defaults = {
        "dark_forest": "mushroom_path",
        "shadow_swamp": "black_water",
        "volcano_wrath": "ash_slope",
        "bone_desert": "",
        "ancient_ruins": "",
        "emotion_rift": "",
        "storm_ridge": "",
    }
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


def get_inventory(telegram_id: int):
    _ensure_player_collections(telegram_id)
    return PLAYER_ITEMS[telegram_id]


def get_item_count(telegram_id: int, item_slug: str):
    return get_inventory(telegram_id).get(item_slug, 0)


def add_item(telegram_id: int, item_slug: str, amount: int = 1):
    inventory = get_inventory(telegram_id)
    inventory[item_slug] = inventory.get(item_slug, 0) + amount
    return inventory[item_slug]


def spend_item(telegram_id: int, item_slug: str, amount: int = 1):
    inventory = get_inventory(telegram_id)
    current = inventory.get(item_slug, 0)
    if current < amount:
        return False

    inventory[item_slug] = current - amount
    return True


def _guess_monster_type(name: str, mood: str):
    name_lower = name.lower()

    if "плам" in name_lower or "лав" in name_lower or "магм" in name_lower or mood == "rage":
        return "flame"
    if "тен" in name_lower or "сумрач" in name_lower or mood == "fear":
        return "shadow"
    if "гриб" in name_lower or "мох" in name_lower or "корн" in name_lower:
        return "nature"
    if "дух" in name_lower or "оракул" in name_lower:
        return "spirit"
    if "кост" in name_lower or "курган" in name_lower:
        return "bone"
    if "бур" in name_lower or "искр" in name_lower:
        return "storm"
    if "эхо" in name_lower or "шёп" in name_lower:
        return "echo"

    return "void"


def _migrate_monster_fields(monster: dict):
    if "distortion" not in monster:
        if "corruption" in monster:
            monster["distortion"] = monster.pop("corruption")
        else:
            monster["distortion"] = 0

    monster.setdefault("infection_type", None)
    monster.setdefault("infection_stage", 0)
    monster.setdefault("current_hp", monster.get("hp", 1))
    monster.setdefault("max_hp", monster.get("hp", 1))
    monster.setdefault("experience", 0)
    monster.setdefault("evolution_stage", 0)
    monster.setdefault(
        "monster_type",
        _guess_monster_type(monster.get("name", ""), monster.get("mood", "")),
    )
    return monster


def _generate_monster_id(telegram_id: int):
    monsters = PLAYER_MONSTERS.get(telegram_id, [])
    if not monsters:
        return 1
    return max(monster.get("id", 0) for monster in monsters) + 1


def _normalize_active_monster_state(telegram_id: int):
    monsters = get_player_monsters(telegram_id)
    active_monsters = [monster for monster in monsters if monster.get("is_active")]

    if not monsters:
        return

    if not active_monsters:
        monsters[0]["is_active"] = True
        return

    if len(active_monsters) > 1:
        first_active_id = active_monsters[0]["id"]
        for monster in monsters:
            monster["is_active"] = monster["id"] == first_active_id


def add_captured_monster(
    telegram_id: int,
    name: str,
    rarity: str,
    mood: str,
    hp: int,
    attack: int,
    source_type: str = "wild",
):
    _ensure_player_collections(telegram_id)

    is_first = len(PLAYER_MONSTERS[telegram_id]) == 0
    monster_id = _generate_monster_id(telegram_id)

    monster = {
        "id": monster_id,
        "name": name,
        "rarity": rarity,
        "mood": mood,
        "monster_type": _guess_monster_type(name, mood),
        "hp": hp,
        "max_hp": hp,
        "current_hp": hp,
        "attack": attack,
        "level": 1,
        "experience": 0,
        "is_active": is_first,
        "infection_type": None,
        "infection_stage": 0,
        "distortion": 0,
        "source_type": source_type,
        "evolution_stage": 0,
    }

    PLAYER_MONSTERS[telegram_id].append(monster)
    _normalize_active_monster_state(telegram_id)
    return monster


def get_player_monsters(telegram_id: int):
    _ensure_player_collections(telegram_id)
    monsters = PLAYER_MONSTERS[telegram_id]

    for monster in monsters:
        _migrate_monster_fields(monster)

    _normalize_active_monster_state(telegram_id)
    return monsters


def get_active_monster(telegram_id: int):
    for monster in get_player_monsters(telegram_id):
        if monster.get("is_active"):
            return _migrate_monster_fields(monster)
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
    monsters = get_player_monsters(telegram_id)
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

        level_ups.append(
            {
                "level": monster["level"],
                "max_hp": monster["max_hp"],
                "attack": monster["attack"],
            }
        )

    return monster, level_ups


def set_active_monster(telegram_id: int, monster_id: int):
    target = None

    for monster in get_player_monsters(telegram_id):
        monster["is_active"] = False
        _migrate_monster_fields(monster)

        if monster["id"] == monster_id:
            target = monster

    if target:
        target["is_active"] = True

    _normalize_active_monster_state(telegram_id)
    return target


def get_monster_by_id(telegram_id: int, monster_id: int):
    for monster in get_player_monsters(telegram_id):
        if monster["id"] == monster_id:
            return _migrate_monster_fields(monster)
    return None
