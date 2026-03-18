from database.models import Player

PLAYERS = {}
PENDING_ENCOUNTERS = {}
PLAYER_MONSTERS = {}
PLAYER_EMOTIONS = {}
PLAYER_QUESTS = {}
PLAYER_STORY = {}
PLAYER_ACTION_FLAGS = {}
PLAYER_ITEMS = {}
PLAYER_CODEX = {}
PLAYER_RELICS = {}
PLAYER_RESOURCES = {}
PLAYER_CRAFT_QUESTS = {}
PLAYER_EXTRA_QUESTS = {}
PLAYER_BOARD_QUESTS = {}
PLAYER_GUILD_QUESTS = {}
MARKET_ITEMS = {}
MARKET_MONSTERS = {}
NEXT_MONSTER_ID = 1
PLAYER_UI = {}
PLAYER_UI = {}

DEFAULT_EMOTIONS = {"rage": 0, "fear": 0, "instinct": 0, "inspiration": 0}

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
    "veteran_scout": {
        "title": "Опытный разведчик",
        "description": "Исследуй мир 8 раз.",
        "target_type": "explore",
        "target_value": 8,
        "reward_gold": 45,
        "reward_exp": 20,
    },
    "field_hunter": {
        "title": "Полевой охотник",
        "description": "Победи 6 монстров в бою.",
        "target_type": "win",
        "target_value": 6,
        "reward_gold": 55,
        "reward_exp": 24,
    },
    "fields_explorer": {
        "title": "Разведка лугов",
        "description": "Исследуй Изумрудные поля 4 раза.",
        "target_type": "explore",
        "target_value": 4,
        "reward_gold": 60,
        "reward_exp": 28,
    },
    "hills_miner": {
        "title": "Рудная жила",
        "description": "Собери 5 ресурсов в Каменных холмах.",
        "target_type": "explore",
        "target_value": 5,
        "reward_gold": 65,
        "reward_exp": 30,
    },
    "marsh_survivor": {
        "title": "Выживание в болотах",
        "description": "Победи 3 монстров в Болоте теней.",
        "target_type": "win",
        "target_value": 3,
        "reward_gold": 70,
        "reward_exp": 32,
    },
    "monster_research": {
        "title": "Исследователь видов",
        "description": "Поймай 5 монстров.",
        "target_type": "capture",
        "target_value": 5,
        "reward_gold": 60,
        "reward_exp": 26,
    },
}

STARTER_QUEST_CHAIN = [
    "first_steps",
    "first_hunt",
    "collector",
    "veteran_scout",
    "field_hunter",
    "fields_explorer",
    "hills_miner",
    "marsh_survivor",
    "monster_research",
]

STORY_QUESTS = [
    {
        "id": "forest_echo",
        "title": "Шёпот леса",
        "description": "Исследуй Тёмный лес 2 раза.",
        "requirements": {"location_slug": "dark_forest", "explore_count": 2},
        "reward_gold": 25,
        "reward_exp": 12,
        "reward_text": "След уходит в Болото теней.",
    },
    {
        "id": "swamp_sign",
        "title": "Тени у воды",
        "description": "Доберись до Болота теней и исследуй его 1 раз.",
        "requirements": {"location_slug": "shadow_swamp", "explore_count": 1},
        "reward_gold": 35,
        "reward_exp": 16,
        "reward_text": "Голоса ведут к Вулкану ярости.",
    },
    {
        "id": "volcano_trial",
        "title": "Испытание жаром",
        "description": "Доберись до Вулкана ярости и победи там 1 монстра.",
        "requirements": {"location_slug": "volcano_wrath", "win_count": 1},
        "reward_gold": 50,
        "reward_exp": 25,
        "reward_text": "Первый акт истории региона завершён.",
    },
]


def _default_story():
    return {
        "current_index": 0,
        "completed_ids": [],
        "forest_echo": {"explore_count": 0, "win_count": 0, "visited": False},
        "swamp_sign": {"explore_count": 0, "win_count": 0, "visited": False},
        "volcano_trial": {"explore_count": 0, "win_count": 0, "visited": False},
    }


def _default_craft_quests():
    return {
        "craft_big_potion": {
            "progress": 0,
            "completed": False,
            "craft_key": "big_potion",
            "count": 1,
            "title": "Полевой алхимик",
            "reward_gold": 35,
            "reward_exp": 12,
        },
        "craft_poison_trap": {
            "progress": 0,
            "completed": False,
            "craft_key": "poison_trap",
            "count": 1,
            "title": "Опасная приманка",
            "reward_gold": 50,
            "reward_exp": 16,
        },
    }


def _default_extra_quests():
    return {
        "extra_first_gather": {
            "progress": 0,
            "completed": False,
            "action_type": "gather",
            "count": 3,
            "title": "Первые находки",
            "reward_gold": 25,
            "reward_exp": 10,
        },
        "extra_first_craft": {
            "progress": 0,
            "completed": False,
            "action_type": "craft",
            "count": 1,
            "title": "Первый рецепт",
            "reward_gold": 20,
            "reward_exp": 10,
        },
        "extra_survivor": {
            "progress": 0,
            "completed": False,
            "action_type": "win",
            "count": 4,
            "title": "Выживший",
            "reward_gold": 40,
            "reward_exp": 18,
        },
    }


def _default_board_quests():
    return {
        "board_hunt_small": {
            "progress": 0,
            "completed": False,
            "action_type": "win",
            "count": 3,
            "title": "Заказ охотников",
            "reward_gold": 45,
            "reward_exp": 18,
        },
        "board_capture_live": {
            "progress": 0,
            "completed": False,
            "action_type": "capture",
            "count": 2,
            "title": "Живой экземпляр",
            "reward_gold": 55,
            "reward_exp": 22,
        },
        "board_field_work": {
            "progress": 0,
            "completed": False,
            "action_type": "explore",
            "count": 5,
            "title": "Полевые работы",
            "reward_gold": 50,
            "reward_exp": 20,
        },
    }


def _default_guild_quests():
    return {
        "hunters_trial": {
            "progress": 0,
            "completed": False,
            "guild_key": "hunters",
            "action_type": "win",
            "count": 3,
            "title": "Испытание ловцов",
            "reward_gold": 50,
            "reward_exp": 20,
        },
        "gatherers_route": {
            "progress": 0,
            "completed": False,
            "guild_key": "gatherers",
            "action_type": "gather",
            "count": 4,
            "title": "Маршрут собирателя",
            "reward_gold": 45,
            "reward_exp": 18,
        },
        "geologists_find": {
            "progress": 0,
            "completed": False,
            "guild_key": "geologists",
            "action_type": "explore",
            "count": 4,
            "title": "Находка геолога",
            "reward_gold": 45,
            "reward_exp": 18,
        },
        "alchemists_work": {
            "progress": 0,
            "completed": False,
            "guild_key": "alchemists",
            "action_type": "craft",
            "count": 2,
            "title": "Работа алхимика",
            "reward_gold": 50,
            "reward_exp": 22,
        },
    }


def _ensure_market_defaults():
    MARKET_ITEMS.setdefault("small_potion", {"base_price": 14, "demand": 0.0, "updated_at": 0.0})
    MARKET_ITEMS.setdefault("energy_capsule", {"base_price": 18, "demand": 0.0, "updated_at": 0.0})
    MARKET_ITEMS.setdefault("basic_trap", {"base_price": 20, "demand": 0.0, "updated_at": 0.0})
    MARKET_MONSTERS.setdefault("forest_sprite", {"base_price": 90, "demand": 0.0, "updated_at": 0.0})
    MARKET_MONSTERS.setdefault("swamp_hunter", {"base_price": 105, "demand": 0.0, "updated_at": 0.0})
    MARKET_MONSTERS.setdefault("ember_fang", {"base_price": 160, "demand": 0.0, "updated_at": 0.0})


def _apply_market_decay(entry: dict, decay_per_hour: float = 0.35):
    import time

    now = time.time()
    updated_at = entry.get("updated_at", 0.0)
    if not updated_at:
        entry["updated_at"] = now
        return entry

    hours = max(0.0, (now - updated_at) / 3600.0)
    if hours > 0:
        entry["demand"] = max(0.0, entry.get("demand", 0.0) - hours * decay_per_hour)
        entry["updated_at"] = now
    return entry


def get_market_item_entry(item_slug: str):
    _ensure_market_defaults()
    return _apply_market_decay(MARKET_ITEMS[item_slug])


def get_market_monster_entry(monster_slug: str):
    _ensure_market_defaults()
    return _apply_market_decay(MARKET_MONSTERS[monster_slug])


def get_market_item_price(item_slug: str):
    entry = get_market_item_entry(item_slug)
    return max(1, int(round(entry["base_price"] * (1 + 0.12 * entry.get("demand", 0.0)))))


def get_market_monster_price(monster_slug: str):
    entry = get_market_monster_entry(monster_slug)
    return max(1, int(round(entry["base_price"] * (1 + 0.10 * entry.get("demand", 0.0)))))


def purchase_market_item(telegram_id: int, item_slug: str):
    player = get_player(telegram_id)
    if not player:
        return None

    price = get_market_item_price(item_slug)
    if player.gold < price:
        return None

    player.gold -= price
    entry = get_market_item_entry(item_slug)
    entry["demand"] = min(10.0, entry.get("demand", 0.0) + 1.0)
    return price


def purchase_market_monster(telegram_id: int, monster_slug: str):
    player = get_player(telegram_id)
    if not player:
        return None

    price = get_market_monster_price(monster_slug)
    if player.gold < price:
        return None

    player.gold -= price
    entry = get_market_monster_entry(monster_slug)
    entry["demand"] = min(10.0, entry.get("demand", 0.0) + 1.0)
    return price


def _default_ui_state():
    return {
        "screen": "main",
        "context": {},
    }


def get_ui_state(telegram_id: int):
    return PLAYER_UI.setdefault(telegram_id, _default_ui_state())


def set_ui_screen(telegram_id: int, screen: str, **context):
    state = get_ui_state(telegram_id)
    state["screen"] = screen
    state["context"] = context
    return state


def get_ui_screen(telegram_id: int) -> str:
    return get_ui_state(telegram_id).get("screen", "main")


def get_player(telegram_id: int):
    player = PLAYERS.get(telegram_id)
    if player:
        for attr, default in {
            "alchemist_level": 1,
            "merchant_level": 1,
            "gatherer_level": 1,
            "hunter_level": 1,
            "geologist_level": 1,
            "gatherer_exp": 0,
            "hunter_exp": 0,
            "geologist_exp": 0,
            "alchemist_exp": 0,
            "merchant_exp": 0,
            "strength": 1,
            "agility": 1,
            "intellect": 1,
            "stat_points": 0,
            "bag_capacity": 12,
            "location_slug": "silver_city",
            "current_district_slug": "market_square",
            "hp": 30,
            "max_hp": 30,
            "is_defeated": False,
            "injury_turns": 0,
            "birth_cooldown_actions": 0,
        }.items():
            if not hasattr(player, attr):
                setattr(player, attr, default)
    return player


def _ensure_player_collections(telegram_id: int):
    PLAYER_MONSTERS.setdefault(telegram_id, [])
    PLAYER_EMOTIONS.setdefault(telegram_id, DEFAULT_EMOTIONS.copy())
    PLAYER_QUESTS.setdefault(
        telegram_id,
        {k: {"progress": 0, "completed": False, **v} for k, v in STARTER_QUESTS.items()},
    )
    PLAYER_STORY.setdefault(telegram_id, _default_story())
    PLAYER_ACTION_FLAGS.setdefault(telegram_id, {})
    PLAYER_ITEMS.setdefault(telegram_id, {"small_potion": 2, "energy_capsule": 1, "basic_trap": 3})
    PLAYER_RESOURCES.setdefault(telegram_id, {})
    PLAYER_CRAFT_QUESTS.setdefault(telegram_id, _default_craft_quests())
    PLAYER_BOARD_QUESTS.setdefault(telegram_id, _default_board_quests())
    PLAYER_GUILD_QUESTS.setdefault(telegram_id, _default_guild_quests())
    PLAYER_EXTRA_QUESTS.setdefault(telegram_id, _default_extra_quests())
    PLAYER_CODEX.setdefault(telegram_id, set())
    PLAYER_RELICS.setdefault(telegram_id, [])


def create_player(telegram_id: int, name: str):
    player = Player(telegram_id=telegram_id, name=name)
    PLAYERS[telegram_id] = player
    _ensure_player_collections(telegram_id)
    get_ui_state(telegram_id)
    return player


def reset_player_state(telegram_id: int, name: str = "Игрок"):
    PLAYERS[telegram_id] = Player(telegram_id=telegram_id, name=name)
    PLAYER_MONSTERS[telegram_id] = []
    PLAYER_EMOTIONS[telegram_id] = DEFAULT_EMOTIONS.copy()
    PLAYER_QUESTS[telegram_id] = {
        k: {"progress": 0, "completed": False, **v} for k, v in STARTER_QUESTS.items()
    }
    PLAYER_STORY[telegram_id] = _default_story()
    PLAYER_ACTION_FLAGS[telegram_id] = {}
    PLAYER_ITEMS[telegram_id] = {"small_potion": 2, "energy_capsule": 1, "basic_trap": 3}
    PLAYER_RESOURCES[telegram_id] = {}
    PLAYER_CRAFT_QUESTS[telegram_id] = _default_craft_quests()
    PLAYER_EXTRA_QUESTS[telegram_id] = _default_extra_quests()
    PLAYER_BOARD_QUESTS[telegram_id] = _default_board_quests()
    PLAYER_GUILD_QUESTS[telegram_id] = _default_guild_quests()
    PLAYER_CODEX[telegram_id] = set()
    PLAYER_RELICS[telegram_id] = []
    PENDING_ENCOUNTERS.pop(telegram_id, None)
    set_ui_screen(telegram_id, "main")
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


def get_temp_effects(telegram_id: int):
    flags = PLAYER_ACTION_FLAGS.setdefault(telegram_id, {})
    return flags.setdefault("effects", {})


def set_temp_effect(telegram_id: int, effect_name: str, duration: int):
    effects = get_temp_effects(telegram_id)
    effects[effect_name] = max(duration, effects.get(effect_name, 0))
    return effects


def has_temp_effect(telegram_id: int, effect_name: str):
    return get_temp_effects(telegram_id).get(effect_name, 0) > 0


def tick_temp_effects(telegram_id: int):
    effects = get_temp_effects(telegram_id)
    expired = []
    for key in list(effects.keys()):
        effects[key] -= 1
        if effects[key] <= 0:
            expired.append(key)
            effects.pop(key, None)
    return expired


def clear_temp_effect(telegram_id: int, effect_name: str):
    effects = get_temp_effects(telegram_id)
    effects.pop(effect_name, None)
    return effects


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
    state["visited"] = state["visited"] or current_location_slug == quest["requirements"]["location_slug"]

    if current_location_slug == quest["requirements"]["location_slug"]:
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
    quests = PLAYER_QUESTS[telegram_id]

    for key, value in STARTER_QUESTS.items():
        if key not in quests:
            quests[key] = {
                "progress": 0,
                "completed": False,
                "active": False,
                "source": "starter",
                **value,
            }

    # Активируем только первый незавершённый стартовый квест
    active_found = False
    for quest_id in STARTER_QUEST_CHAIN:
        quest = quests[quest_id]

        if quest.get("completed"):
            quest["active"] = False
            continue

        if not active_found:
            quest["active"] = True
            active_found = True
        else:
            quest["active"] = False

    return quests

def get_active_player_quests(telegram_id: int):
    quests = get_player_quests(telegram_id)
    active = {}

    for quest_id, quest in quests.items():
        if quest.get("active") and not quest.get("completed"):
            active[quest_id] = quest

    return active


def progress_quests(telegram_id: int, action_type: str):
    quests = get_player_quests(telegram_id)
    completed_now = []

    for quest_id in STARTER_QUEST_CHAIN:
        quest = quests[quest_id]

        if quest.get("completed"):
            continue
        if not quest.get("active"):
            continue
        if quest["target_type"] != action_type:
            continue

        quest["progress"] += 1

        if quest["progress"] >= quest["target_value"]:
            quest["completed"] = True
            quest["active"] = False
            completed_now.append((quest_id, quest))

            # сразу открываем следующий квест в цепочке
            current_index = STARTER_QUEST_CHAIN.index(quest_id)
            if current_index + 1 < len(STARTER_QUEST_CHAIN):
                next_quest_id = STARTER_QUEST_CHAIN[current_index + 1]
                if not quests[next_quest_id].get("completed"):
                    quests[next_quest_id]["active"] = True

        # только один активный стартовый квест обрабатываем за раз
        break

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
        "silver_city": "market_square",
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
        player.stat_points += 2
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


def add_resource(telegram_id: int, slug: str, count: int):
    inv = PLAYER_RESOURCES.setdefault(telegram_id, {})
    inv[slug] = inv.get(slug, 0) + count


def spend_resource(telegram_id: int, slug: str, count: int):
    inv = PLAYER_RESOURCES.setdefault(telegram_id, {})
    current = inv.get(slug, 0)
    if current < count:
        return False
    inv[slug] = current - count
    return True


def get_resources(telegram_id: int):
    _ensure_player_collections(telegram_id)
    return PLAYER_RESOURCES[telegram_id]


def progress_crafting_quests(telegram_id: int, craft_key: str):
    _ensure_player_collections(telegram_id)
    quests = PLAYER_CRAFT_QUESTS[telegram_id]
    completed_now = []

    for quest in quests.values():
        if quest["completed"] or quest["craft_key"] != craft_key:
            continue
        quest["progress"] += 1
        if quest["progress"] >= quest["count"]:
            quest["completed"] = True
            completed_now.append(quest)

    return completed_now


def get_player_guild_quests(telegram_id: int):
    _ensure_player_collections(telegram_id)
    return PLAYER_GUILD_QUESTS[telegram_id]


def progress_guild_quests(
    telegram_id: int,
    action_type: str,
    guild_key: str | None = None,
    amount: int = 1,
):
    quests = get_player_guild_quests(telegram_id)
    completed_now = []

    for quest_id, quest in quests.items():
        if quest.get("completed"):
            continue

        quest_action_type = quest.get("target_type") or quest.get("action_type")
        quest_guild_key = quest.get("guild_key") or quest.get("guild")

        if quest_action_type and quest_action_type != action_type:
            continue

        if guild_key and quest_guild_key and quest_guild_key != guild_key:
            continue

        current_progress = quest.get("progress", 0)
        target_value = quest.get("target_value", quest.get("count", 1))
        quest["progress"] = current_progress + amount

        if quest["progress"] >= target_value:
            quest["completed"] = True
            completed_now.append((quest_id, quest))

    return completed_now


def progress_extra_quests(
    telegram_id: int,
    action_type: str,
    amount: int = 1,
):
    extra_quests = PLAYER_EXTRA_QUESTS.get(telegram_id)
    if not extra_quests:
        return []

    completed_now = []

    for quest_id, quest in extra_quests.items():
        if quest.get("completed"):
            continue

        quest_action = quest.get("target_type") or quest.get("action_type")
        if quest_action and quest_action != action_type:
            continue

        current = quest.get("progress", 0)
        target = quest.get("target_value", quest.get("count", 1))
        quest["progress"] = current + amount

        if quest["progress"] >= target:
            quest["completed"] = True
            completed_now.append((quest_id, quest))

    return completed_now


def progress_board_quests(
    telegram_id: int,
    action_type: str,
    amount: int = 1,
):
    board_quests = PLAYER_BOARD_QUESTS.get(telegram_id)
    if not board_quests:
        return []

    completed_now = []

    for quest_id, quest in board_quests.items():
        if quest.get("completed"):
            continue

        quest_action = quest.get("target_type") or quest.get("action_type")
        if quest_action and quest_action != action_type:
            continue

        current = quest.get("progress", 0)
        target = quest.get("target_value", quest.get("count", 1))
        quest["progress"] = current + amount

        if quest["progress"] >= target:
            quest["completed"] = True
            completed_now.append((quest_id, quest))

    return completed_now


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


def get_damage_multiplier(attacker_type: str | None, defender_type: str | None) -> float:
    if not attacker_type or not defender_type:
        return 1.0

    chart = {
        ("flame", "nature"): 1.5,
        ("nature", "storm"): 1.25,
        ("storm", "shadow"): 1.25,
        ("shadow", "spirit"): 1.25,
        ("spirit", "bone"): 1.25,
        ("bone", "flame"): 1.25,
        ("echo", "void"): 1.25,
        ("void", "echo"): 1.25,
        ("nature", "flame"): 0.75,
        ("storm", "nature"): 0.85,
        ("shadow", "storm"): 0.85,
        ("spirit", "shadow"): 0.85,
        ("bone", "spirit"): 0.85,
        ("flame", "bone"): 0.85,
    }

    return chart.get((attacker_type, defender_type), 1.0)


def render_type_hint(attacker_type: str | None, defender_type: str | None) -> str:
    multiplier = get_damage_multiplier(attacker_type, defender_type)

    if multiplier >= 1.5:
        return "🔥 Очень эффективно"
    if multiplier > 1.0:
        return "⚔️ Эффективно"
    if multiplier < 1.0:
        return "🛡 Слабо"
    return "➖ Без преимущества"


def _migrate_monster_fields(monster: dict):
    from game.monster_abilities import MONSTER_ABILITIES

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
    monster.setdefault("monster_type", _guess_monster_type(monster.get("name", ""), monster.get("mood", "")))
    monster.setdefault("abilities", MONSTER_ABILITIES.get(monster.get("name", ""), []).copy())
    return monster


def add_captured_monster(
    telegram_id: int,
    name: str,
    rarity: str,
    mood: str,
    hp: int,
    attack: int,
    source_type: str = "wild",
):
    global NEXT_MONSTER_ID

    _ensure_player_collections(telegram_id)
    is_first = len(PLAYER_MONSTERS[telegram_id]) == 0

    monster = {
        "id": NEXT_MONSTER_ID,
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
        "abilities": [],
    }

    NEXT_MONSTER_ID += 1
    PLAYER_MONSTERS[telegram_id].append(monster)
    return monster


def get_player_monsters(telegram_id: int):
    _ensure_player_collections(telegram_id)
    monsters = PLAYER_MONSTERS[telegram_id]
    for monster in monsters:
        _migrate_monster_fields(monster)
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

    return target


def get_monster_by_id(telegram_id: int, monster_id: int):
    for monster in get_player_monsters(telegram_id):
        if monster["id"] == monster_id:
            return _migrate_monster_fields(monster)
    return None


def spend_stat_point(telegram_id: int, stat_name: str):
    player = get_player(telegram_id)
    if not player or player.stat_points <= 0:
        return False
    if stat_name not in {"strength", "agility", "intellect"}:
        return False

    setattr(player, stat_name, getattr(player, stat_name) + 1)
    player.stat_points -= 1
    return True


def get_resources_count_total(telegram_id: int):
    return sum(max(0, value) for value in get_resources(telegram_id).values())


PROFESSION_LEVEL_CAP = 10

PROFESSION_FIELD_MAP = {
    "gatherer": ("gatherer_level", "gatherer_exp"),
    "hunter": ("hunter_level", "hunter_exp"),
    "geologist": ("geologist_level", "geologist_exp"),
    "alchemist": ("alchemist_level", "alchemist_exp"),
    "merchant": ("merchant_level", "merchant_exp"),
}


def get_profession_exp_required(level: int) -> int:
    # Сколько XP нужно, чтобы перейти с текущего уровня на следующий
    # 1->2: 10, 2->3: 14, 3->4: 18 ...
    return 6 + level * 4


def get_profession_state(player, kind: str):
    fields = PROFESSION_FIELD_MAP.get(kind)
    if not fields:
        return None

    level_field, exp_field = fields
    level = getattr(player, level_field, 1)
    exp = getattr(player, exp_field, 0)

    return {
        "kind": kind,
        "level_field": level_field,
        "exp_field": exp_field,
        "level": level,
        "exp": exp,
        "exp_to_next": 0 if level >= PROFESSION_LEVEL_CAP else get_profession_exp_required(level),
    }


def improve_profession_from_action(telegram_id: int, kind: str, amount: int = 1):
    player = get_player(telegram_id)
    if not player:
        return None

    fields = PROFESSION_FIELD_MAP.get(kind)
    if not fields:
        return None

    level_field, exp_field = fields

    old_level = getattr(player, level_field, 1)
    old_exp = getattr(player, exp_field, 0)

    if old_level >= PROFESSION_LEVEL_CAP:
        return {
            "kind": kind,
            "leveled_up": False,
            "level_before": old_level,
            "level_after": old_level,
            "exp_before": old_exp,
            "exp_after": old_exp,
            "exp_to_next": 0,
            "is_max_level": True,
            "gained_exp": 0,
        }

    new_exp = old_exp + max(0, amount)
    new_level = old_level
    leveled_up = False

    while new_level < PROFESSION_LEVEL_CAP:
        need = get_profession_exp_required(new_level)
        if new_exp < need:
            break
        new_exp -= need
        new_level += 1
        leveled_up = True

    if new_level >= PROFESSION_LEVEL_CAP:
        new_level = PROFESSION_LEVEL_CAP
        new_exp = 0

    setattr(player, level_field, new_level)
    setattr(player, exp_field, new_exp)

    return {
        "kind": kind,
        "leveled_up": leveled_up,
        "level_before": old_level,
        "level_after": new_level,
        "exp_before": old_exp,
        "exp_after": new_exp,
        "exp_to_next": 0 if new_level >= PROFESSION_LEVEL_CAP else get_profession_exp_required(new_level),
        "is_max_level": new_level >= PROFESSION_LEVEL_CAP,
        "gained_exp": max(0, amount),
    }


def get_player_codex(telegram_id: int):
    return PLAYER_CODEX.setdefault(telegram_id, set())


def register_monster_seen(telegram_id: int, monster_name: str):
    codex = get_player_codex(telegram_id)
    codex.add(monster_name)
    return codex


def get_player_relics(telegram_id: int):
    return PLAYER_RELICS.setdefault(telegram_id, [])


def add_relic(telegram_id: int, relic_slug: str):
    relics = get_player_relics(telegram_id)
    if relic_slug not in relics:
        relics.append(relic_slug)
    return relics


def has_relic(telegram_id: int, relic_slug: str):
    return relic_slug in get_player_relics(telegram_id)


def damage_player_hp(telegram_id: int, amount: int):
    player = get_player(telegram_id)
    if not player or amount <= 0:
        return player

    player.hp = max(0, player.hp - amount)
    if player.hp <= 0:
        player.is_defeated = True
    return player


def heal_player_hp(telegram_id: int, amount: int):
    player = get_player(telegram_id)
    if not player or amount <= 0:
        return player

    player.hp = min(player.max_hp, player.hp + amount)
    if player.hp > 1:
        player.is_defeated = False
    return player


def defeat_player_state(telegram_id: int, gold_loss: int = 0):
    player = get_player(telegram_id)
    if not player:
        return None

    player.is_defeated = True
    player.hp = 1
    player.injury_turns = max(getattr(player, "injury_turns", 0), 5)

    if gold_loss > 0:
        player.gold = max(0, player.gold - gold_loss)

    player.location_slug = "silver_city"
    player.current_district_slug = "market_square"
    return player


def tick_player_injuries(telegram_id: int, amount: int = 1):
    player = get_player(telegram_id)
    if not player:
        return None

    if getattr(player, "injury_turns", 0) > 0:
        player.injury_turns = max(0, player.injury_turns - amount)
    return player


def clear_player_injuries(telegram_id: int):
    player = get_player(telegram_id)
    if not player:
        return None

    player.injury_turns = 0
    player.is_defeated = False
    player.hp = player.max_hp
    return player
# =========================
# 🧱 SQLITE: ГОРОДСКИЕ ЗАКАЗЫ
# =========================

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "game.db"


def _get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_city_orders_db():
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_city_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                order_slug TEXT NOT NULL,
                title TEXT NOT NULL,
                goal_text TEXT NOT NULL,
                reward_gold INTEGER NOT NULL,
                reward_exp INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


# авто-инициализация при старте
_init_city_orders_db()


# =========================
# 📦 CRUD ЗАКАЗОВ
# =========================

def get_active_city_orders(telegram_id: int):
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM player_city_orders
            WHERE telegram_id = ? AND status = 'active'
            ORDER BY created_at ASC
            """,
            (telegram_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def count_active_city_orders(telegram_id: int) -> int:
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) as cnt
            FROM player_city_orders
            WHERE telegram_id = ? AND status = 'active'
            """,
            (telegram_id,),
        ).fetchone()

    return int(row["cnt"] if row else 0)


def has_active_city_order(telegram_id: int, order_slug: str) -> bool:
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM player_city_orders
            WHERE telegram_id = ? AND order_slug = ? AND status = 'active'
            LIMIT 1
            """,
            (telegram_id, order_slug),
        ).fetchone()

    return row is not None


def add_city_order(
    telegram_id: int,
    order_slug: str,
    title: str,
    goal_text: str,
    reward_gold: int,
    reward_exp: int,
):
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO player_city_orders (
                telegram_id,
                order_slug,
                title,
                goal_text,
                reward_gold,
                reward_exp,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'active')
            """,
            (telegram_id, order_slug, title, goal_text, reward_gold, reward_exp),
        )
        conn.commit()


def complete_city_order(order_id: int):
    with _get_connection() as conn:
        conn.execute(
            """
            UPDATE player_city_orders
            SET status = 'completed'
            WHERE id = ?
            """,
            (order_id,),
        )
        conn.commit()


def clear_active_city_orders(telegram_id: int):
    with _get_connection() as conn:
        conn.execute(
            """
            DELETE FROM player_city_orders
            WHERE telegram_id = ? AND status = 'active'
            """,
            (telegram_id,),
        )
        conn.commit()
