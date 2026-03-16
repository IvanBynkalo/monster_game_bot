
from database.models import Player

PLAYERS = {}
PLAYER_MONSTERS = {}
PLAYER_EMOTIONS = {}
PLAYER_ITEMS = {}
PLAYER_RESOURCES = {}

PLAYER_BOARD_QUESTS = {}

# --- TYPE SYSTEM ---

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
        return "⚡ Суперэффективная атака!"
    if mult < 1:
        return "🛡 Цель сопротивляется урону."
    return ""


# --- MONSTER REGISTRY ---

def register_monster_seen(telegram_id: int, monster_name: str):
    player = get_player(telegram_id)

    if not hasattr(player, "seen_monsters"):
        player.seen_monsters = set()

    player.seen_monsters.add(monster_name)


# --- QUESTS ---

def _default_board_quests():
    return {
        "guild_hunt": {
            "progress": 0,
            "completed": False,
            "target": 3,
            "title": "Охота гильдии",
            "reward_gold": 40,
            "reward_exp": 15,
        },
        "guild_gather": {
            "progress": 0,
            "completed": False,
            "target": 5,
            "title": "Сбор ресурсов",
            "reward_gold": 30,
            "reward_exp": 10,
        }
    }


# --- INJURIES SYSTEM ---

def tick_player_injuries(telegram_id: int):
    player = get_player(telegram_id)

    if not player:
        return

    if not hasattr(player, "injury_turns"):
        player.injury_turns = 0

    if player.injury_turns > 0:
        player.injury_turns -= 1


# --- PLAYER ---

def get_player(telegram_id: int):

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


# --- MONSTERS ---

def get_player_monsters(telegram_id):

    if telegram_id not in PLAYER_MONSTERS:
        PLAYER_MONSTERS[telegram_id] = []

    return PLAYER_MONSTERS[telegram_id]


def add_player_monster(telegram_id, monster):

    monsters = get_player_monsters(telegram_id)
    monsters.append(monster)


# --- GOLD ---

def add_gold(telegram_id, amount):

    player = get_player(telegram_id)
    player.gold += amount


def remove_gold(telegram_id, amount):

    player = get_player(telegram_id)
    player.gold = max(0, player.gold - amount)
