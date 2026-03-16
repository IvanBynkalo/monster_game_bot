# database/repositories.py

from database.models import Player

PLAYERS = {}
PLAYER_MONSTERS = {}
PLAYER_ITEMS = {}
PLAYER_RESOURCES = {}
PLAYER_BOARD_QUESTS = {}

# -----------------------------
# TYPE SYSTEM
# -----------------------------

TYPE_DAMAGE = {
    ("Эхо", "Тень"): 1.2,
    ("Тень", "Эхо"): 0.8,
    ("Свет", "Тень"): 1.4,
    ("Тень", "Свет"): 0.6,
    ("Эхо", "Свет"): 1.1,
    ("Свет", "Эхо"): 0.9,
}


def get_damage_multiplier(attacker_type: str, defender_type: str) -> float:
    return TYPE_DAMAGE.get((attacker_type, defender_type), 1.0)


def render_type_hint(attacker_type: str, defender_type: str) -> str:

    mult = get_damage_multiplier(attacker_type, defender_type)

    if mult > 1:
        return "⚡ Суперэффективно!"
    elif mult < 1:
        return "🛡 Слабая атака"
    else:
        return ""


# -----------------------------
# PLAYER
# -----------------------------

def get_player(telegram_id):

    if telegram_id not in PLAYERS:

        player = Player(
            telegram_id=telegram_id,
            gold=50,
            energy=10,
            location_slug="silver_city"
        )

        player.hp = 30
        player.max_hp = 30

        player.injury_turns = 0
        player.is_defeated = False

        PLAYERS[telegram_id] = player

    return PLAYERS[telegram_id]


# -----------------------------
# MONSTERS
# -----------------------------

def get_player_monsters(telegram_id):

    if telegram_id not in PLAYER_MONSTERS:
        PLAYER_MONSTERS[telegram_id] = []

    return PLAYER_MONSTERS[telegram_id]


def add_player_monster(telegram_id, monster):

    monsters = get_player_monsters(telegram_id)
    monsters.append(monster)


def register_monster_seen(telegram_id, monster_name):

    player = get_player(telegram_id)

    if not hasattr(player, "seen_monsters"):
        player.seen_monsters = set()

    player.seen_monsters.add(monster_name)


# -----------------------------
# GOLD
# -----------------------------

def add_gold(telegram_id, amount):

    player = get_player(telegram_id)
    player.gold += amount


def remove_gold(telegram_id, amount):

    player = get_player(telegram_id)
    player.gold = max(0, player.gold - amount)


# -----------------------------
# QUEST BOARD
# -----------------------------

def _default_board_quests():

    return {
        "hunt": {
            "title": "Охота гильдии",
            "progress": 0,
            "target": 3,
            "completed": False,
            "reward_gold": 40,
            "reward_exp": 15
        },
        "gather": {
            "title": "Сбор ресурсов",
            "progress": 0,
            "target": 5,
            "completed": False,
            "reward_gold": 30,
            "reward_exp": 10
        }
    }


def get_board_quests(telegram_id):

    if telegram_id not in PLAYER_BOARD_QUESTS:
        PLAYER_BOARD_QUESTS[telegram_id] = _default_board_quests()

    return PLAYER_BOARD_QUESTS[telegram_id]


# -----------------------------
# INJURIES SYSTEM
# -----------------------------

def tick_player_injuries(telegram_id):

    player = get_player(telegram_id)

    if not hasattr(player, "injury_turns"):
        player.injury_turns = 0

    if player.injury_turns > 0:
        player.injury_turns -= 1


# -----------------------------
# ITEMS
# -----------------------------

def get_player_items(telegram_id):

    if telegram_id not in PLAYER_ITEMS:
        PLAYER_ITEMS[telegram_id] = {}

    return PLAYER_ITEMS[telegram_id]


def add_item(telegram_id, item, amount=1):

    items = get_player_items(telegram_id)

    if item not in items:
        items[item] = 0

    items[item] += amount


# -----------------------------
# RESOURCES
# -----------------------------

def get_player_resources(telegram_id):

    if telegram_id not in PLAYER_RESOURCES:
        PLAYER_RESOURCES[telegram_id] = {}

    return PLAYER_RESOURCES[telegram_id]


def add_resource(telegram_id, resource, amount=1):

    res = get_player_resources(telegram_id)

    if resource not in res:
        res[resource] = 0

    res[resource] += amount
