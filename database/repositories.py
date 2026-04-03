"""
repositories.py — полный слой доступа к данным на SQLite.
Все данные персистентны между перезапусками.
"""
import json
import time
import logging
from database.db import get_connection, json_get, json_set
from database.models import Player

logger = logging.getLogger(__name__)
events_logger = logging.getLogger("game_events")


def _log_repo_event(action: str, **kwargs):
    try:
        payload = " | ".join(f"{k}={kwargs[k]!r}" for k in sorted(kwargs))
        events_logger.info("REPO_%s | %s", action, payload)
    except Exception:
        logger.exception("REPO_LOG_EVENT_FAIL | action=%s", action)


# ─── Константы квестов ────────────────────────────────────────────────────────

STARTER_QUESTS = {
    "first_steps":      {"title": "Первые шаги",          "description": "Исследуй мир 3 раза.",            "target_type": "explore", "target_value": 3,  "reward_gold": 20, "reward_exp": 10},
    "first_hunt":       {"title": "Первая охота",          "description": "Победи 2 монстров в бою.",        "target_type": "win",     "target_value": 2,  "reward_gold": 25, "reward_exp": 12},
    "collector":        {"title": "Коллекционер",          "description": "Поймай 2 монстров.",              "target_type": "capture", "target_value": 2,  "reward_gold": 30, "reward_exp": 15},
    "veteran_scout":    {"title": "Опытный разведчик",     "description": "Исследуй мир 8 раз.",             "target_type": "explore", "target_value": 8,  "reward_gold": 45, "reward_exp": 20},
    "field_hunter":     {"title": "Полевой охотник",       "description": "Победи 6 монстров в бою.",        "target_type": "win",     "target_value": 6,  "reward_gold": 55, "reward_exp": 24},
    "fields_explorer":  {"title": "Разведка лугов",        "description": "Исследуй Изумрудные поля 4 раза.","target_type": "explore", "target_value": 4,  "reward_gold": 60, "reward_exp": 28},
    "hills_miner":      {"title": "Рудная жила",           "description": "Собери 5 ресурсов.",              "target_type": "explore", "target_value": 5,  "reward_gold": 65, "reward_exp": 30},
    "marsh_survivor":   {"title": "Выживание в болотах",   "description": "Победи 3 монстров в Болоте.",     "target_type": "win",     "target_value": 3,  "reward_gold": 70, "reward_exp": 32},
    "monster_research": {"title": "Исследователь видов",   "description": "Поймай 5 монстров.",              "target_type": "capture", "target_value": 5,  "reward_gold": 60, "reward_exp": 26},
}
STARTER_QUEST_CHAIN = ["first_steps","first_hunt","collector","veteran_scout","field_hunter","fields_explorer","hills_miner","marsh_survivor","monster_research"]

STORY_QUESTS = [
    {"id":"forest_echo",   "title":"Шёпот леса",       "description":"Исследуй Тёмный лес 2 раза.",           "requirements":{"location_slug":"dark_forest",    "explore_count":2},"reward_gold":25,"reward_exp":12,"reward_text":"След уходит в Болото теней."},
    {"id":"swamp_sign",    "title":"Тени у воды",       "description":"Исследуй Болото теней 1 раз.",          "requirements":{"location_slug":"shadow_swamp",   "explore_count":1},"reward_gold":35,"reward_exp":16,"reward_text":"Голоса ведут к Вулкану ярости."},
    {"id":"volcano_trial", "title":"Испытание жаром",   "description":"Победи монстра на Вулкане ярости.",     "requirements":{"location_slug":"volcano_wrath",  "win_count":1},    "reward_gold":50,"reward_exp":25,"reward_text":"Первый акт завершён."},
]

DEFAULT_CRAFT_QUESTS = {
    "craft_big_potion":  {"craft_key":"big_potion",  "count":1,"title":"Полевой алхимик",   "reward_gold":35,"reward_exp":12},
    "craft_poison_trap": {"craft_key":"poison_trap", "count":1,"title":"Опасная приманка",  "reward_gold":50,"reward_exp":16},
}
DEFAULT_EXTRA_QUESTS = {
    "extra_first_gather": {"action_type":"gather","count":3,"title":"Первые находки",   "reward_gold":25,"reward_exp":10},
    "extra_first_craft":  {"action_type":"craft", "count":1,"title":"Первый рецепт",    "reward_gold":20,"reward_exp":10},
    "extra_survivor":     {"action_type":"win",   "count":4,"title":"Выживший",         "reward_gold":40,"reward_exp":18},
}
DEFAULT_BOARD_QUESTS = {
    "board_hunt_small":   {"action_type":"win",     "count":3,"title":"Заказ охотников","reward_gold":45,"reward_exp":18},
    "board_capture_live": {"action_type":"capture", "count":2,"title":"Живой экземпляр","reward_gold":55,"reward_exp":22},
    "board_field_work":   {"action_type":"explore", "count":5,"title":"Полевые работы", "reward_gold":50,"reward_exp":20},
}
DEFAULT_GUILD_QUESTS = {
    "hunters_trial":    {"guild_key":"hunters",    "action_type":"win",    "count":3,"title":"Испытание ловцов",   "reward_gold":50,"reward_exp":20},
    "gatherers_route":  {"guild_key":"gatherers",  "action_type":"gather", "count":4,"title":"Маршрут собирателя","reward_gold":45,"reward_exp":18},
    "geologists_find":  {"guild_key":"geologists", "action_type":"explore","count":4,"title":"Находка геолога",   "reward_gold":45,"reward_exp":18},
    "alchemists_work":  {"guild_key":"alchemists", "action_type":"craft",  "count":2,"title":"Работа алхимика",   "reward_gold":50,"reward_exp":22},
}

DEFAULT_MARKET_ITEMS = {
    "small_potion":   {"base_price":14},
    "energy_capsule": {"base_price":18},
    "basic_trap":     {"base_price":20},
}
DEFAULT_MARKET_MONSTERS = {
    "forest_sprite":  {"base_price":90},
    "swamp_hunter":   {"base_price":105},
    "ember_fang":     {"base_price":160},
}
DEFAULT_CITY_RESOURCE_MARKET = {
    "forest_herb":   {"base_price":6,  "stock":8.0, "target_stock":8.0},
    "mushroom_cap":  {"base_price":7,  "stock":8.0, "target_stock":8.0},
    "silver_moss":   {"base_price":24, "stock":2.0, "target_stock":2.0},
    "swamp_moss":    {"base_price":8,  "stock":6.0, "target_stock":6.0},
    "toxic_spore":   {"base_price":11, "stock":5.0, "target_stock":5.0},
    "black_pearl":   {"base_price":28, "stock":1.0, "target_stock":1.0},
    "ember_stone":   {"base_price":10, "stock":5.0, "target_stock":5.0},
    "ash_leaf":      {"base_price":9,  "stock":5.0, "target_stock":5.0},
    "magma_core":    {"base_price":35, "stock":1.0, "target_stock":1.0},
    "field_grass":   {"base_price":6,  "stock":9.0, "target_stock":9.0},
    "sun_blossom":   {"base_price":9,  "stock":4.0, "target_stock":4.0},
    "dew_crystal":   {"base_price":26, "stock":2.0, "target_stock":2.0},
    "raw_ore":       {"base_price":10, "stock":6.0, "target_stock":6.0},
    "granite_shard": {"base_price":8,  "stock":6.0, "target_stock":6.0},
    "sky_crystal":   {"base_price":30, "stock":1.0, "target_stock":1.0},
    "bog_flower":    {"base_price":9,  "stock":4.0, "target_stock":4.0},
    "dark_resin":    {"base_price":11, "stock":4.0, "target_stock":4.0},
    "ghost_reed":    {"base_price":32, "stock":1.0, "target_stock":1.0},
    # Охотничий лут — продаётся у Скупщика ресурсов (Борт)
    "fox_fur":            {"base_price":12, "stock":5.0, "target_stock":5.0},
    "mouse_whisker":      {"base_price":8,  "stock":6.0, "target_stock":6.0},
    "wolf_fang":          {"base_price":18, "stock":4.0, "target_stock":4.0},
    "wolf_hide":          {"base_price":15, "stock":4.0, "target_stock":4.0},
    "rabbit_pelt":        {"base_price":7,  "stock":8.0, "target_stock":8.0},
    "deer_antler":        {"base_price":22, "stock":3.0, "target_stock":3.0},
    "bear_hide":          {"base_price":28, "stock":2.0, "target_stock":2.0},
    "boar_tusk":          {"base_price":20, "stock":3.0, "target_stock":3.0},
    "goat_horn":          {"base_price":14, "stock":5.0, "target_stock":5.0},
    "eagle_feather":      {"base_price":35, "stock":2.0, "target_stock":2.0},
    "lynx_claw":          {"base_price":30, "stock":2.0, "target_stock":2.0},
    "aurochs_horn":       {"base_price":25, "stock":3.0, "target_stock":3.0},
    "giant_bark":         {"base_price":16, "stock":4.0, "target_stock":4.0},
    "mountain_lion_pelt": {"base_price":40, "stock":2.0, "target_stock":2.0},
    "stone_beetle":       {"base_price":22, "stock":3.0, "target_stock":3.0},
    "lava_wolf_fang":     {"base_price":45, "stock":1.0, "target_stock":1.0},
    "croc_scale":         {"base_price":32, "stock":2.0, "target_stock":2.0},
    "shadow_wolf_fang":   {"base_price":50, "stock":1.0, "target_stock":1.0},
    "crystal_shard":      {"base_price":20, "stock":3.0, "target_stock":3.0},
}

# ─── Утилиты ──────────────────────────────────────────────────────────────────

def _row_to_player(row) -> Player | None:
    if not row:
        return None
    d = dict(row)
    p = Player.__new__(Player)
    for field in Player.__dataclass_fields__:
        val = d.get(field)
        if field == "is_defeated":
            setattr(p, field, bool(val))
        else:
            setattr(p, field, val if val is not None else Player.__dataclass_fields__[field].default)
    return p

def _guess_monster_type(name: str, mood: str) -> str:
    n = name.lower()
    if "плам" in n or "лав" in n or "магм" in n or mood == "rage": return "flame"
    if "тен" in n or "сумрач" in n or mood == "fear": return "shadow"
    if "гриб" in n or "мох" in n or "корн" in n: return "nature"
    if "дух" in n or "оракул" in n: return "spirit"
    if "кост" in n or "курган" in n: return "bone"
    if "бур" in n or "искр" in n: return "storm"
    if "эхо" in n or "шёп" in n: return "echo"
    return "void"

def _migrate_monster(d: dict) -> dict:
    from game.monster_abilities import MONSTER_ABILITIES
    d.setdefault("distortion", 0)
    d.setdefault("infection_type", None)
    d.setdefault("infection_stage", 0)
    d.setdefault("current_hp", d.get("hp", 1))
    d.setdefault("max_hp", d.get("hp", 1))
    d.setdefault("experience", 0)
    d.setdefault("evolution_stage", 0)
    d.setdefault("combo_mutation", None)
    d.setdefault("monster_type", _guess_monster_type(d.get("name",""), d.get("mood","")))
    if isinstance(d.get("abilities"), str):
        d["abilities"] = json_get(d["abilities"])
    d.setdefault("abilities", MONSTER_ABILITIES.get(d.get("name",""), []).copy())
    return d

def _monster_row_to_dict(row) -> dict:
    d = dict(row)
    d["abilities"] = json_get(d.get("abilities", "[]"))
    d["is_active"] = bool(d.get("is_active", 0))
    d["is_listed"] = bool(d.get("is_listed", 0))
    return _migrate_monster(d)

# ─── Игрок ────────────────────────────────────────────────────────────────────

def get_player(telegram_id: int) -> Player | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM players WHERE telegram_id=?", (telegram_id,)).fetchone()
    return _row_to_player(row)

def create_player(telegram_id: int, name: str) -> Player:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO players (telegram_id, name) VALUES (?,?)",
            (telegram_id, name)
        )
        # Default items
        for slug, amt in [("small_potion",2),("energy_capsule",1),("basic_trap",3)]:
            conn.execute("INSERT OR IGNORE INTO player_items (telegram_id,item_slug,amount) VALUES (?,?,?)", (telegram_id,slug,amt))
        # Default emotions
        conn.execute("INSERT OR IGNORE INTO player_emotions (telegram_id) VALUES (?)", (telegram_id,))
        # Default quests
        for i, qid in enumerate(STARTER_QUEST_CHAIN):
            q = STARTER_QUESTS[qid]
            conn.execute("""INSERT OR IGNORE INTO player_quests
                (telegram_id,quest_id,progress,completed,active,source)
                VALUES (?,?,0,0,?,?)""",
                (telegram_id, qid, 1 if i==0 else 0, "starter"))
        # Story
        conn.execute("INSERT OR IGNORE INTO player_story_index (telegram_id,current_index) VALUES (?,0)", (telegram_id,))
        for sq in STORY_QUESTS:
            conn.execute("INSERT OR IGNORE INTO player_story (telegram_id,story_id) VALUES (?,?)", (telegram_id, sq["id"]))
        # Craft/extra/board/guild quests
        for qid, q in DEFAULT_CRAFT_QUESTS.items():
            conn.execute("INSERT OR IGNORE INTO player_craft_quests (telegram_id,quest_id,craft_key,count,title,reward_gold,reward_exp) VALUES (?,?,?,?,?,?,?)",
                (telegram_id,qid,q["craft_key"],q["count"],q["title"],q["reward_gold"],q["reward_exp"]))
        for qid, q in DEFAULT_EXTRA_QUESTS.items():
            conn.execute("INSERT OR IGNORE INTO player_extra_quests (telegram_id,quest_id,action_type,count,title,reward_gold,reward_exp) VALUES (?,?,?,?,?,?,?)",
                (telegram_id,qid,q["action_type"],q["count"],q["title"],q["reward_gold"],q["reward_exp"]))
        for qid, q in DEFAULT_BOARD_QUESTS.items():
            conn.execute("INSERT OR IGNORE INTO player_board_quests (telegram_id,quest_id,action_type,count,title,reward_gold,reward_exp) VALUES (?,?,?,?,?,?,?)",
                (telegram_id,qid,q["action_type"],q["count"],q["title"],q["reward_gold"],q["reward_exp"]))
        for qid, q in DEFAULT_GUILD_QUESTS.items():
            conn.execute("INSERT OR IGNORE INTO player_guild_quests (telegram_id,quest_id,guild_key,action_type,count,title,reward_gold,reward_exp) VALUES (?,?,?,?,?,?,?,?)",
                (telegram_id,qid,q["guild_key"],q["action_type"],q["count"],q["title"],q["reward_gold"],q["reward_exp"]))
        # UI
        conn.execute("INSERT OR IGNORE INTO player_ui (telegram_id) VALUES (?)", (telegram_id,))
        # PvP
        conn.execute("INSERT OR IGNORE INTO player_pvp (telegram_id) VALUES (?)", (telegram_id,))
        conn.commit()
    return get_player(telegram_id)

def get_or_create_player(telegram_id: int, name: str) -> tuple[Player, bool]:
    p = get_player(telegram_id)
    if p:
        return p, False
    return create_player(telegram_id, name), True

def reset_player_state(telegram_id: int, name: str = "Игрок") -> Player:
    with get_connection() as conn:
        conn.execute("DELETE FROM player_monsters WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_emotions WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_items WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_resources WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_quests WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_story WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_story_index WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_craft_quests WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_extra_quests WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_board_quests WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_guild_quests WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM pending_encounters WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_action_flags WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_codex WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_relics WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_pvp WHERE telegram_id=?", (telegram_id,))
        # Сбрасываем основные поля игрока
        conn.execute("""UPDATE players SET
            name=?,location_slug='silver_city',current_region_slug='valley_of_emotions',
            current_district_slug='market_square',gold=120,level=1,experience=0,
            energy=12,birth_cooldown_actions=0,strength=1,agility=1,intellect=1,
            stat_points=0,gatherer_level=1,gatherer_exp=0,hunter_level=1,hunter_exp=0,
            geologist_level=1,geologist_exp=0,alchemist_level=1,alchemist_exp=0,
            merchant_level=1,merchant_exp=0,bag_capacity=12,hp=30,max_hp=30,
            is_defeated=0,injury_turns=0,daily_streak=0,last_login_date=\'\',
            last_energy_time=NULL,energy_notified=0,cartographer_level=1,cartographer_exp=0
            WHERE telegram_id=?""", (name, telegram_id))
        # Сбрасываем исследование локаций (картограф)
        conn.execute("DELETE FROM player_exploration WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM player_grid_exploration WHERE telegram_id=?", (telegram_id,))
        # Сбрасываем охотничьи квесты
        try:
            conn.execute("DELETE FROM player_hunting_quests WHERE telegram_id=?", (telegram_id,))
        except Exception:
            pass
        # Сбрасываем путешествие
        try:
            conn.execute("DELETE FROM player_travel WHERE telegram_id=?", (telegram_id,))
        except Exception:
            pass

        # ── Кристаллы и экипировка ────────────────────────────────────────────
        for tbl in [
            "player_crystals",
            "player_crystal_storage",
            "monster_crystal_bond",
            "player_belt_crystals",
            "player_equipment",
            "player_equipment_inventory",
        ]:
            try:
                conn.execute(f"DELETE FROM {tbl} WHERE telegram_id=?", (telegram_id,))
            except Exception:
                pass

        # ── Прогресс и достижения ─────────────────────────────────────────────
        for tbl in [
            "player_dungeon_progress",
            "player_bestiary",
            "player_weekly_quests",
            "player_quest_completions",
            "player_hunting_completions",
            "player_city_orders",
            "player_rift_tokens",
            "player_bags",
        ]:
            try:
                conn.execute(f"DELETE FROM {tbl} WHERE telegram_id=?", (telegram_id,))
            except Exception:
                pass

        # ── Сезонный пропуск и уведомления ───────────────────────────────────
        for tbl in ["player_season_pass", "player_notifications"]:
            try:
                conn.execute(f"DELETE FROM {tbl} WHERE telegram_id=?", (telegram_id,))
            except Exception:
                pass

        # ── UI-состояние ──────────────────────────────────────────────────────
        try:
            conn.execute("DELETE FROM player_ui WHERE telegram_id=?", (telegram_id,))
        except Exception:
            pass

        # ── Видимость локаций на карте ────────────────────────────────────────
        try:
            conn.execute("DELETE FROM player_location_visibility WHERE telegram_id=?", (telegram_id,))
        except Exception:
            pass

        conn.commit()
    return create_player(telegram_id, name)

def _update_player_field(telegram_id: int, **fields):
    if not fields:
        return
    try:
        sets = ", ".join(f"{k}=?" for k in fields)
        vals = list(fields.values()) + [telegram_id]
        with get_connection() as conn:
            conn.execute(f"UPDATE players SET {sets} WHERE telegram_id=?", vals)
            conn.commit()
        _log_repo_event("UPDATE_PLAYER_FIELD", telegram_id=telegram_id, fields=list(fields.keys()))
    except Exception:
        logger.exception(
            "UPDATE_PLAYER_FIELD_FAIL | telegram_id=%s | fields=%r",
            telegram_id,
            fields,
        )
        raise

def update_player_location(telegram_id: int, location_slug: str) -> Player | None:
    """Обновляет текущую локацию и выставляет корректный район по умолчанию.

    Для любой локации с районами выбирается валидный стартовый район.
    Это устраняет баг, когда после перехода в полевую локацию у игрока
    оставался пустой или район от предыдущей зоны, из-за чего неверно
    работали сбор, навигация и отображение карточки локации.
    """
    district = ""
    try:
        from game.district_service import get_default_district_slug
        district = get_default_district_slug(location_slug) or ""
    except Exception:
        defaults = {
            "dark_forest": "mushroom_path",
            "shadow_swamp": "black_water",
            "volcano_wrath": "ash_slope",
            "silver_city": "market_square",
        }
        district = defaults.get(location_slug, "")

    _update_player_field(
        telegram_id,
        location_slug=location_slug,
        current_district_slug=district,
    )
    return get_player(telegram_id)

def update_player_district(telegram_id: int, district_slug: str) -> Player | None:
    _update_player_field(telegram_id, current_district_slug=district_slug)
    return get_player(telegram_id)

def add_player_gold(telegram_id: int, amount: int) -> Player | None:
    with get_connection() as conn:
        conn.execute("UPDATE players SET gold=MAX(0,gold+?) WHERE telegram_id=?", (amount,telegram_id))
        conn.commit()
    return get_player(telegram_id)

def add_player_experience(telegram_id: int, amount: int) -> Player | None:
    p = get_player(telegram_id)
    if not p:
        return None
    exp = p.experience + amount
    level = p.level
    stat_pts = p.stat_points
    while exp >= level * 10:
        exp -= level * 10
        level += 1
        stat_pts += 2
    _update_player_field(telegram_id, experience=exp, level=level, stat_points=stat_pts)
    return get_player(telegram_id)

def restore_player_energy(telegram_id: int, amount: int, max_energy: int | None = None) -> Player | None:
    if max_energy is None:
        max_energy = get_max_energy(telegram_id)
    with get_connection() as conn:
        conn.execute("UPDATE players SET energy=MIN(?,energy+?) WHERE telegram_id=?", (max_energy, amount, telegram_id))
        conn.commit()
    return get_player(telegram_id)



def _ensure_energy_columns():
    """Lazy migration: adds energy-related columns if missing."""
    with get_connection() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()]
        if "max_energy" not in cols:
            conn.execute("ALTER TABLE players ADD COLUMN max_energy INTEGER NOT NULL DEFAULT 12")
        if "last_energy_time" not in cols:
            conn.execute("ALTER TABLE players ADD COLUMN last_energy_time INTEGER DEFAULT NULL")
        if "energy_notified" not in cols:
            conn.execute("ALTER TABLE players ADD COLUMN energy_notified INTEGER NOT NULL DEFAULT 0")
        if "bonus_energy" not in cols:
            # Бонусная энергия — сверх лимита, не восстанавливается автоматически
            conn.execute("ALTER TABLE players ADD COLUMN bonus_energy INTEGER NOT NULL DEFAULT 0")
        conn.commit()

_energy_cols_ok = False
def _lazy_energy():
    global _energy_cols_ok
    if not _energy_cols_ok:
        _ensure_energy_columns()
        _energy_cols_ok = True


def get_max_energy(telegram_id: int) -> int:
    """
    Максимальная энергия = 12 + ловкость // 3.
    С ловкостью 15 = 17 энергии.
    """
    _lazy_energy()
    p = get_player(telegram_id)
    if not p:
        return 12
    base = 12
    agility_bonus = getattr(p, "agility", 0) // 3
    return base + agility_bonus


def get_bonus_energy(telegram_id: int) -> int:
    """Бонусная энергия сверх лимита (от предметов/админа)."""
    _lazy_energy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT bonus_energy FROM players WHERE telegram_id=?", (telegram_id,)
        ).fetchone()
    return row["bonus_energy"] if row and row["bonus_energy"] else 0


def add_bonus_energy(telegram_id: int, amount: int):
    """Добавляет бонусную энергию сверх лимита."""
    _lazy_energy()
    with get_connection() as conn:
        conn.execute(
            "UPDATE players SET bonus_energy = bonus_energy + ? WHERE telegram_id=?",
            (amount, telegram_id)
        )
        conn.commit()


def get_total_energy_display(telegram_id: int) -> tuple[int, int, int]:
    """Возвращает (текущая, базовый_макс, бонус) для отображения."""
    _lazy_energy()
    tick_energy_regen(telegram_id)
    p = get_player(telegram_id)
    if not p:
        return 0, 12, 0
    max_e = get_max_energy(telegram_id)
    bonus = get_bonus_energy(telegram_id)
    return p.energy, max_e, bonus


def tick_energy_regen(telegram_id: int) -> tuple[int, bool]:
    """
    Восполняет энергию на основе прошедшего времени.
    1 энергия каждые 10 минут.
    Возвращает (текущая_энергия, стала_полной).
    """
    import time as _time
    _lazy_energy()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT energy, max_energy, last_energy_time, energy_notified FROM players WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()

    if not row:
        return 0, False

    max_e = get_max_energy(telegram_id)
    current = row["energy"]
    last_t  = row["last_energy_time"]
    notified = row["energy_notified"]
    now = int(_time.time())

    if current >= max_e:
        # Уже полная — обновим max_energy если изменилась
        with get_connection() as conn:
            conn.execute(
                "UPDATE players SET max_energy=?, energy=? WHERE telegram_id=?",
                (max_e, max_e, telegram_id)
            )
            conn.commit()
        return max_e, False

    if last_t is None:
        # Первый раз — фиксируем время
        with get_connection() as conn:
            conn.execute(
                "UPDATE players SET last_energy_time=?, max_energy=? WHERE telegram_id=?",
                (now, max_e, telegram_id)
            )
            conn.commit()
        return current, False

    # Считаем сколько энергии восстановилось
    elapsed = now - last_t
    # Бонус от комбеза ускоряет регенерацию
    try:
        from game.equipment_service import get_equipment_bonuses
        _eq = get_equipment_bonuses(telegram_id)
        _suit_bonus = _eq.get("energy_regen", 0.0)
        _regen_interval = max(60, int(600 / (1 + _suit_bonus)))  # мин. 60 сек
    except Exception:
        _regen_interval = 600

    regen_ticks = elapsed // _regen_interval

    if regen_ticks <= 0:
        return current, False

    new_energy = min(max_e, current + regen_ticks)
    new_last_t = last_t + regen_ticks * 600
    was_full = new_energy >= max_e

    with get_connection() as conn:
        conn.execute(
            "UPDATE players SET energy=?, last_energy_time=?, max_energy=?, energy_notified=? WHERE telegram_id=?",
            (new_energy, new_last_t, max_e,
             0 if not was_full else notified,  # сбрасываем notified если заполнилась
             telegram_id)
        )
        conn.commit()

    return new_energy, was_full


def mark_energy_notification_sent(telegram_id: int):
    _lazy_energy()
    with get_connection() as conn:
        conn.execute(
            "UPDATE players SET energy_notified=1 WHERE telegram_id=?",
            (telegram_id,)
        )
        conn.commit()

def spend_player_energy(telegram_id: int, amount: int) -> bool:
    """
    Тратит энергию. Сначала расходует бонусную (сверх лимита),
    затем обычную. Обычная восстанавливается, бонусная — нет.
    """
    tick_energy_regen(telegram_id)
    import time as _t
    p = get_player(telegram_id)
    if not p:
        return False

    bonus = get_bonus_energy(telegram_id)
    total_available = p.energy + bonus

    if total_available < amount:
        return False

    with get_connection() as conn:
        if bonus >= amount:
            # Тратим только бонусную
            conn.execute(
                "UPDATE players SET bonus_energy=bonus_energy-? WHERE telegram_id=?",
                (amount, telegram_id)
            )
        else:
            # Сначала тратим всю бонусную, потом обычную
            regular_spend = amount - bonus
            conn.execute(
                "UPDATE players SET bonus_energy=0, energy=energy-?,"
                " last_energy_time=COALESCE(last_energy_time,?), energy_notified=0"
                " WHERE telegram_id=?",
                (regular_spend, int(_t.time()), telegram_id)
            )
        conn.commit()
    return True

def spend_stat_point(telegram_id: int, stat_name: str) -> bool:
    if stat_name not in {"strength","agility","intellect"}:
        return False
    p = get_player(telegram_id)
    if not p or p.stat_points <= 0:
        return False
    _update_player_field(telegram_id, stat_points=p.stat_points-1,
        **{stat_name: getattr(p, stat_name)+1})
    return True

def damage_player_hp(telegram_id: int, amount: int) -> Player | None:
    p = get_player(telegram_id)
    if not p or amount <= 0:
        return p
    new_hp = max(0, p.hp - amount)
    defeated = 1 if new_hp <= 0 else 0
    _update_player_field(telegram_id, hp=new_hp, is_defeated=defeated)
    return get_player(telegram_id)

def heal_player_hp(telegram_id: int, amount: int) -> Player | None:
    p = get_player(telegram_id)
    if not p or amount <= 0:
        return p
    new_hp = min(p.max_hp, p.hp + amount)
    # Сбрасываем is_defeated как только HP > 0
    defeated = 0 if new_hp > 0 else p.is_defeated
    _update_player_field(telegram_id, hp=new_hp, is_defeated=int(defeated))
    return get_player(telegram_id)

def defeat_player_state(telegram_id: int, gold_loss: int = 0) -> Player | None:
    p = get_player(telegram_id)
    if not p:
        return None
    new_gold = max(0, p.gold - gold_loss) if gold_loss > 0 else p.gold
    _update_player_field(telegram_id, is_defeated=1, hp=1,
        injury_turns=max(p.injury_turns, 5), gold=new_gold,
        location_slug="silver_city", current_district_slug="market_square")
    return get_player(telegram_id)

def tick_player_injuries(telegram_id: int, amount: int = 1) -> Player | None:
    p = get_player(telegram_id)
    if not p:
        return None
    if p.injury_turns > 0:
        _update_player_field(telegram_id, injury_turns=max(0, p.injury_turns - amount))
    return get_player(telegram_id)

def clear_player_injuries(telegram_id: int) -> Player | None:
    p = get_player(telegram_id)
    if not p:
        return None
    _update_player_field(telegram_id, injury_turns=0, is_defeated=0, hp=p.max_hp)
    return get_player(telegram_id)

def start_birth_cooldown(telegram_id: int, actions: int = 3) -> int:
    _update_player_field(telegram_id, birth_cooldown_actions=actions)
    return actions

def tick_birth_cooldown(telegram_id: int) -> int:
    p = get_player(telegram_id)
    if not p:
        return 0
    new_val = max(0, p.birth_cooldown_actions - 1)
    _update_player_field(telegram_id, birth_cooldown_actions=new_val)
    return new_val

# ─── Профессии ────────────────────────────────────────────────────────────────

PROFESSION_LEVEL_CAP = 10
PROFESSION_FIELD_MAP = {
    "gatherer":  ("gatherer_level",  "gatherer_exp"),
    "hunter":    ("hunter_level",    "hunter_exp"),
    "geologist": ("geologist_level", "geologist_exp"),
    "alchemist": ("alchemist_level", "alchemist_exp"),
    "merchant":  ("merchant_level",  "merchant_exp"),
}

def get_profession_exp_required(level: int) -> int:
    return 6 + level * 4

def get_profession_state(player: Player, kind: str) -> dict | None:
    fields = PROFESSION_FIELD_MAP.get(kind)
    if not fields:
        return None
    lf, ef = fields
    level = getattr(player, lf, 1)
    exp   = getattr(player, ef, 0)
    return {"kind":kind,"level":level,"exp":exp,
            "exp_to_next": 0 if level>=PROFESSION_LEVEL_CAP else get_profession_exp_required(level)}

def improve_profession_from_action(telegram_id: int, kind: str, amount: int = 1) -> dict | None:
    p = get_player(telegram_id)
    if not p:
        return None
    fields = PROFESSION_FIELD_MAP.get(kind)
    if not fields:
        return None
    lf, ef = fields
    old_level = getattr(p, lf, 1)
    old_exp   = getattr(p, ef, 0)
    if old_level >= PROFESSION_LEVEL_CAP:
        return {"kind":kind,"leveled_up":False,"level_before":old_level,"level_after":old_level,
                "exp_before":old_exp,"exp_after":old_exp,"exp_to_next":0,"is_max_level":True,"gained_exp":0}
    new_exp   = old_exp + max(0, amount)
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
        new_exp   = 0
    _update_player_field(telegram_id, **{lf: new_level, ef: new_exp})
    return {"kind":kind,"leveled_up":leveled_up,"level_before":old_level,"level_after":new_level,
            "exp_before":old_exp,"exp_after":new_exp,
            "exp_to_next":0 if new_level>=PROFESSION_LEVEL_CAP else get_profession_exp_required(new_level),
            "is_max_level":new_level>=PROFESSION_LEVEL_CAP,"gained_exp":max(0,amount)}

# ─── Монстры ──────────────────────────────────────────────────────────────────

def add_captured_monster(telegram_id: int, name: str, rarity: str, mood: str,
                          hp: int, attack: int, source_type: str = "wild") -> dict:
    from game.monster_abilities import MONSTER_ABILITIES
    mtype = _guess_monster_type(name, mood)
    abilities = json_set(MONSTER_ABILITIES.get(name, []))
    is_first = len(get_player_monsters(telegram_id)) == 0
    with get_connection() as conn:
        cur = conn.execute("""INSERT INTO player_monsters
            (telegram_id,name,rarity,mood,monster_type,hp,max_hp,current_hp,attack,
             level,experience,is_active,source_type,abilities)
            VALUES (?,?,?,?,?,?,?,?,?,1,0,?,?,?)""",
            (telegram_id,name,rarity,mood,mtype,hp,hp,hp,attack,
             1 if is_first else 0, source_type, abilities))
        mid = cur.lastrowid
        conn.commit()
    return get_monster_by_id(telegram_id, mid)

def get_player_monsters(telegram_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM player_monsters WHERE telegram_id=? ORDER BY id", (telegram_id,)).fetchall()
    return [_monster_row_to_dict(r) for r in rows]

def get_active_monster(telegram_id: int) -> dict | None:
    """Возвращает активного живого монстра (current_hp>0, is_dead=0).
    Используем lazy migration для is_dead чтобы не ломать старые БД.
    """
    _lazy_monster_dead()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_monsters WHERE telegram_id=? AND is_active=1 AND is_dead=0 AND current_hp>0 LIMIT 1",
            (telegram_id,)
        ).fetchone()
    return _monster_row_to_dict(row) if row else None


def _ensure_monster_dead_column():
    """Lazy migration: adds is_dead column if missing."""
    with get_connection() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(player_monsters)").fetchall()]
        if "is_dead" not in cols:
            conn.execute("ALTER TABLE player_monsters ADD COLUMN is_dead INTEGER NOT NULL DEFAULT 0")
            conn.commit()

_monster_dead_col_ok = False
def _lazy_monster_dead():
    global _monster_dead_col_ok
    if not _monster_dead_col_ok:
        _ensure_monster_dead_column()
        _monster_dead_col_ok = True


def kill_active_monster(telegram_id: int) -> dict | None:
    """Marks active monster as dead. Monster stays in roster but cannot fight."""
    _lazy_monster_dead()
    m = get_active_monster(telegram_id)
    if not m:
        return None
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_monsters SET is_dead=1, current_hp=0 WHERE id=?",
            (m["id"],)
        )
        conn.commit()
    return m


def get_living_active_monster(telegram_id: int) -> dict | None:
    """Returns active monster only if alive (current_hp > 0 and is_dead = 0)."""
    _lazy_monster_dead()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_monsters WHERE telegram_id=? AND is_active=1 AND is_dead=0 AND current_hp>0 LIMIT 1",
            (telegram_id,)
        ).fetchone()
    if not row:
        return None
    from database.db import json_get
    return {**dict(row), "abilities": json_get(row["abilities"])}


def has_living_monster(telegram_id: int) -> bool:
    """Checks if player has any living active monster."""
    try:
        return get_living_active_monster(telegram_id) is not None
    except Exception:
        # Fallback: just check active monster exists with hp > 0
        m = get_active_monster(telegram_id)
        return m is not None and m.get("current_hp", 1) > 0


def revive_monster(telegram_id: int, monster_id: int, hp: int) -> bool:
    """Revives a dead monster with given HP (used in city healing)."""
    _lazy_monster_dead()
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_monsters SET is_dead=0, current_hp=? WHERE id=? AND telegram_id=?",
            (hp, monster_id, telegram_id)
        )
        conn.commit()
    return True


def get_monster_by_id(telegram_id: int, monster_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM player_monsters WHERE telegram_id=? AND id=?", (telegram_id,monster_id)).fetchone()
    return _monster_row_to_dict(row) if row else None

def set_active_monster(telegram_id: int, monster_id: int) -> dict | None:
    with get_connection() as conn:
        conn.execute("UPDATE player_monsters SET is_active=0 WHERE telegram_id=?", (telegram_id,))
        conn.execute("UPDATE player_monsters SET is_active=1 WHERE telegram_id=? AND id=?", (telegram_id,monster_id))
        conn.commit()
    return get_monster_by_id(telegram_id, monster_id)

def save_monster(monster: dict):
    """Сохраняет изменённый словарь монстра обратно в БД."""
    with get_connection() as conn:
        conn.execute("""UPDATE player_monsters SET
            name=?,rarity=?,mood=?,monster_type=?,hp=?,max_hp=?,current_hp=?,attack=?,
            level=?,experience=?,is_active=?,infection_type=?,infection_stage=?,
            distortion=?,source_type=?,evolution_stage=?,evolution_from=?,
            abilities=?,combo_mutation=?,is_listed=?,list_price=?
            WHERE id=?""",
            (monster["name"],monster["rarity"],monster["mood"],monster.get("monster_type","void"),
             monster["hp"],monster["max_hp"],monster["current_hp"],monster["attack"],
             monster.get("level",1),monster.get("experience",0),
             1 if monster.get("is_active") else 0,
             monster.get("infection_type"),monster.get("infection_stage",0),
             monster.get("distortion",0),monster.get("source_type","wild"),
             monster.get("evolution_stage",0),monster.get("evolution_from"),
             json_set(monster.get("abilities",[])),
             monster.get("combo_mutation"),
             1 if monster.get("is_listed") else 0,
             monster.get("list_price",0),
             monster["id"]))
        conn.commit()

def damage_active_monster(telegram_id: int, amount: int) -> dict | None:
    m = get_active_monster(telegram_id)
    if m:
        m["current_hp"] = max(0, m["current_hp"] - amount)
        save_monster(m)
    return m

def heal_active_monster(telegram_id: int, amount: int = 999) -> dict | None:
    m = get_active_monster(telegram_id)
    if m:
        m["current_hp"] = min(m["max_hp"], m["current_hp"] + amount)
        save_monster(m)
    return m

def heal_all_monsters(telegram_id: int) -> list[dict]:
    monsters = get_player_monsters(telegram_id)
    for m in monsters:
        m["current_hp"] = m.get("max_hp", m.get("hp",1))
        save_monster(m)
    return monsters

# ── v3: роль-зависимый рост статов ──────────────────────────────────────────

_ROLE_FROM_TYPE = {
    "flame": "assault", "storm": "hunter",  "void": "hybrid",
    "nature": "hybrid", "shadow": "controller", "echo": "controller",
    "bone": "tank",     "spirit": "support",
}

_LEVELUP_GAINS = {
    # (hp_gain, atk_gain)
    "assault":    (3,  2),   # больше атаки
    "tank":       (8,  1),   # много HP
    "hunter":     (4,  2),   # скорость → атака
    "controller": (4,  1),   # сбалансированный
    "support":    (6,  1),   # много HP
    "hybrid":     (4,  1),   # стандарт
}


def _infer_role_from_type(monster_type: str) -> str:
    return _ROLE_FROM_TYPE.get(monster_type, "hybrid")


def _get_levelup_gains(role: str) -> tuple[int, int]:
    return _LEVELUP_GAINS.get(role, (4, 1))


def add_active_monster_experience(telegram_id: int, amount: int) -> tuple[dict | None, list]:
    m = get_active_monster(telegram_id)
    if not m:
        return None, []
    m["experience"] = m.get("experience",0) + amount
    level_ups = []
    while m["experience"] >= m.get("level",1) * 5:
        m["experience"] -= m.get("level",1) * 5
        m["level"] = m.get("level",1) + 1
        # v3: Рост статов по роли монстра
        _role = m.get("role") or _infer_role_from_type(m.get("monster_type", "void"))
        _hp_gain, _atk_gain = _get_levelup_gains(_role)
        m["max_hp"] += _hp_gain
        m["attack"] += _atk_gain
        m["current_hp"] = m["max_hp"]
        level_ups.append({"level":m["level"],"max_hp":m["max_hp"],"attack":m["attack"],
                          "hp_gain":_hp_gain,"atk_gain":_atk_gain,"role":_role})
    save_monster(m)
    return m, level_ups

def get_resources_count_total(telegram_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COALESCE(SUM(amount),0) as total FROM player_resources WHERE telegram_id=?", (telegram_id,)).fetchone()
    return int(row["total"]) if row else 0


def remove_player_monster(telegram_id: int, monster_id: int) -> bool:
    """Удалить монстра из команды игрока (продажа, освобождение)."""
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM player_monsters WHERE telegram_id=? AND id=? AND is_active=0",
            (telegram_id, monster_id)
        )
        conn.commit()
    return cur.rowcount > 0

# ─── Эмоции ───────────────────────────────────────────────────────────────────

def _ensure_emotions(telegram_id: int):
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO player_emotions (telegram_id) VALUES (?)", (telegram_id,))
        conn.commit()

def get_player_emotions(telegram_id: int) -> dict:
    _ensure_emotions(telegram_id)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM player_emotions WHERE telegram_id=?", (telegram_id,)).fetchone()
    if not row:
        return {"rage":0,"fear":0,"instinct":0,"inspiration":0,"sadness":0,"joy":0,"disgust":0,"surprise":0}
    d = dict(row)
    d.pop("telegram_id", None)
    return d

def add_emotions(telegram_id: int, changes: dict) -> dict:
    _ensure_emotions(telegram_id)
    current = get_player_emotions(telegram_id)
    for k, v in changes.items():
        if k in current:
            current[k] = max(0, current[k] + v)
    sets = ", ".join(f"{k}=?" for k in current)
    vals = list(current.values()) + [telegram_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE player_emotions SET {sets} WHERE telegram_id=?", vals)
        conn.commit()
    return current

def spend_emotions(telegram_id: int, changes: dict) -> dict:
    return add_emotions(telegram_id, {k: -v for k, v in changes.items()})

# ─── Инвентарь ────────────────────────────────────────────────────────────────

def get_inventory(telegram_id: int) -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT item_slug, amount FROM player_items WHERE telegram_id=?", (telegram_id,)).fetchall()
    return {r["item_slug"]: r["amount"] for r in rows}

def get_item_count(telegram_id: int, item_slug: str) -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT amount FROM player_items WHERE telegram_id=? AND item_slug=?", (telegram_id,item_slug)).fetchone()
    return row["amount"] if row else 0

def add_item(telegram_id: int, item_slug: str, amount: int = 1) -> int:
    try:
        with get_connection() as conn:
            conn.execute("""INSERT INTO player_items (telegram_id,item_slug,amount)
                VALUES (?,?,?) ON CONFLICT(telegram_id,item_slug) DO UPDATE SET amount=amount+?""",
                (telegram_id,item_slug,amount,amount))
            conn.commit()
        total = get_item_count(telegram_id, item_slug)
        _log_repo_event("ADD_ITEM", telegram_id=telegram_id, item_slug=item_slug, amount=amount, total=total)
        return total
    except Exception:
        logger.exception(
            "ADD_ITEM_FAIL | telegram_id=%s | item_slug=%r | amount=%s",
            telegram_id,
            item_slug,
            amount,
        )
        raise

def spend_item(telegram_id: int, item_slug: str, amount: int = 1) -> bool:
    try:
        current = get_item_count(telegram_id, item_slug)
        if current < amount:
            _log_repo_event("SPEND_ITEM_DENIED", telegram_id=telegram_id, item_slug=item_slug, amount=amount, current=current)
            return False
        with get_connection() as conn:
            conn.execute("UPDATE player_items SET amount=amount-? WHERE telegram_id=? AND item_slug=?",
                (amount,telegram_id,item_slug))
            conn.commit()
        _log_repo_event("SPEND_ITEM", telegram_id=telegram_id, item_slug=item_slug, amount=amount, remaining=current - amount)
        return True
    except Exception:
        logger.exception(
            "SPEND_ITEM_FAIL | telegram_id=%s | item_slug=%r | amount=%s",
            telegram_id,
            item_slug,
            amount,
        )
        raise

# ─── Ресурсы ──────────────────────────────────────────────────────────────────

def get_resources(telegram_id: int) -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT slug, amount FROM player_resources WHERE telegram_id=?", (telegram_id,)).fetchall()
    return {r["slug"]: r["amount"] for r in rows}

def add_resource(telegram_id: int, slug: str, count: int) -> int:
    try:
        with get_connection() as conn:
            conn.execute("""INSERT INTO player_resources (telegram_id,slug,amount)
                VALUES (?,?,?) ON CONFLICT(telegram_id,slug) DO UPDATE SET amount=amount+?""",
                (telegram_id,slug,count,count))
            conn.commit()
        with get_connection() as conn:
            row = conn.execute("SELECT amount FROM player_resources WHERE telegram_id=? AND slug=?", (telegram_id,slug)).fetchone()
        total = row["amount"] if row else 0
        _log_repo_event("ADD_RESOURCE", telegram_id=telegram_id, slug=slug, count=count, total=total)
        return total
    except Exception:
        logger.exception(
            "ADD_RESOURCE_FAIL | telegram_id=%s | slug=%r | count=%s",
            telegram_id,
            slug,
            count,
        )
        raise

def spend_resource(telegram_id: int, slug: str, count: int) -> bool:
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT amount FROM player_resources WHERE telegram_id=? AND slug=?", (telegram_id,slug)).fetchone()
        if not row or row["amount"] < count:
            _log_repo_event(
                "SPEND_RESOURCE_DENIED",
                telegram_id=telegram_id,
                slug=slug,
                count=count,
                current=(row["amount"] if row else 0),
            )
            return False
        with get_connection() as conn:
            conn.execute("UPDATE player_resources SET amount=amount-? WHERE telegram_id=? AND slug=?",
                (count,telegram_id,slug))
            conn.commit()
        _log_repo_event("SPEND_RESOURCE", telegram_id=telegram_id, slug=slug, count=count, remaining=row["amount"] - count)
        return True
    except Exception:
        logger.exception(
            "SPEND_RESOURCE_FAIL | telegram_id=%s | slug=%r | count=%s",
            telegram_id,
            slug,
            count,
        )
        raise

# ─── Квесты ───────────────────────────────────────────────────────────────────

def get_player_quests(telegram_id: int) -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM player_quests WHERE telegram_id=?", (telegram_id,)).fetchall()
    result = {}
    existing = {r["quest_id"]: dict(r) for r in rows}
    for i, qid in enumerate(STARTER_QUEST_CHAIN):
        base = STARTER_QUESTS[qid]
        q = existing.get(qid, {"progress":0,"completed":0,"active":1 if i==0 else 0,"source":"starter"})
        result[qid] = {"progress":q["progress"],"completed":bool(q["completed"]),
                       "active":bool(q["active"]),"source":q.get("source","starter"),**base}
    # recompute active chain
    active_found = False
    for qid in STARTER_QUEST_CHAIN:
        q = result[qid]
        if q["completed"]:
            q["active"] = False
            continue
        if not active_found:
            q["active"] = True
            active_found = True
        else:
            q["active"] = False
    return result

def get_active_player_quests(telegram_id: int) -> dict:
    quests = get_player_quests(telegram_id)
    return {qid: q for qid, q in quests.items() if q.get("active") and not q.get("completed")}

def progress_quests(telegram_id: int, action_type: str) -> list:
    quests = get_player_quests(telegram_id)
    completed_now = []
    for qid in STARTER_QUEST_CHAIN:
        q = quests[qid]
        if q["completed"] or not q["active"] or q["target_type"] != action_type:
            continue
        new_progress = q["progress"] + 1
        completed = new_progress >= q["target_value"]
        with get_connection() as conn:
            conn.execute("""INSERT INTO player_quests (telegram_id,quest_id,progress,completed,active,source)
                VALUES (?,?,?,?,?,?)
                ON CONFLICT(telegram_id,quest_id) DO UPDATE SET progress=?,completed=?,active=?""",
                (telegram_id,qid,new_progress,int(completed),int(not completed),"starter",
                 new_progress,int(completed),int(not completed)))
            if completed:
                idx = STARTER_QUEST_CHAIN.index(qid)
                if idx+1 < len(STARTER_QUEST_CHAIN):
                    nqid = STARTER_QUEST_CHAIN[idx+1]
                    conn.execute("""INSERT INTO player_quests (telegram_id,quest_id,progress,completed,active,source)
                        VALUES (?,?,0,0,1,'starter')
                        ON CONFLICT(telegram_id,quest_id) DO UPDATE SET active=1""",
                        (telegram_id,nqid))
            conn.commit()
        if completed:
            completed_now.append((qid, q))
        break
    return completed_now

# ─── Сюжетные квесты ──────────────────────────────────────────────────────────

def get_player_story(telegram_id: int) -> dict:
    with get_connection() as conn:
        idx_row = conn.execute("SELECT current_index FROM player_story_index WHERE telegram_id=?", (telegram_id,)).fetchone()
        rows    = conn.execute("SELECT * FROM player_story WHERE telegram_id=?", (telegram_id,)).fetchall()
    current_index = idx_row["current_index"] if idx_row else 0
    story_data = {r["story_id"]: dict(r) for r in rows}
    result = {"current_index": current_index, "completed_ids": []}
    for sq in STORY_QUESTS:
        sid = sq["id"]
        if sid not in story_data:
            result[sid] = {"explore_count":0,"win_count":0,"visited":False}
        else:
            d = story_data[sid]
            result[sid] = {"explore_count":d["explore_count"],"win_count":d["win_count"],"visited":bool(d["visited"])}
            if d["completed"]:
                result["completed_ids"].append(sid)
    return result

def get_current_story_quest(telegram_id: int) -> dict | None:
    story = get_player_story(telegram_id)
    idx = story["current_index"]
    if idx >= len(STORY_QUESTS):
        return None
    return STORY_QUESTS[idx]

def update_story_progress(telegram_id: int, action_type: str, current_location_slug: str) -> dict | None:
    quest = get_current_story_quest(telegram_id)
    if not quest:
        return None
    sid = quest["id"]
    story = get_player_story(telegram_id)
    state = story[sid]
    visited = state["visited"] or current_location_slug == quest["requirements"]["location_slug"]
    ec = state["explore_count"] + (1 if current_location_slug == quest["requirements"]["location_slug"] and action_type == "explore" else 0)
    wc = state["win_count"]    + (1 if current_location_slug == quest["requirements"]["location_slug"] and action_type == "win"     else 0)
    req = quest["requirements"]
    completed = visited and ec >= req.get("explore_count",0) and wc >= req.get("win_count",0)
    with get_connection() as conn:
        conn.execute("""INSERT INTO player_story (telegram_id,story_id,explore_count,win_count,visited,completed)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(telegram_id,story_id) DO UPDATE SET
            explore_count=?,win_count=?,visited=?,completed=?""",
            (telegram_id,sid,ec,wc,int(visited),int(completed),ec,wc,int(visited),int(completed)))
        if completed:
            new_idx = story["current_index"] + 1
            conn.execute("INSERT INTO player_story_index (telegram_id,current_index) VALUES (?,?) ON CONFLICT(telegram_id) DO UPDATE SET current_index=?",
                (telegram_id,new_idx,new_idx))
        conn.commit()
    return quest if completed else None

# ─── Encounters ───────────────────────────────────────────────────────────────

def save_pending_encounter(telegram_id: int, encounter: dict) -> dict:
    with get_connection() as conn:
        conn.execute("""INSERT INTO pending_encounters (telegram_id,data) VALUES (?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET data=?""",
            (telegram_id, json_set(encounter), json_set(encounter)))
        conn.commit()
    return encounter

def get_pending_encounter(telegram_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT data FROM pending_encounters WHERE telegram_id=?", (telegram_id,)).fetchone()
    return json_get(row["data"]) if row else None

def clear_pending_encounter(telegram_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM pending_encounters WHERE telegram_id=?", (telegram_id,))
        conn.commit()

# ─── Action flags ─────────────────────────────────────────────────────────────

def _get_flags(telegram_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT data FROM player_action_flags WHERE telegram_id=?", (telegram_id,)).fetchone()
    return json_get(row["data"]) if row else {}

def _save_flags(telegram_id: int, flags: dict):
    with get_connection() as conn:
        conn.execute("""INSERT INTO player_action_flags (telegram_id,data) VALUES (?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET data=?""",
            (telegram_id, json_set(flags), json_set(flags)))
        conn.commit()

def begin_action_scope(telegram_id: int, action_key: str) -> dict:
    flags = _get_flags(telegram_id)
    flags["current_action"] = action_key
    flags["birth_done"] = False
    _save_flags(telegram_id, flags)
    return flags

def get_action_flags(telegram_id: int) -> dict:
    return _get_flags(telegram_id)

def get_temp_effects(telegram_id: int) -> dict:
    return _get_flags(telegram_id).get("effects", {})

def set_temp_effect(telegram_id: int, effect_name: str, duration: int) -> dict:
    flags = _get_flags(telegram_id)
    effects = flags.setdefault("effects", {})
    effects[effect_name] = max(duration, effects.get(effect_name, 0))
    _save_flags(telegram_id, flags)
    return effects

def has_temp_effect(telegram_id: int, effect_name: str) -> bool:
    return get_temp_effects(telegram_id).get(effect_name, 0) > 0

def tick_temp_effects(telegram_id: int) -> list:
    flags = _get_flags(telegram_id)
    effects = flags.setdefault("effects", {})
    expired = []
    for k in list(effects.keys()):
        effects[k] -= 1
        if effects[k] <= 0:
            expired.append(k)
            del effects[k]
    _save_flags(telegram_id, flags)
    return expired

def clear_temp_effect(telegram_id: int, effect_name: str):
    flags = _get_flags(telegram_id)
    flags.get("effects", {}).pop(effect_name, None)
    _save_flags(telegram_id, flags)

def mark_birth_done(telegram_id: int):
    flags = _get_flags(telegram_id)
    flags["birth_done"] = True
    _save_flags(telegram_id, flags)

def is_birth_done(telegram_id: int) -> bool:
    return _get_flags(telegram_id).get("birth_done", False)

# ─── UI ───────────────────────────────────────────────────────────────────────

def get_ui_state(telegram_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT screen, context_data FROM player_ui WHERE telegram_id=?", (telegram_id,)).fetchone()
    if not row:
        with get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO player_ui (telegram_id) VALUES (?)", (telegram_id,))
            conn.commit()
        return {"screen":"main","context":{}}
    return {"screen": row["screen"], "context": json_get(row["context_data"])}

def set_ui_screen(telegram_id: int, screen: str, **context) -> dict:
    with get_connection() as conn:
        conn.execute("""INSERT INTO player_ui (telegram_id,screen,context_data) VALUES (?,?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET screen=?,context_data=?""",
            (telegram_id,screen,json_set(context),screen,json_set(context)))
        conn.commit()
    return {"screen":screen,"context":context}

def get_ui_screen(telegram_id: int) -> str:
    return get_ui_state(telegram_id).get("screen","main")

# ─── Кодекс и реликвии ────────────────────────────────────────────────────────

def get_player_codex(telegram_id: int) -> set:
    with get_connection() as conn:
        rows = conn.execute("SELECT monster_name FROM player_codex WHERE telegram_id=?", (telegram_id,)).fetchall()
    return {r["monster_name"] for r in rows}

def register_monster_seen(telegram_id: int, monster_name: str) -> set:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO player_codex (telegram_id,monster_name) VALUES (?,?)", (telegram_id,monster_name))
        conn.commit()
    return get_player_codex(telegram_id)

def get_player_relics(telegram_id: int) -> list:
    with get_connection() as conn:
        rows = conn.execute("SELECT relic_slug FROM player_relics WHERE telegram_id=?", (telegram_id,)).fetchall()
    return [r["relic_slug"] for r in rows]

def add_relic(telegram_id: int, relic_slug: str) -> list:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO player_relics (telegram_id,relic_slug) VALUES (?,?)", (telegram_id,relic_slug))
        conn.commit()
    return get_player_relics(telegram_id)

def has_relic(telegram_id: int, relic_slug: str) -> bool:
    return relic_slug in get_player_relics(telegram_id)

# ─── Craft/Extra/Board/Guild квесты ───────────────────────────────────────────

def progress_crafting_quests(telegram_id: int, craft_key: str) -> list:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM player_craft_quests WHERE telegram_id=? AND completed=0 AND craft_key=?", (telegram_id,craft_key)).fetchall()
    completed_now = []
    for row in rows:
        new_prog = row["progress"] + 1
        done = new_prog >= row["count"]
        with get_connection() as conn:
            conn.execute("UPDATE player_craft_quests SET progress=?,completed=? WHERE telegram_id=? AND quest_id=?",
                (new_prog,int(done),telegram_id,row["quest_id"]))
            conn.commit()
        if done:
            completed_now.append(dict(row))
    return completed_now

def _progress_generic_quests(table: str, telegram_id: int, action_type: str, amount: int = 1) -> list:
    with get_connection() as conn:
        rows = conn.execute(f"SELECT * FROM {table} WHERE telegram_id=? AND completed=0 AND action_type=?", (telegram_id,action_type)).fetchall()
    completed_now = []
    for row in rows:
        new_prog = row["progress"] + amount
        done = new_prog >= row["count"]
        with get_connection() as conn:
            conn.execute(f"UPDATE {table} SET progress=?,completed=? WHERE telegram_id=? AND quest_id=?",
                (new_prog,int(done),telegram_id,row["quest_id"]))
            conn.commit()
        if done:
            completed_now.append((row["quest_id"], dict(row)))
    return completed_now

def progress_extra_quests(telegram_id: int, action_type: str, amount: int = 1) -> list:
    return _progress_generic_quests("player_extra_quests", telegram_id, action_type, amount)

def progress_board_quests(telegram_id: int, action_type: str, amount: int = 1) -> list:
    return _progress_generic_quests("player_board_quests", telegram_id, action_type, amount)

def get_player_guild_quests(telegram_id: int) -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM player_guild_quests WHERE telegram_id=?", (telegram_id,)).fetchall()
    return {r["quest_id"]: dict(r) for r in rows}

def progress_guild_quests(telegram_id: int, action_type: str, guild_key: str | None = None, amount: int = 1) -> list:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM player_guild_quests WHERE telegram_id=? AND completed=0", (telegram_id,)).fetchall()
    completed_now = []
    for row in rows:
        if row["action_type"] != action_type:
            continue
        if guild_key and row["guild_key"] and row["guild_key"] != guild_key:
            continue
        new_prog = row["progress"] + amount
        done = new_prog >= row["count"]
        with get_connection() as conn:
            conn.execute("UPDATE player_guild_quests SET progress=?,completed=? WHERE telegram_id=? AND quest_id=?",
                (new_prog,int(done),telegram_id,row["quest_id"]))
            conn.commit()
        if done:
            completed_now.append((row["quest_id"], dict(row)))
    return completed_now

# ─── Городские заказы ─────────────────────────────────────────────────────────

def get_active_city_orders(telegram_id: int) -> list:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM player_city_orders WHERE telegram_id=? AND status='active' ORDER BY created_at", (telegram_id,)).fetchall()
    return [dict(r) for r in rows]

def count_active_city_orders(telegram_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM player_city_orders WHERE telegram_id=? AND status='active'", (telegram_id,)).fetchone()
    return int(row["cnt"]) if row else 0

def has_active_city_order(telegram_id: int, order_slug: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM player_city_orders WHERE telegram_id=? AND order_slug=? AND status='active' LIMIT 1", (telegram_id,order_slug)).fetchone()
    return row is not None

def add_city_order(telegram_id: int, order_slug: str, title: str, goal_text: str, reward_gold: int, reward_exp: int):
    with get_connection() as conn:
        conn.execute("INSERT INTO player_city_orders (telegram_id,order_slug,title,goal_text,reward_gold,reward_exp) VALUES (?,?,?,?,?,?)",
            (telegram_id,order_slug,title,goal_text,reward_gold,reward_exp))
        conn.commit()

def complete_city_order(order_id: int):
    import time
    with get_connection() as conn:
        conn.execute("UPDATE player_city_orders SET status='completed', completed_at=? WHERE id=?", (int(time.time()), order_id))
        conn.commit()

def clear_active_city_orders(telegram_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM player_city_orders WHERE telegram_id=? AND status='active'", (telegram_id,))
        conn.commit()

# ─── Рынок (NPC) ──────────────────────────────────────────────────────────────

def _ensure_market_defaults():
    with get_connection() as conn:
        for slug, d in DEFAULT_MARKET_ITEMS.items():
            conn.execute("INSERT OR IGNORE INTO market_items (item_slug,base_price) VALUES (?,?)", (slug,d["base_price"]))
        for slug, d in DEFAULT_MARKET_MONSTERS.items():
            conn.execute("INSERT OR IGNORE INTO market_monsters_npc (monster_slug,base_price) VALUES (?,?)", (slug,d["base_price"]))
        conn.commit()

def _decay(entry: dict, decay_per_hour: float = 0.35) -> dict:
    now = time.time()
    updated_at = entry.get("updated_at", 0.0)
    if updated_at:
        hours = max(0.0, (now - updated_at) / 3600.0)
        entry["demand"] = max(0.0, entry.get("demand",0.0) - hours * decay_per_hour)
    entry["updated_at"] = now
    return entry

def get_market_item_entry(item_slug: str) -> dict:
    _ensure_market_defaults()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM market_items WHERE item_slug=?", (item_slug,)).fetchone()
    return _decay(dict(row)) if row else {"base_price":10,"demand":0.0,"updated_at":time.time()}

def get_market_monster_entry(monster_slug: str) -> dict:
    _ensure_market_defaults()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM market_monsters_npc WHERE monster_slug=?", (monster_slug,)).fetchone()
    return _decay(dict(row)) if row else {"base_price":90,"demand":0.0,"updated_at":time.time()}

def get_market_item_price(item_slug: str) -> int:
    e = get_market_item_entry(item_slug)
    return max(1, int(round(e["base_price"] * (1 + 0.12 * e.get("demand",0.0)))))

def get_market_monster_price(monster_slug: str) -> int:
    e = get_market_monster_entry(monster_slug)
    return max(1, int(round(e["base_price"] * (1 + 0.10 * e.get("demand",0.0)))))

def purchase_market_item(telegram_id: int, item_slug: str) -> int | None:
    try:
        p = get_player(telegram_id)
        if not p:
            _log_repo_event("PURCHASE_MARKET_ITEM_NO_PLAYER", telegram_id=telegram_id, item_slug=item_slug)
            return None
        price = get_market_item_price(item_slug)
        if p.gold < price:
            _log_repo_event("PURCHASE_MARKET_ITEM_NO_GOLD", telegram_id=telegram_id, item_slug=item_slug, price=price, gold=p.gold)
            return None
        _update_player_field(telegram_id, gold=p.gold - price)
        e = get_market_item_entry(item_slug)
        new_demand = min(10.0, e.get("demand",0.0) + 1.0)
        with get_connection() as conn:
            conn.execute("UPDATE market_items SET demand=?,updated_at=? WHERE item_slug=?", (new_demand,time.time(),item_slug))
            conn.commit()
        _log_repo_event("PURCHASE_MARKET_ITEM", telegram_id=telegram_id, item_slug=item_slug, price=price, new_demand=new_demand)
        return price
    except Exception:
        logger.exception(
            "PURCHASE_MARKET_ITEM_FAIL | telegram_id=%s | item_slug=%r",
            telegram_id,
            item_slug,
        )
        raise

def purchase_market_monster(telegram_id: int, monster_slug: str) -> int | None:
    try:
        p = get_player(telegram_id)
        if not p:
            _log_repo_event("PURCHASE_MARKET_MONSTER_NO_PLAYER", telegram_id=telegram_id, monster_slug=monster_slug)
            return None
        price = get_market_monster_price(monster_slug)
        if p.gold < price:
            _log_repo_event("PURCHASE_MARKET_MONSTER_NO_GOLD", telegram_id=telegram_id, monster_slug=monster_slug, price=price, gold=p.gold)
            return None
        _update_player_field(telegram_id, gold=p.gold - price)
        e = get_market_monster_entry(monster_slug)
        new_demand = min(10.0, e.get("demand",0.0) + 1.0)
        with get_connection() as conn:
            conn.execute("UPDATE market_monsters_npc SET demand=?,updated_at=? WHERE monster_slug=?", (new_demand,time.time(),monster_slug))
            conn.commit()
        _log_repo_event("PURCHASE_MARKET_MONSTER", telegram_id=telegram_id, monster_slug=monster_slug, price=price, new_demand=new_demand)
        return price
    except Exception:
        logger.exception(
            "PURCHASE_MARKET_MONSTER_FAIL | telegram_id=%s | monster_slug=%r",
            telegram_id,
            monster_slug,
        )
        raise

# ─── Ресурсный рынок города ───────────────────────────────────────────────────

def _ensure_city_resource_market(city_slug: str):
    with get_connection() as conn:
        for slug, d in DEFAULT_CITY_RESOURCE_MARKET.items():
            conn.execute("""INSERT OR IGNORE INTO city_resource_markets
                (city_slug,resource_slug,base_price,stock,target_stock)
                VALUES (?,?,?,?,?)""",
                (city_slug,slug,d["base_price"],d["stock"],d["target_stock"]))
        conn.commit()

def _resource_decay(entry: dict, drift_per_hour: float = 0.75) -> dict:
    now = time.time()
    updated_at = entry.get("updated_at", 0.0)
    if updated_at:
        hours = max(0.0, (now - updated_at) / 3600.0)
        if hours > 0:
            stock  = float(entry.get("stock", 0))
            target = float(entry.get("target_stock", max(1, stock)))
            if stock > target:
                stock = max(target, stock - hours * drift_per_hour)
            elif stock < target:
                stock = min(target, stock + hours * drift_per_hour * 0.5)
            entry["stock"] = round(stock, 2)
    entry["updated_at"] = now
    return entry

def get_city_resource_market(city_slug: str) -> dict:
    _ensure_city_resource_market(city_slug)
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM city_resource_markets WHERE city_slug=?", (city_slug,)).fetchall()
    result = {}
    for row in rows:
        entry = _resource_decay(dict(row))
        result[row["resource_slug"]] = entry
    return result

def get_city_resource_market_entry(city_slug: str, slug: str) -> dict | None:
    return get_city_resource_market(city_slug).get(slug)

def get_city_resource_sell_price(city_slug: str, slug: str, merchant_level: int = 1, amount: int = 1) -> int:
    entry = get_city_resource_market_entry(city_slug, slug)
    if not entry:
        return 1
    bp     = entry["base_price"]
    stock  = float(entry.get("stock", 0))
    target = max(1.0, float(entry.get("target_stock", 1)))
    sc_r   = max(0.0, (target - stock) / target)
    su_r   = max(0.0, (stock - target) / target)
    mm     = 1.0 + sc_r * 0.35 - min(0.45, su_r * 0.18)
    xm     = 1.0 + max(0, merchant_level - 1) * 0.05
    return max(1, int(round(bp * mm * xm))) * max(1, amount)

def get_city_resource_buy_price(city_slug: str, slug: str, amount: int = 1) -> int:
    entry = get_city_resource_market_entry(city_slug, slug)
    if not entry:
        return 1
    sell  = get_city_resource_sell_price(city_slug, slug, merchant_level=1, amount=1)
    stock = float(entry.get("stock", 0))
    target = max(1.0, float(entry.get("target_stock", 1)))
    sc_r  = max(0.0, (target - stock) / target)
    mu    = 1.25 + sc_r * 0.25
    return max(sell+1, int(round(entry["base_price"] * mu))) * max(1, amount)

def sell_resource_to_city_market(telegram_id: int, city_slug: str, slug: str, amount: int = 1) -> int | None:
    try:
        p = get_player(telegram_id)
        if not p:
            _log_repo_event("SELL_RESOURCE_NO_PLAYER", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount)
            return None
        entry = get_city_resource_market_entry(city_slug, slug)
        if not entry:
            _log_repo_event("SELL_RESOURCE_NO_MARKET_ENTRY", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount)
            return None
        if not spend_resource(telegram_id, slug, amount):
            _log_repo_event("SELL_RESOURCE_NO_STOCK", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount)
            return None
        gold = get_city_resource_sell_price(city_slug, slug, merchant_level=getattr(p,"merchant_level",1), amount=amount)
        if not gold or gold <= 0:
            _log_repo_event("SELL_RESOURCE_BAD_PRICE", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount, gold=gold)
            return None
        _update_player_field(telegram_id, gold=p.gold + gold)
        with get_connection() as conn:
            conn.execute("UPDATE city_resource_markets SET stock=ROUND(stock+?,2) WHERE city_slug=? AND resource_slug=?",
                (amount,city_slug,slug))
            conn.commit()
        _log_repo_event("SELL_RESOURCE", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount, gold=gold)
        return gold
    except Exception:
        logger.exception(
            "SELL_RESOURCE_FAIL | telegram_id=%s | city_slug=%r | slug=%r | amount=%s",
            telegram_id,
            city_slug,
            slug,
            amount,
        )
        raise

def buy_resource_from_city_market(telegram_id: int, city_slug: str, slug: str, amount: int = 1) -> int | None:
    try:
        p = get_player(telegram_id)
        if not p:
            _log_repo_event("BUY_RESOURCE_NO_PLAYER", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount)
            return None
        entry = get_city_resource_market_entry(city_slug, slug)
        if not entry:
            _log_repo_event("BUY_RESOURCE_NO_MARKET_ENTRY", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount)
            return None
        if float(entry.get("stock",0)) < amount:
            _log_repo_event("BUY_RESOURCE_NO_STOCK", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount, stock=entry.get("stock", 0))
            return None
        price = get_city_resource_buy_price(city_slug, slug, amount=amount)
        if p.gold < price:
            _log_repo_event("BUY_RESOURCE_NO_GOLD", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount, price=price, gold=p.gold)
            return None
        _update_player_field(telegram_id, gold=p.gold - price)
        add_resource(telegram_id, slug, amount)
        with get_connection() as conn:
            conn.execute("UPDATE city_resource_markets SET stock=ROUND(MAX(0,stock-?),2) WHERE city_slug=? AND resource_slug=?",
                (amount,city_slug,slug))
            conn.commit()
        _log_repo_event("BUY_RESOURCE", telegram_id=telegram_id, city_slug=city_slug, slug=slug, amount=amount, price=price)
        return price
    except Exception:
        logger.exception(
            "BUY_RESOURCE_FAIL | telegram_id=%s | city_slug=%r | slug=%r | amount=%s",
            telegram_id,
            city_slug,
            slug,
            amount,
        )
        raise

# ─── Система типов ────────────────────────────────────────────────────────────

def get_damage_multiplier(attacker_type: str | None, defender_type: str | None) -> float:
    if not attacker_type or not defender_type:
        return 1.0
    chart = {
        ("flame","nature"):1.5, ("nature","storm"):1.25, ("storm","shadow"):1.25,
        ("shadow","spirit"):1.25, ("spirit","bone"):1.25, ("bone","flame"):1.25,
        ("echo","void"):1.25, ("void","echo"):1.25,
        ("nature","flame"):0.75, ("storm","nature"):0.85, ("shadow","storm"):0.85,
        ("spirit","shadow"):0.85, ("bone","spirit"):0.85, ("flame","bone"):0.85,
    }
    return chart.get((attacker_type, defender_type), 1.0)

def render_type_hint(attacker_type: str | None, defender_type: str | None) -> str:
    m = get_damage_multiplier(attacker_type, defender_type)
    if m >= 1.5: return "🔥 Очень эффективно"
    if m > 1.0:  return "⚔️ Эффективно"
    if m < 1.0:  return "🛡 Слабо"
    return "➖ Без преимущества"

# ─── Таблица лидеров ──────────────────────────────────────────────────────────

def get_leaderboard(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.telegram_id, p.name, p.level, p.gold,
                   COUNT(m.id) as monster_count,
                   pv.wins as pvp_wins, pv.rating as pvp_rating
            FROM players p
            LEFT JOIN player_monsters m ON m.telegram_id = p.telegram_id
            LEFT JOIN player_pvp pv ON pv.telegram_id = p.telegram_id
            GROUP BY p.telegram_id
            ORDER BY p.level DESC, p.experience DESC
            LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]

def get_pvp_leaderboard(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.telegram_id, p.name, p.level, pv.wins, pv.losses, pv.rating
            FROM player_pvp pv
            JOIN players p ON p.telegram_id = pv.telegram_id
            ORDER BY pv.rating DESC
            LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]

# ─── PvP ──────────────────────────────────────────────────────────────────────

def get_pvp_stats(telegram_id: int) -> dict:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO player_pvp (telegram_id) VALUES (?)", (telegram_id,))
        row = conn.execute("SELECT * FROM player_pvp WHERE telegram_id=?", (telegram_id,)).fetchone()
        conn.commit()
    return dict(row) if row else {"wins":0,"losses":0,"rating":1000}

def record_pvp_result(winner_id: int, loser_id: int):
    rating_delta = 25
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO player_pvp (telegram_id) VALUES (?)", (winner_id,))
        conn.execute("INSERT OR IGNORE INTO player_pvp (telegram_id) VALUES (?)", (loser_id,))
        conn.execute("UPDATE player_pvp SET wins=wins+1, rating=rating+? WHERE telegram_id=?", (rating_delta,winner_id))
        conn.execute("UPDATE player_pvp SET losses=losses+1, rating=MAX(0,rating-?) WHERE telegram_id=?", (rating_delta,loser_id))
        conn.commit()

def create_pvp_challenge(challenger_id: int, target_id: int) -> int:
    with get_connection() as conn:
        cur = conn.execute("INSERT INTO pvp_challenges (challenger_id,target_id) VALUES (?,?)", (challenger_id,target_id))
        cid = cur.lastrowid
        conn.commit()
    return cid

def get_pending_challenge(target_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM pvp_challenges WHERE target_id=? AND status='pending' ORDER BY created_at DESC LIMIT 1", (target_id,)).fetchone()
    return dict(row) if row else None

def resolve_pvp_challenge(challenge_id: int, status: str = "accepted"):
    with get_connection() as conn:
        conn.execute("UPDATE pvp_challenges SET status=? WHERE id=?", (status,challenge_id))
        conn.commit()

# ─── Гильдии ──────────────────────────────────────────────────────────────────

def create_guild(name: str, leader_id: int, description: str = "") -> dict | None:
    try:
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO guilds (name,leader_id,description) VALUES (?,?,?)", (name,leader_id,description))
            gid = cur.lastrowid
            conn.execute("INSERT INTO guild_members (guild_id,telegram_id,role) VALUES (?,?,'leader')", (gid,leader_id))
            conn.commit()
        return get_guild_by_id(gid)
    except Exception:
        return None

def get_guild_by_id(guild_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM guilds WHERE id=?", (guild_id,)).fetchone()
    return dict(row) if row else None

def get_player_guild(telegram_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("""SELECT g.* FROM guilds g
            JOIN guild_members gm ON gm.guild_id=g.id
            WHERE gm.telegram_id=?""", (telegram_id,)).fetchone()
    return dict(row) if row else None

def join_guild(guild_id: int, telegram_id: int) -> bool:
    try:
        with get_connection() as conn:
            conn.execute("INSERT INTO guild_members (guild_id,telegram_id) VALUES (?,?)", (guild_id,telegram_id))
            conn.commit()
        return True
    except Exception:
        return False

def leave_guild(telegram_id: int) -> bool:
    with get_connection() as conn:
        conn.execute("DELETE FROM guild_members WHERE telegram_id=?", (telegram_id,))
        conn.commit()
    return True

def get_guild_members(guild_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""SELECT p.telegram_id, p.name, p.level, gm.role
            FROM guild_members gm JOIN players p ON p.telegram_id=gm.telegram_id
            WHERE gm.guild_id=? ORDER BY p.level DESC""", (guild_id,)).fetchall()
    return [dict(r) for r in rows]

def add_guild_treasury(guild_id: int, amount: int):
    with get_connection() as conn:
        conn.execute("UPDATE guilds SET treasury_gold=treasury_gold+? WHERE id=?", (amount,guild_id))
        conn.commit()

def list_guilds(limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""SELECT g.*, COUNT(gm.telegram_id) as member_count
            FROM guilds g LEFT JOIN guild_members gm ON gm.guild_id=g.id
            GROUP BY g.id ORDER BY member_count DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]

# ─── Ежедневные задания ───────────────────────────────────────────────────────

import random as _random
from datetime import date as _date

DAILY_TASK_POOL = [
    {"task_id":"daily_win3",     "description":"Победи 3 монстров в бою",    "action_type":"win",     "target":3, "reward_gold":50},
    {"task_id":"daily_explore5", "description":"Исследуй локации 5 раз",     "action_type":"explore", "target":5, "reward_gold":40},
    {"task_id":"daily_gather3",  "description":"Собери 3 ресурса",           "action_type":"gather",  "target":3, "reward_gold":35},
    {"task_id":"daily_capture1", "description":"Поймай монстра",             "action_type":"capture", "target":1, "reward_gold":60},
    {"task_id":"daily_craft1",   "description":"Создай 1 предмет в мастерской","action_type":"craft", "target":1, "reward_gold":45},
    {"task_id":"daily_win5",     "description":"Победи 5 монстров в бою",    "action_type":"win",     "target":5, "reward_gold":75},
]

def get_today_tasks(telegram_id: int) -> list[dict]:
    today = str(_date.today())
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM daily_tasks WHERE telegram_id=? AND task_date=?", (telegram_id,today)).fetchall()
    if rows:
        return [dict(r) for r in rows]
    # Генерируем 3 случайных задания на сегодня
    chosen = _random.sample(DAILY_TASK_POOL, min(3, len(DAILY_TASK_POOL)))
    with get_connection() as conn:
        for t in chosen:
            conn.execute("""INSERT OR IGNORE INTO daily_tasks
                (telegram_id,task_date,task_id,description,action_type,target,reward_gold)
                VALUES (?,?,?,?,?,?,?)""",
                (telegram_id,today,t["task_id"],t["description"],t["action_type"],t["target"],t["reward_gold"]))
        conn.commit()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM daily_tasks WHERE telegram_id=? AND task_date=?", (telegram_id,today)).fetchall()
    return [dict(r) for r in rows]

def progress_daily_tasks(telegram_id: int, action_type: str, amount: int = 1) -> list[dict]:
    today = str(_date.today())
    tasks = get_today_tasks(telegram_id)
    completed_now = []
    for t in tasks:
        if t["completed"] or t["action_type"] != action_type:
            continue
        new_prog = t["progress"] + amount
        done = new_prog >= t["target"]
        with get_connection() as conn:
            conn.execute("""UPDATE daily_tasks SET progress=?,completed=?
                WHERE telegram_id=? AND task_date=? AND task_id=?""",
                (new_prog,int(done),telegram_id,today,t["task_id"]))
            conn.commit()
        if done:
            completed_now.append(t)
    return completed_now

def check_and_update_daily_streak(telegram_id: int) -> tuple[int, bool]:
    """Возвращает (streak, is_new_day). Вызывать при каждом входе игрока."""
    p = get_player(telegram_id)
    if not p:
        return 0, False
    today = str(_date.today())
    last  = p.last_login_date or ""
    if last == today:
        return p.daily_streak, False
    yesterday = str(_date.fromordinal(_date.today().toordinal()-1))
    new_streak = (p.daily_streak + 1) if last == yesterday else 1
    _update_player_field(telegram_id, daily_streak=new_streak, last_login_date=today)
    return new_streak, True

def get_streak_reward(streak: int) -> int:
    rewards = {1:30, 2:40, 3:55, 4:70, 5:90, 6:110, 7:200}
    return rewards.get(min(streak, 7), 50 + (streak//7)*50)

# ─── Сезонный пасс ────────────────────────────────────────────────────────────

SEASON_TASKS = [
    {"task_id":"s_win20",      "description":"Победи 20 монстров",       "action_type":"win",     "target":20, "reward_gold":100, "premium_reward":250},
    {"task_id":"s_capture10",  "description":"Поймай 10 монстров",       "action_type":"capture", "target":10, "reward_gold":80,  "premium_reward":200},
    {"task_id":"s_gather30",   "description":"Собери 30 ресурсов",       "action_type":"gather",  "target":30, "reward_gold":80,  "premium_reward":180},
    {"task_id":"s_craft5",     "description":"Создай 5 предметов",       "action_type":"craft",   "target":5,  "reward_gold":70,  "premium_reward":160},
    {"task_id":"s_explore40",  "description":"Исследуй локации 40 раз",  "action_type":"explore", "target":40, "reward_gold":90,  "premium_reward":220},
]
CURRENT_SEASON = 1

def get_season_tasks(telegram_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM player_season_pass WHERE telegram_id=? AND season_id=?",
            (telegram_id, CURRENT_SEASON)).fetchall()
    existing = {r["task_id"]: dict(r) for r in rows}
    result = []
    for t in SEASON_TASKS:
        row = existing.get(t["task_id"])
        result.append({
            **t,
            "progress":  row["progress"]  if row else 0,
            "completed": bool(row["completed"]) if row else False,
        })
    return result

def progress_season_tasks(telegram_id: int, action_type: str, amount: int = 1) -> list[dict]:
    tasks = get_season_tasks(telegram_id)
    completed_now = []
    for t in tasks:
        if t["completed"] or t["action_type"] != action_type:
            continue
        new_prog = t["progress"] + amount
        done = new_prog >= t["target"]
        with get_connection() as conn:
            conn.execute("""INSERT INTO player_season_pass (telegram_id,season_id,task_id,progress,completed)
                VALUES (?,?,?,?,?)
                ON CONFLICT(telegram_id,season_id,task_id) DO UPDATE SET progress=?,completed=?""",
                (telegram_id,CURRENT_SEASON,t["task_id"],new_prog,int(done),new_prog,int(done)))
            conn.commit()
        if done:
            completed_now.append(t)
    return completed_now

# ─── P2P рынок монстров ───────────────────────────────────────────────────────

def list_monster_for_sale(telegram_id: int, monster_id: int, price: int) -> bool:
    m = get_monster_by_id(telegram_id, monster_id)
    if not m or m.get("is_active"):
        return False
    m["is_listed"] = True
    m["list_price"] = price
    save_monster(m)
    return True

def delist_monster(telegram_id: int, monster_id: int) -> bool:
    m = get_monster_by_id(telegram_id, monster_id)
    if not m:
        return False
    m["is_listed"] = False
    m["list_price"] = 0
    save_monster(m)
    return True

def get_p2p_market_listings(limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""SELECT m.*, p.name as seller_name
            FROM player_monsters m JOIN players p ON p.telegram_id=m.telegram_id
            WHERE m.is_listed=1 ORDER BY m.list_price ASC LIMIT ?""", (limit,)).fetchall()
    return [_monster_row_to_dict(dict(r)) for r in rows]

def buy_p2p_monster(buyer_id: int, monster_id: int) -> dict | None:
    """Покупка монстра у другого игрока с комиссией 8%."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM player_monsters WHERE id=? AND is_listed=1", (monster_id,)).fetchone()
    if not row:
        return None
    m = _monster_row_to_dict(row)
    seller_id = m["telegram_id"]
    if seller_id == buyer_id:
        return None
    price    = m["list_price"]
    buyer    = get_player(buyer_id)
    if not buyer or buyer.gold < price:
        return None
    commission = int(price * 0.08)
    seller_gets = price - commission
    _update_player_field(buyer_id,  gold=buyer.gold - price)
    seller = get_player(seller_id)
    if seller:
        _update_player_field(seller_id, gold=seller.gold + seller_gets)
    with get_connection() as conn:
        conn.execute("UPDATE player_monsters SET telegram_id=?,is_active=0,is_listed=0,list_price=0 WHERE id=?",
            (buyer_id, monster_id))
        conn.commit()
    return get_monster_by_id(buyer_id, monster_id)

# ─── Аналитика ────────────────────────────────────────────────────────────────

def track(telegram_id: int, event: str, data: dict | None = None):
    try:
        with get_connection() as conn:
            conn.execute("INSERT INTO analytics_events (telegram_id,event,data) VALUES (?,?,?)",
                (telegram_id, event, json_set(data or {})))
            conn.commit()
    except Exception:
        pass

def get_analytics_summary() -> dict:
    with get_connection() as conn:
        total    = conn.execute("SELECT COUNT(*) as c FROM players").fetchone()["c"]
        active7d = conn.execute("""SELECT COUNT(DISTINCT telegram_id) as c FROM analytics_events
            WHERE created_at > datetime('now','-7 days')""").fetchone()["c"]
        events   = conn.execute("""SELECT event, COUNT(*) as cnt FROM analytics_events
            GROUP BY event ORDER BY cnt DESC LIMIT 20""").fetchall()
    return {"total_players":total,"active_7d":active7d,"top_events":[dict(r) for r in events]}


def get_guild_quests_status(telegram_id: int) -> dict:
    """
    Возвращает статус квестов по гильдиям.
    Формат: {"hunter": "active"|"ready"|None, ...}
    """
    result = {}
    try:
        with get_connection() as conn:
            # Выполненные (готовые к сдаче)
            done_rows = conn.execute("""
                SELECT guild_key FROM player_guild_quests
                WHERE telegram_id=? AND completed=1
            """, (telegram_id,)).fetchall()
            for row in done_rows:
                gk = row["guild_key"] or "unknown"
                result[gk] = "ready"
            # Активные (ещё в процессе)
            active_rows = conn.execute("""
                SELECT guild_key FROM player_guild_quests
                WHERE telegram_id=? AND completed=0
            """, (telegram_id,)).fetchall()
            for row in active_rows:
                gk = row["guild_key"] or "unknown"
                if gk not in result:  # ready приоритетнее
                    result[gk] = "active"
    except Exception:
        pass
    return result


def get_npc_quest_status(telegram_id: int, npc_key: str) -> str | None:
    """
    Проверяет статус квеста у конкретного NPC.
    npc_key: "mirna", "varg", "bort", "hunter", "gatherer" и т.д.
    Возвращает: "ready" | "active" | None
    """
    # Маппинг NPC → guild_key в player_guild_quests
    NPC_TO_GUILD = {
        "hunter":    "hunter",
        "gatherer":  "gatherer",
        "geologist": "geologist",
        "alchemist": "alchemist",
        "varg":      "hunter",   # Варг даёт охотничьи квесты
        "mirna":     "gatherer", # Мирна даёт квесты на сбор
        "bort":      "geologist",
    }
    guild_key = NPC_TO_GUILD.get(npc_key, npc_key)

    # Доска заказов - проверяем board quests
    if npc_key == "board":
        try:
            with get_connection() as conn:
                ready = conn.execute(
                    "SELECT COUNT(*) FROM player_board_quests WHERE telegram_id=? AND completed=1",
                    (telegram_id,)
                ).fetchone()[0]
                if ready:
                    return "ready"
                active = conn.execute(
                    "SELECT COUNT(*) FROM player_board_quests WHERE telegram_id=? AND completed=0",
                    (telegram_id,)
                ).fetchone()[0]
                if active:
                    return "active"
        except Exception:
            pass
        return None

    if guild_key is None:
        return None

    try:
        with get_connection() as conn:
            # Гильдейские квесты (player_guild_quests — колонка guild_key)
            ready = conn.execute("""
                SELECT COUNT(*) FROM player_guild_quests
                WHERE telegram_id=? AND guild_key=? AND completed=1
            """, (telegram_id, guild_key)).fetchone()[0]
            if ready:
                return "ready"
            active = conn.execute("""
                SELECT COUNT(*) FROM player_guild_quests
                WHERE telegram_id=? AND guild_key=? AND completed=0
            """, (telegram_id, guild_key)).fetchone()[0]
            if active:
                return "active"
            # Доска заказов (player_board_quests — нет колонки npc, 
            # ищем по quest_id содержащему ключ NPC)
            board_ready = conn.execute("""
                SELECT COUNT(*) FROM player_board_quests
                WHERE telegram_id=? AND completed=1
                AND quest_id LIKE ?
            """, (telegram_id, f"%{npc_key}%")).fetchone()[0]
            if board_ready:
                return "ready"
            board_active = conn.execute("""
                SELECT COUNT(*) FROM player_board_quests
                WHERE telegram_id=? AND completed=0
                AND quest_id LIKE ?
            """, (telegram_id, f"%{npc_key}%")).fetchone()[0]
            if board_active:
                return "active"
    except Exception:
        pass
    return None


# ─── Подземелья (cooldown система) ───────────────────────────────────────────

from datetime import datetime, timedelta


DUNGEON_COOLDOWN_HOURS = 72  # 3 дня


def get_dungeon_cooldown_status(telegram_id: int, dungeon_slug: str) -> dict:
    """
    Проверяет доступность подземелья для игрока.
    Если кулдаун истёк — данж снова считается доступным.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status, cooldown_until
            FROM player_dungeon_progress
            WHERE telegram_id=? AND dungeon_slug=?
            """,
            (telegram_id, dungeon_slug),
        ).fetchone()

    if not row or not row["cooldown_until"]:
        return {
            "available": True,
            "status": "available",
            "cooldown_until": None,
            "remaining_seconds": 0,
        }

    cooldown_until_raw = row["cooldown_until"]
    try:
        cooldown_until = datetime.fromisoformat(cooldown_until_raw)
    except Exception:
        return {
            "available": True,
            "status": "available",
            "cooldown_until": None,
            "remaining_seconds": 0,
        }

    now = datetime.utcnow()

    if now >= cooldown_until:
        return {
            "available": True,
            "status": "available",
            "cooldown_until": None,
            "remaining_seconds": 0,
        }

    remaining = int((cooldown_until - now).total_seconds())

    return {
        "available": False,
        "status": row["status"] or "cleared",
        "cooldown_until": cooldown_until_raw,
        "remaining_seconds": remaining,
    }


def mark_dungeon_cleared(telegram_id: int, dungeon_slug: str, cooldown_hours: int = 72):
    """
    Вызывается после убийства босса.
    Ставит подземелье на кулдаун.
    """
    try:
        now = datetime.utcnow()
        cooldown_until = now + timedelta(hours=cooldown_hours)

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO player_dungeon_progress (
                    telegram_id,
                    dungeon_slug,
                    status,
                    cleared_at,
                    cooldown_until,
                    updated_at
                )
                VALUES (?, ?, 'cleared', ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(telegram_id, dungeon_slug)
                DO UPDATE SET
                    status='cleared',
                    cleared_at=excluded.cleared_at,
                    cooldown_until=excluded.cooldown_until,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    telegram_id,
                    dungeon_slug,
                    now.isoformat(),
                    cooldown_until.isoformat(),
                ),
            )
            conn.commit()
        _log_repo_event(
            "DUNGEON_CLEARED",
            telegram_id=telegram_id,
            dungeon_slug=dungeon_slug,
            cooldown_hours=cooldown_hours,
            cooldown_until=cooldown_until.isoformat(),
        )
    except Exception:
        logger.exception(
            "DUNGEON_CLEARED_FAIL | telegram_id=%s | dungeon_slug=%r | cooldown_hours=%s",
            telegram_id,
            dungeon_slug,
            cooldown_hours,
        )
        raise


def set_dungeon_cleared(telegram_id: int, dungeon_slug: str):
    """
    Совместимость со старым именем.
    """
    return mark_dungeon_cleared(
        telegram_id=telegram_id,
        dungeon_slug=dungeon_slug,
        cooldown_hours=DUNGEON_COOLDOWN_HOURS,
    )


def format_duration_ru(seconds: int) -> str:
    """
    Красиво форматирует время: 2 д. 5 ч. 10 мин.
    """
    seconds = int(seconds)

    days = seconds // 86400
    seconds %= 86400

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60

    parts = []
    if days:
        parts.append(f"{days} д.")
    if hours:
        parts.append(f"{hours} ч.")
    if minutes:
        parts.append(f"{minutes} мин.")

    return " ".join(parts) if parts else "меньше минуты"


# ─── Сумки / инвентарь ───────────────────────────────────────────────────────

def _row_to_bag(row) -> dict | None:
    if not row:
        return None
    return {
        "telegram_id": row["telegram_id"],
        "bag_slug": row["bag_slug"],
        "bag_name": row["bag_name"],
        "capacity": int(row["capacity"]),
        "source": row["source"],
        "is_equipped": bool(row["is_equipped"]),
        "sell_price": int(row["sell_price"] or 0),
        "created_at": row["created_at"],
    }


def _ensure_player_bags_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_bags (
                telegram_id     INTEGER NOT NULL,
                bag_slug        TEXT NOT NULL,
                bag_name        TEXT NOT NULL,
                capacity        INTEGER NOT NULL,
                source          TEXT NOT NULL DEFAULT 'shop',
                is_equipped     INTEGER NOT NULL DEFAULT 0,
                sell_price      INTEGER NOT NULL DEFAULT 0,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, bag_slug)
            )
            """
        )
        conn.commit()


def _ensure_default_bag(telegram_id: int):
    _ensure_player_bags_table()
    player = get_player(telegram_id)
    if not player:
        return
    with get_connection() as conn:
        row = conn.execute(
            "SELECT bag_slug FROM player_bags WHERE telegram_id=? LIMIT 1",
            (telegram_id,),
        ).fetchone()
        if row:
            equipped = conn.execute(
                "SELECT bag_slug, capacity FROM player_bags WHERE telegram_id=? AND is_equipped=1 LIMIT 1",
                (telegram_id,),
            ).fetchone()
            if equipped:
                conn.execute(
                    "UPDATE players SET bag_capacity=? WHERE telegram_id=?",
                    (int(equipped["capacity"]), telegram_id),
                )
                conn.commit()
            return

        cap = max(1, int(getattr(player, "bag_capacity", 12) or 12))
        conn.execute(
            """
            INSERT OR IGNORE INTO player_bags
                (telegram_id, bag_slug, bag_name, capacity, source, is_equipped, sell_price)
            VALUES (?,?,?,?,?,?,?)
            """,
            (telegram_id, "starter_bag", "Стартовая сумка", cap, "starter", 1, 0),
        )
        conn.execute(
            "UPDATE players SET bag_capacity=? WHERE telegram_id=?",
            (cap, telegram_id),
        )
        conn.commit()


def get_player_bags(telegram_id: int) -> list[dict]:
    _ensure_default_bag(telegram_id)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM player_bags
            WHERE telegram_id=?
            ORDER BY is_equipped DESC, capacity DESC, created_at ASC
            """,
            (telegram_id,),
        ).fetchall()
    return [_row_to_bag(r) for r in rows]


def get_equipped_bag(telegram_id: int) -> dict | None:
    _ensure_default_bag(telegram_id)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_bags WHERE telegram_id=? AND is_equipped=1 LIMIT 1",
            (telegram_id,),
        ).fetchone()
    return _row_to_bag(row)


def grant_bag(telegram_id: int, bag_slug: str, bag_name: str, capacity: int, *, source: str = "shop", sell_price: int = 0, auto_equip: bool = True) -> tuple[bool, dict | None]:
    try:
        _ensure_default_bag(telegram_id)
        capacity = int(capacity)
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT * FROM player_bags WHERE telegram_id=? AND bag_slug=?",
                (telegram_id, bag_slug),
            ).fetchone()
            if existing:
                bag = _row_to_bag(existing)
                _log_repo_event("GRANT_BAG_EXISTS", telegram_id=telegram_id, bag_slug=bag_slug)
                return False, bag

            equipped = conn.execute(
                "SELECT * FROM player_bags WHERE telegram_id=? AND is_equipped=1 LIMIT 1",
                (telegram_id,),
            ).fetchone()
            should_equip = bool(auto_equip and (not equipped or capacity > int(equipped["capacity"])))

            if should_equip:
                conn.execute(
                    "UPDATE player_bags SET is_equipped=0 WHERE telegram_id=?",
                    (telegram_id,),
                )

            conn.execute(
                """
                INSERT INTO player_bags
                    (telegram_id, bag_slug, bag_name, capacity, source, is_equipped, sell_price)
                VALUES (?,?,?,?,?,?,?)
                """,
                (telegram_id, bag_slug, bag_name, capacity, source, 1 if should_equip else 0, int(sell_price or 0)),
            )

            if should_equip:
                conn.execute(
                    "UPDATE players SET bag_capacity=? WHERE telegram_id=?",
                    (capacity, telegram_id),
                )
            conn.commit()

            row = conn.execute(
                "SELECT * FROM player_bags WHERE telegram_id=? AND bag_slug=?",
                (telegram_id, bag_slug),
            ).fetchone()
        bag = _row_to_bag(row)
        _log_repo_event("GRANT_BAG", telegram_id=telegram_id, bag_slug=bag_slug, capacity=capacity, should_equip=should_equip, source=source)
        return True, bag
    except Exception:
        logger.exception(
            "GRANT_BAG_FAIL | telegram_id=%s | bag_slug=%r | capacity=%s | source=%r",
            telegram_id,
            bag_slug,
            capacity,
            source,
        )
        raise


def equip_bag(telegram_id: int, bag_slug: str) -> bool:
    try:
        _ensure_default_bag(telegram_id)
        bag = None
        for item in get_player_bags(telegram_id):
            if item["bag_slug"] == bag_slug:
                bag = item
                break
        if not bag:
            _log_repo_event("EQUIP_BAG_NOT_FOUND", telegram_id=telegram_id, bag_slug=bag_slug)
            return False

        total_resources = get_resources_count_total(telegram_id)
        total_items = sum(get_inventory(telegram_id).values())
        used_slots = total_resources + total_items
        if used_slots > int(bag["capacity"]):
            _log_repo_event("EQUIP_BAG_NO_SPACE", telegram_id=telegram_id, bag_slug=bag_slug, used_slots=used_slots, capacity=bag["capacity"])
            return False

        with get_connection() as conn:
            conn.execute("UPDATE player_bags SET is_equipped=0 WHERE telegram_id=?", (telegram_id,))
            conn.execute(
                "UPDATE player_bags SET is_equipped=1 WHERE telegram_id=? AND bag_slug=?",
                (telegram_id, bag_slug),
            )
            conn.execute(
                "UPDATE players SET bag_capacity=? WHERE telegram_id=?",
                (int(bag["capacity"]), telegram_id),
            )
            conn.commit()
        _log_repo_event("EQUIP_BAG", telegram_id=telegram_id, bag_slug=bag_slug, capacity=bag["capacity"])
        return True
    except Exception:
        logger.exception(
            "EQUIP_BAG_FAIL | telegram_id=%s | bag_slug=%r",
            telegram_id,
            bag_slug,
        )
        raise


def sell_bag(telegram_id: int, bag_slug: str) -> int | None:
    try:
        _ensure_default_bag(telegram_id)
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM player_bags WHERE telegram_id=? AND bag_slug=?",
                (telegram_id, bag_slug),
            ).fetchone()
            if not row:
                _log_repo_event("SELL_BAG_NOT_FOUND", telegram_id=telegram_id, bag_slug=bag_slug)
                return None
            bag = _row_to_bag(row)
            if bag["is_equipped"]:
                _log_repo_event("SELL_BAG_EQUIPPED_DENIED", telegram_id=telegram_id, bag_slug=bag_slug)
                return None
            price = int(bag.get("sell_price") or 0)
            conn.execute(
                "DELETE FROM player_bags WHERE telegram_id=? AND bag_slug=? AND is_equipped=0",
                (telegram_id, bag_slug),
            )
            if price > 0:
                conn.execute(
                    "UPDATE players SET gold=gold+? WHERE telegram_id=?",
                    (price, telegram_id),
                )
            conn.commit()
        _log_repo_event("SELL_BAG", telegram_id=telegram_id, bag_slug=bag_slug, price=price)
        return price
    except Exception:
        logger.exception(
            "SELL_BAG_FAIL | telegram_id=%s | bag_slug=%r",
            telegram_id,
            bag_slug,
        )
        raise
