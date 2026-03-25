"""
crystal_service.py — полноценная система кристаллов для хранения монстров.

Цели:
- каждый монстр обязан храниться в кристалле;
- у нового игрока всегда есть стартовый кристалл;
- старые игроки и старые монстры автоматически мигрируют;
- покупка и поимка монстров могут заранее проверить, есть ли подходящий кристалл;
- текущие handlers/crystals.py, handlers/monsters.py и city.py остаются совместимыми.
"""

from __future__ import annotations

from typing import Iterable

from database.repositories import get_connection


# ──────────────────────────────────────────────────────────────────────────────
# Шаблоны кристаллов
# ──────────────────────────────────────────────────────────────────────────────

CRYSTAL_TEMPLATES = {
    "simple_quartz": {
        "name": "💎 Простой кварц",
        "rarity": "common",
        "emotion_affinity": "neutral",
        "max_volume": 5,
        "max_monsters": 2,
        "buy_price": 50,
        "sell_price": 20,
        "desc": "Начальный кристалл. Вмещает 2 монстра небольшого размера.",
    },
    "cut_quartz": {
        "name": "💠 Огранённый кварц",
        "rarity": "uncommon",
        "emotion_affinity": "neutral",
        "max_volume": 8,
        "max_monsters": 2,
        "buy_price": 120,
        "sell_price": 50,
        "desc": "Улучшенный кварц с большей вместимостью.",
    },
    "amber_vessel": {
        "name": "🟡 Янтарный сосуд",
        "rarity": "rare",
        "emotion_affinity": "joy",
        "max_volume": 10,
        "max_monsters": 3,
        "buy_price": 250,
        "sell_price": 100,
        "desc": "Резонирует с радостью. Лучше подходит для светлых монстров.",
    },
    "crimson_crystal": {
        "name": "🔴 Багровый кристалл",
        "rarity": "rare",
        "emotion_affinity": "rage",
        "max_volume": 8,
        "max_monsters": 1,
        "buy_price": 250,
        "sell_price": 100,
        "desc": "Кристалл ярости. Один, но мощный монстр.",
    },
    "shadow_shard": {
        "name": "🖤 Осколок тени",
        "rarity": "rare",
        "emotion_affinity": "fear",
        "max_volume": 9,
        "max_monsters": 2,
        "buy_price": 220,
        "sell_price": 90,
        "desc": "Резонирует со страхом и тёмными следами.",
    },
    "crystal_of_sadness": {
        "name": "🔵 Кристалл печали",
        "rarity": "uncommon",
        "emotion_affinity": "sadness",
        "max_volume": 7,
        "max_monsters": 2,
        "buy_price": 140,
        "sell_price": 60,
        "desc": "Холодный кристалл для спокойных и стойких существ.",
    },
}

EMOTION_AFFINITY_BONUS = {
    ("rage", "rage"): 1.10,
    ("joy", "joy"): 1.08,
    ("fear", "fear"): 1.05,
    ("sadness", "sadness"): 1.05,
    ("instinct", "neutral"): 1.03,
    ("inspiration", "neutral"): 1.03,
    ("rage", "joy"): 0.95,
    ("joy", "rage"): 0.95,
}

HOME_CRYSTAL_REGEN_PCT = 0.15
BOND_BATTLES_PER_LEVEL = 10
BOND_MAX_LEVEL = 5
BOND_ATK_BONUS = 0.05
CRACK_THRESHOLD_CRACKED = 3
CRACK_THRESHOLD_BROKEN = 6
CRACK_ATK_PENALTY = 0.10
UNSTABLE_ATK_PENALTY = 0.15
VARG_RENT_PRICE = 35


# ──────────────────────────────────────────────────────────────────────────────
# Имена редких кристаллов
# ──────────────────────────────────────────────────────────────────────────────

_NAMED_PREFIXES = {
    "rage": ["Багровое", "Пылающее", "Яростное", "Огненное"],
    "joy": ["Золотое", "Лучезарное", "Светлое", "Янтарное"],
    "fear": ["Теневое", "Мрачное", "Тёмное", "Ночное"],
    "sadness": ["Туманное", "Слезливое", "Серое", "Печальное"],
    "instinct": ["Острое", "Дикое", "Первозданное", "Звериное"],
    "inspiration": ["Лунное", "Мечтательное", "Небесное", "Хрустальное"],
    "neutral": ["Чистое", "Молчаливое", "Тихое", "Древнее"],
}
_NAMED_NOUNS = [
    "Сердце", "Призма", "Осколок", "Сосуд", "Зеркало",
    "Слеза", "Коготь", "Жемчуг", "Клык", "Оплот",
]
_NAMED_SUFFIXES = [
    "Мирны", "Тумана", "Бури", "Рассвета", "Забвения",
    "Судьбы", "Вечности", "Разлома", "Глубин", "Тишины",
]


# ──────────────────────────────────────────────────────────────────────────────
# База и миграции
# ──────────────────────────────────────────────────────────────────────────────

_crystal_tables_ok = False
_storage_ok = False


def _ensure_crystal_tables():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_crystals (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id      INTEGER NOT NULL,
                template_code    TEXT    NOT NULL DEFAULT 'simple_quartz',
                name             TEXT    NOT NULL,
                rarity           TEXT    NOT NULL DEFAULT 'common',
                emotion_affinity TEXT    NOT NULL DEFAULT 'neutral',
                max_volume       INTEGER NOT NULL DEFAULT 5,
                max_monsters     INTEGER NOT NULL DEFAULT 2,
                current_volume   INTEGER NOT NULL DEFAULT 0,
                current_monsters INTEGER NOT NULL DEFAULT 0,
                state            TEXT    NOT NULL DEFAULT 'normal',
                battle_count     INTEGER NOT NULL DEFAULT 0,
                crack_count      INTEGER NOT NULL DEFAULT 0,
                location         TEXT    NOT NULL DEFAULT 'on_hand',
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS monster_crystal_bond (
                monster_id    INTEGER NOT NULL,
                crystal_id    INTEGER NOT NULL,
                battles       INTEGER NOT NULL DEFAULT 0,
                bond_level    INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (monster_id, crystal_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS crystal_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER NOT NULL,
                crystal_id   INTEGER,
                monster_id   INTEGER,
                action       TEXT NOT NULL,
                detail       TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cols = [r[1] for r in conn.execute("PRAGMA table_info(player_monsters)").fetchall()]
        if "crystal_id" not in cols:
            conn.execute("ALTER TABLE player_monsters ADD COLUMN crystal_id INTEGER DEFAULT NULL")
        if "storage_volume" not in cols:
            conn.execute("ALTER TABLE player_monsters ADD COLUMN storage_volume INTEGER NOT NULL DEFAULT 1")
        if "is_summoned" not in cols:
            conn.execute("ALTER TABLE player_monsters ADD COLUMN is_summoned INTEGER NOT NULL DEFAULT 0")

        conn.commit()


def _ensure_storage_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_crystal_storage (
                telegram_id  INTEGER PRIMARY KEY,
                varg_slots   INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cols = [r[1] for r in conn.execute("PRAGMA table_info(player_crystals)").fetchall()]
        if "location" not in cols:
            conn.execute("ALTER TABLE player_crystals ADD COLUMN location TEXT NOT NULL DEFAULT 'on_hand'")
        conn.commit()


def _lazy():
    global _crystal_tables_ok
    if not _crystal_tables_ok:
        _ensure_crystal_tables()
        _crystal_tables_ok = True


def _ensure_storage():
    global _storage_ok
    _lazy()
    if not _storage_ok:
        _ensure_storage_table()
        _storage_ok = True


def _log(telegram_id: int, action: str, crystal_id: int | None = None, monster_id: int | None = None, detail: str = ""):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO crystal_log (telegram_id, crystal_id, monster_id, action, detail) VALUES (?,?,?,?,?)",
                (telegram_id, crystal_id, monster_id, action, detail),
            )
            conn.commit()
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Базовые вычисления
# ──────────────────────────────────────────────────────────────────────────────


def calculate_monster_volume(monster: dict) -> int:
    level = int(monster.get("level", 1) or 1)
    rarity = monster.get("rarity", "common")
    base = min(((level - 1) // 2) + 1, 5)
    rarity_mod = {
        "common": 0,
        "uncommon": 1,
        "rare": 1,
        "epic": 2,
        "legendary": 3,
        "mythic": 4,
    }.get(rarity, 0)
    return max(1, base + rarity_mod)


def get_affinity_bonus(monster_mood: str, crystal_affinity: str) -> float:
    return EMOTION_AFFINITY_BONUS.get((monster_mood, crystal_affinity), 1.0)


def generate_crystal_name(template_code: str, rarity: str) -> str:
    if rarity not in ("rare", "epic", "legendary"):
        return CRYSTAL_TEMPLATES.get(template_code, {}).get("name", "Кристалл")

    import random

    tmpl = CRYSTAL_TEMPLATES.get(template_code, {})
    affinity = tmpl.get("emotion_affinity", "neutral")
    prefix = random.choice(_NAMED_PREFIXES.get(affinity, _NAMED_PREFIXES["neutral"]))
    noun = random.choice(_NAMED_NOUNS)
    if rarity == "legendary":
        suffix = random.choice(_NAMED_SUFFIXES)
        return f"✨ {prefix} {noun} {suffix}"
    return f"💎 {prefix} {noun}"


def _monster_row(monster_id: int, telegram_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM player_monsters WHERE id=? AND telegram_id=?",
            (monster_id, telegram_id),
        ).fetchone()


# ──────────────────────────────────────────────────────────────────────────────
# Кристаллы игрока
# ──────────────────────────────────────────────────────────────────────────────


def create_crystal(telegram_id: int, template_code: str) -> dict:
    _ensure_storage()
    tmpl = CRYSTAL_TEMPLATES.get(template_code, CRYSTAL_TEMPLATES["simple_quartz"])
    crystal_name = generate_crystal_name(template_code, tmpl["rarity"])

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO player_crystals
            (telegram_id, template_code, name, rarity, emotion_affinity,
             max_volume, max_monsters, current_volume, current_monsters, state, location)
            VALUES (?,?,?,?,?,?,?,0,0,'normal','on_hand')
            """,
            (
                telegram_id,
                template_code,
                crystal_name,
                tmpl["rarity"],
                tmpl["emotion_affinity"],
                tmpl["max_volume"],
                tmpl["max_monsters"],
            ),
        )
        cid = cur.lastrowid
        conn.commit()

    _log(telegram_id, "crystal_created", crystal_id=cid, detail=template_code)
    return get_crystal(cid)


def ensure_starter_crystal(telegram_id: int) -> bool:
    _ensure_storage()
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM player_crystals WHERE telegram_id=?",
            (telegram_id,),
        ).fetchone()[0]
    if count == 0:
        create_crystal(telegram_id, "simple_quartz")
        return True
    return False


def get_player_crystals(telegram_id: int) -> list[dict]:
    _ensure_storage()
    normalize_player_crystals(telegram_id)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM player_crystals WHERE telegram_id=? ORDER BY location='on_hand' DESC, id",
            (telegram_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_crystal(crystal_id: int) -> dict | None:
    _ensure_storage()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM player_crystals WHERE id=?", (crystal_id,)).fetchone()
    return dict(row) if row else None


def get_monsters_in_crystal(crystal_id: int) -> list[dict]:
    _ensure_storage()
    from database.db import json_get

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM player_monsters WHERE crystal_id=? ORDER BY is_active DESC, level DESC, id",
            (crystal_id,),
        ).fetchall()

    result = []
    for row in rows:
        item = dict(row)
        item["abilities"] = json_get(item.get("abilities", "[]"))
        result.append(item)
    return result


def recalculate_crystal_load(crystal_id: int):
    _ensure_storage()
    monsters = get_monsters_in_crystal(crystal_id)
    total_volume = sum(int(m.get("storage_volume") or calculate_monster_volume(m)) for m in monsters)
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET current_volume=?, current_monsters=? WHERE id=?",
            (total_volume, len(monsters), crystal_id),
        )
        conn.commit()


def normalize_player_crystals(telegram_id: int):
    """Приводит текущую загрузку кристаллов к фактической по монстрам."""
    _ensure_storage()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM player_crystals WHERE telegram_id=?",
            (telegram_id,),
        ).fetchall()
    for row in rows:
        recalculate_crystal_load(row["id"])


def _get_varg_storage_slots(telegram_id: int) -> int:
    _ensure_storage()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT varg_slots FROM player_crystal_storage WHERE telegram_id=?",
            (telegram_id,),
        ).fetchone()
    return int(row["varg_slots"]) if row else 0


def get_crystal_capacity(telegram_id: int) -> dict:
    """
    Лимит кристаллов на руках и на хранении.
    На руках: 1 базовый + бонусы экипировки.
    У Варга: платные слоты хранения.
    """
    _ensure_storage()
    on_hand_limit = 1
    try:
        from game.equipment_service import get_equipped
        belt = get_equipped(telegram_id).get("belt")
        if belt:
            on_hand_limit += int(belt.get("crystal_slots", 0) or 0)
    except Exception:
        pass

    varg_limit = _get_varg_storage_slots(telegram_id)
    crystals = get_player_crystals(telegram_id)
    on_hand_now = sum(1 for c in crystals if c.get("location", "on_hand") == "on_hand")
    varg_now = sum(1 for c in crystals if c.get("location") == "varg")

    return {
        "on_hand_limit": on_hand_limit,
        "on_hand_now": on_hand_now,
        "on_hand_free": max(0, on_hand_limit - on_hand_now),
        "varg_limit": varg_limit,
        "varg_now": varg_now,
        "varg_free": max(0, varg_limit - varg_now),
    }


def can_add_crystal(telegram_id: int, target_location: str = "on_hand") -> tuple[bool, str]:
    cap = get_crystal_capacity(telegram_id)
    if target_location == "on_hand":
        if cap["on_hand_free"] <= 0:
            return False, (
                "❌ У тебя нет места для нового кристалла на руках.\n"
                "Сдай лишний кристалл Варгу, купи ремень со слотами или освободи место."
            )
        return True, ""

    if target_location == "varg":
        if cap["varg_free"] <= 0:
            return False, "❌ Нет свободных арендованных слотов у Варга."
        return True, ""

    return False, "Неизвестное место хранения."


def rent_varg_slot(telegram_id: int, gold: int) -> tuple[bool, str, int]:
    _ensure_storage()
    if gold < VARG_RENT_PRICE:
        return False, f"❌ Нужно {VARG_RENT_PRICE}з для аренды ячейки у Варга.", gold

    with get_connection() as conn:
        row = conn.execute(
            "SELECT varg_slots FROM player_crystal_storage WHERE telegram_id=?",
            (telegram_id,),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE player_crystal_storage SET varg_slots=varg_slots+1 WHERE telegram_id=?",
                (telegram_id,),
            )
        else:
            conn.execute(
                "INSERT INTO player_crystal_storage (telegram_id, varg_slots) VALUES (?, 1)",
                (telegram_id,),
            )
        conn.commit()

    return True, "✅ У Варга арендована новая ячейка хранения.", gold - VARG_RENT_PRICE


def move_crystal_to_varg(telegram_id: int, crystal_id: int) -> tuple[bool, str]:
    _ensure_storage()
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден."
    if crystal.get("location", "on_hand") == "varg":
        return False, "Этот кристалл уже хранится у Варга."
    ok, msg = can_add_crystal(telegram_id, "varg")
    if not ok:
        return False, msg
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET location='varg' WHERE id=?",
            (crystal_id,),
        )
        conn.commit()
    _log(telegram_id, "move_to_varg", crystal_id=crystal_id)
    return True, f"🏪 {crystal['name']} отправлен на хранение к Варгу."


def move_crystal_from_varg(telegram_id: int, crystal_id: int) -> tuple[bool, str]:
    _ensure_storage()
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден."
    if crystal.get("location", "on_hand") == "on_hand":
        return False, "Этот кристалл уже у тебя на руках."
    ok, msg = can_add_crystal(telegram_id, "on_hand")
    if not ok:
        return False, msg
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET location='on_hand' WHERE id=?",
            (crystal_id,),
        )
        conn.commit()
    _log(telegram_id, "move_from_varg", crystal_id=crystal_id)
    return True, f"🎒 {crystal['name']} снова у тебя на руках."


# ──────────────────────────────────────────────────────────────────────────────
# Проверка и размещение монстров
# ──────────────────────────────────────────────────────────────────────────────


def _iter_usable_crystals(telegram_id: int) -> Iterable[dict]:
    for crystal in get_player_crystals(telegram_id):
        if crystal.get("location", "on_hand") != "on_hand":
            continue
        if crystal.get("state", "normal") != "normal":
            continue
        yield crystal


def find_free_crystal(telegram_id: int, volume_needed: int) -> dict | None:
    for crystal in _iter_usable_crystals(telegram_id):
        free_volume = int(crystal["max_volume"] - crystal["current_volume"])
        free_slots = int(crystal["max_monsters"] - crystal["current_monsters"])
        if free_volume >= volume_needed and free_slots > 0:
            return crystal
    return None


def get_available_crystals_for_monster(telegram_id: int, monster: dict | None = None, volume_needed: int | None = None) -> list[dict]:
    if volume_needed is None:
        if monster is None:
            raise ValueError("Нужно передать monster или volume_needed")
        volume_needed = calculate_monster_volume(monster)

    result = []
    for crystal in _iter_usable_crystals(telegram_id):
        free_volume = int(crystal["max_volume"] - crystal["current_volume"])
        free_slots = int(crystal["max_monsters"] - crystal["current_monsters"])
        if free_volume >= volume_needed and free_slots > 0:
            result.append(crystal)
    return result


def can_receive_monster(telegram_id: int, monster: dict | None = None, volume_needed: int | None = None) -> tuple[bool, str, dict | None]:
    ensure_starter_crystal(telegram_id)
    crystals = get_available_crystals_for_monster(telegram_id, monster=monster, volume_needed=volume_needed)
    if crystals:
        best = sorted(
            crystals,
            key=lambda c: (c["current_monsters"], c["current_volume"], c["id"]),
        )[0]
        return True, f"Можно разместить в {best['name']}.", best

    need = volume_needed
    if need is None and monster is not None:
        need = calculate_monster_volume(monster)
    need = need or 1
    return False, (
        f"❌ Нет свободного кристалла для монстра.\n"
        f"Нужно хотя бы {need} ед. объёма и 1 свободный слот в кристалле на руках."
    ), None


def store_monster_in_crystal(telegram_id: int, monster_id: int, crystal_id: int) -> tuple[bool, str]:
    _ensure_storage()
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден."
    if crystal.get("location", "on_hand") != "on_hand":
        return False, "Этот кристалл сейчас не у тебя на руках."
    if crystal.get("state", "normal") != "normal":
        return False, f"Кристалл недоступен: {crystal['state']}"

    row = _monster_row(monster_id, telegram_id)
    if not row:
        return False, "Монстр не найден."

    monster = dict(row)
    volume = calculate_monster_volume(monster)
    old_crystal_id = monster.get("crystal_id")

    if old_crystal_id == crystal_id:
        return True, f"{monster['name']} уже хранится в {crystal['name']}."

    free_v = int(crystal["max_volume"] - crystal["current_volume"])
    free_s = int(crystal["max_monsters"] - crystal["current_monsters"])
    if free_v < volume:
        return False, f"Недостаточно объёма в кристалле ({volume} нужно, {free_v} свободно)."
    if free_s < 1:
        return False, "В этом кристалле больше нет свободных мест."

    with get_connection() as conn:
        if old_crystal_id:
            old_crystal = get_crystal(old_crystal_id)
            if old_crystal:
                conn.execute(
                    "UPDATE player_crystals SET current_volume=MAX(0,current_volume-?), current_monsters=MAX(0,current_monsters-1) WHERE id=?",
                    (int(monster.get("storage_volume") or volume), old_crystal_id),
                )

        conn.execute(
            "UPDATE player_monsters SET crystal_id=?, storage_volume=?, is_summoned=0 WHERE id=?",
            (crystal_id, volume, monster_id),
        )
        conn.execute(
            "UPDATE player_crystals SET current_volume=current_volume+?, current_monsters=current_monsters+1 WHERE id=?",
            (volume, crystal_id),
        )
        conn.commit()

    _log(telegram_id, "store", crystal_id=crystal_id, monster_id=monster_id, detail=f"volume={volume}")
    return True, f"✅ {monster['name']} помещён в {crystal['name']}."


def auto_store_new_monster(telegram_id: int, monster_id: int) -> tuple[bool, str]:
    row = _monster_row(monster_id, telegram_id)
    if not row:
        return False, "Монстр не найден."
    monster = dict(row)
    ok, msg, best = can_receive_monster(telegram_id, monster=monster)
    if not ok or not best:
        _log(telegram_id, "failed_store_no_crystal", monster_id=monster_id, detail=msg)
        return False, msg
    return store_monster_in_crystal(telegram_id, monster_id, best["id"])


# ──────────────────────────────────────────────────────────────────────────────
# Призыв и возврат
# ──────────────────────────────────────────────────────────────────────────────


def get_summoned_monster(telegram_id: int) -> dict | None:
    _ensure_storage()
    from database.db import json_get

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_monsters WHERE telegram_id=? AND is_summoned=1 LIMIT 1",
            (telegram_id,),
        ).fetchone()
    if not row:
        return None
    item = dict(row)
    item["abilities"] = json_get(item.get("abilities", "[]"))
    return item


def summon_monster(telegram_id: int, monster_id: int) -> tuple[bool, str]:
    _ensure_storage()
    row = _monster_row(monster_id, telegram_id)
    if not row:
        return False, "Монстр не найден."

    monster = dict(row)
    if monster.get("is_dead"):
        return False, "Этот монстр пал — сначала возроди его."
    crystal_id = monster.get("crystal_id")
    if not crystal_id:
        return False, "У монстра нет назначенного кристалла."
    crystal = get_crystal(crystal_id)
    if not crystal:
        return False, "Кристалл монстра не найден."
    if crystal.get("location", "on_hand") != "on_hand":
        return False, f"Кристалл {crystal['name']} сейчас на хранении у Варга."
    if crystal.get("state") == "broken":
        return False, "Кристалл разбит — сначала почини его."

    with get_connection() as conn:
        conn.execute(
            "UPDATE player_monsters SET is_summoned=0, is_active=0 WHERE telegram_id=?",
            (telegram_id,),
        )
        conn.execute(
            "UPDATE player_monsters SET is_summoned=1, is_active=1 WHERE id=? AND telegram_id=?",
            (monster_id, telegram_id),
        )
        conn.commit()

    _log(telegram_id, "summon", crystal_id=crystal_id, monster_id=monster_id)
    return True, f"✨ {monster['name']} призван из {crystal['name']}."


def return_summoned_monster(telegram_id: int, heal_in_home_crystal: bool = True):
    _ensure_storage()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_monsters WHERE telegram_id=? AND is_summoned=1 LIMIT 1",
            (telegram_id,),
        ).fetchone()
        if not row:
            return
        monster = dict(row)
        monster_id = monster["id"]
        crystal_id = monster.get("crystal_id")

        if heal_in_home_crystal and crystal_id and int(monster.get("current_hp", 0)) > 0:
            heal = max(1, int(int(monster.get("max_hp", 1)) * HOME_CRYSTAL_REGEN_PCT))
            new_hp = min(int(monster.get("max_hp", 1)), int(monster.get("current_hp", 0)) + heal)
            conn.execute(
                "UPDATE player_monsters SET is_summoned=0, current_hp=? WHERE id=?",
                (new_hp, monster_id),
            )
        else:
            conn.execute(
                "UPDATE player_monsters SET is_summoned=0 WHERE id=?",
                (monster_id,),
            )
        conn.commit()

    _log(telegram_id, "return", crystal_id=crystal_id, monster_id=monster_id)


# ──────────────────────────────────────────────────────────────────────────────
# Миграция старых игроков и сиротских монстров
# ──────────────────────────────────────────────────────────────────────────────


def migrate_existing_players() -> int:
    _ensure_storage()
    with get_connection() as conn:
        players = conn.execute("SELECT telegram_id FROM players").fetchall()

    migrated = 0
    for prow in players:
        uid = int(prow["telegram_id"])
        ensure_starter_crystal(uid)

        with get_connection() as conn:
            orphan_rows = conn.execute(
                "SELECT * FROM player_monsters WHERE telegram_id=? AND (crystal_id IS NULL OR crystal_id=0)",
                (uid,),
            ).fetchall()

        for orphan in orphan_rows:
            monster = dict(orphan)
            ok, _, best = can_receive_monster(uid, monster=monster)
            if not ok or not best:
                created = create_crystal(uid, "simple_quartz")
                best = created
            placed, _ = store_monster_in_crystal(uid, monster["id"], best["id"])
            if placed:
                migrated += 1

        normalize_player_crystals(uid)

    return migrated


# ──────────────────────────────────────────────────────────────────────────────
# Боевые модификаторы
# ──────────────────────────────────────────────────────────────────────────────


def get_bond_level(monster_id: int, crystal_id: int) -> int:
    _ensure_storage()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT bond_level FROM monster_crystal_bond WHERE monster_id=? AND crystal_id=?",
            (monster_id, crystal_id),
        ).fetchone()
    return int(row["bond_level"]) if row else 0


def get_combat_modifiers(telegram_id: int, monster_id: int) -> dict:
    _ensure_storage()
    row = _monster_row(monster_id, telegram_id)
    if not row:
        return {"atk_multiplier": 1.0, "note": ""}

    monster = dict(row)
    crystal_id = monster.get("crystal_id")
    mood = monster.get("mood", "instinct")

    if not crystal_id:
        return {
            "atk_multiplier": round(1 - UNSTABLE_ATK_PENALTY, 2),
            "note": f"⚠️ Монстр без кристалла: -{int(UNSTABLE_ATK_PENALTY * 100)}% ATK",
        }

    crystal = get_crystal(crystal_id)
    if not crystal:
        return {
            "atk_multiplier": round(1 - UNSTABLE_ATK_PENALTY, 2),
            "note": "⚠️ Кристалл не найден.",
        }

    multiplier = 1.0
    notes: list[str] = []

    affinity_bonus = get_affinity_bonus(mood, crystal.get("emotion_affinity", "neutral"))
    multiplier *= affinity_bonus
    if affinity_bonus != 1.0:
        diff = int((affinity_bonus - 1.0) * 100)
        sign = "+" if diff > 0 else ""
        notes.append(f"💎 Совместимость: {sign}{diff}% ATK")

    bond = get_bond_level(monster_id, crystal_id)
    if bond > 0:
        bond_bonus = bond * BOND_ATK_BONUS
        multiplier *= (1 + bond_bonus)
        notes.append(f"🔗 Связь ур.{bond}: +{int(bond_bonus * 100)}% ATK")

    state = crystal.get("state", "normal")
    if state == "cracked":
        multiplier *= (1 - CRACK_ATK_PENALTY)
        notes.append(f"⚠️ Трещина: -{int(CRACK_ATK_PENALTY * 100)}% ATK")
    elif state == "broken":
        multiplier *= 0.5
        notes.append("💔 Разбитый кристалл: -50% ATK")

    if crystal.get("location", "on_hand") != "on_hand":
        multiplier *= 0.85
        notes.append("🏪 Кристалл на хранении у Варга")

    return {"atk_multiplier": round(multiplier, 2), "note": " | ".join(notes)}


def record_battle_result(telegram_id: int, monster_id: int, victory: bool):
    _ensure_storage()
    row = _monster_row(monster_id, telegram_id)
    if not row or not row["crystal_id"]:
        return
    crystal_id = row["crystal_id"]

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO monster_crystal_bond (monster_id, crystal_id, battles, bond_level)
            VALUES (?, ?, 1, 0)
            ON CONFLICT(monster_id, crystal_id) DO UPDATE SET battles = battles + 1
            """,
            (monster_id, crystal_id),
        )

        bond = conn.execute(
            "SELECT battles, bond_level FROM monster_crystal_bond WHERE monster_id=? AND crystal_id=?",
            (monster_id, crystal_id),
        ).fetchone()
        if bond:
            new_level = min(BOND_MAX_LEVEL, int(bond["battles"]) // BOND_BATTLES_PER_LEVEL)
            if new_level > int(bond["bond_level"]):
                conn.execute(
                    "UPDATE monster_crystal_bond SET bond_level=? WHERE monster_id=? AND crystal_id=?",
                    (new_level, monster_id, crystal_id),
                )

        if not victory:
            conn.execute(
                "UPDATE player_crystals SET crack_count=crack_count+1 WHERE id=?",
                (crystal_id,),
            )
            crack_row = conn.execute(
                "SELECT crack_count FROM player_crystals WHERE id=?",
                (crystal_id,),
            ).fetchone()
            if crack_row:
                cracks = int(crack_row["crack_count"])
                new_state = "normal"
                if cracks >= CRACK_THRESHOLD_BROKEN:
                    new_state = "broken"
                elif cracks >= CRACK_THRESHOLD_CRACKED:
                    new_state = "cracked"
                conn.execute(
                    "UPDATE player_crystals SET state=? WHERE id=?",
                    (new_state, crystal_id),
                )

        conn.execute(
            "UPDATE player_crystals SET battle_count=battle_count+1 WHERE id=?",
            (crystal_id,),
        )
        conn.commit()


def repair_crystal(telegram_id: int, crystal_id: int, gold: int) -> tuple[bool, str, int]:
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден.", gold
    if crystal.get("state", "normal") == "normal":
        return False, "Кристалл в порядке, ремонт не нужен.", gold

    repair_costs = {"common": 40, "uncommon": 80, "rare": 150, "epic": 280, "legendary": 500}
    cost = repair_costs.get(crystal.get("rarity", "common"), 60)
    if crystal.get("state") == "broken":
        cost *= 2
    if gold < cost:
        return False, f"Нужно {cost}з для ремонта. У тебя {gold}з.", gold

    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET state='normal', crack_count=0 WHERE id=?",
            (crystal_id,),
        )
        conn.commit()

    return True, f"✅ {crystal['name']} восстановлен.", gold - cost


# ──────────────────────────────────────────────────────────────────────────────
# Текстовый UI
# ──────────────────────────────────────────────────────────────────────────────


def render_capacity_hint(telegram_id: int) -> str:
    cap = get_crystal_capacity(telegram_id)
    return (
        f"🎒 На руках: {cap['on_hand_now']}/{cap['on_hand_limit']}\n"
        f"🏪 У Варга: {cap['varg_now']}/{cap['varg_limit']}\n"
        f"Свободно на руках: {cap['on_hand_free']}"
    )


def render_crystal_list(telegram_id: int) -> str:
    ensure_starter_crystal(telegram_id)
    crystals = get_player_crystals(telegram_id)
    cap = get_crystal_capacity(telegram_id)

    lines = [
        "💎 Твои кристаллы",
        "",
        f"🎒 На руках: {cap['on_hand_now']}/{cap['on_hand_limit']}",
        f"🏪 У Варга: {cap['varg_now']}/{cap['varg_limit']}",
        "",
    ]

    if not crystals:
        lines.append("У тебя пока нет кристаллов.")
        return "\n".join(lines)

    for crystal in crystals:
        loc = "🎒" if crystal.get("location", "on_hand") == "on_hand" else "🏪"
        state_map = {"normal": "", "cracked": " ⚠️", "broken": " 💔"}
        lines.append(
            f"{loc} {crystal['name']}{state_map.get(crystal.get('state', 'normal'), '')}\n"
            f"   Вместимость: {crystal['current_monsters']}/{crystal['max_monsters']} монстр. | "
            f"{crystal['current_volume']}/{crystal['max_volume']} объёма"
        )
    return "\n".join(lines)


def render_crystal_detail(crystal_id: int) -> str:
    crystal = get_crystal(crystal_id)
    if not crystal:
        return "Кристалл не найден."

    recalculate_crystal_load(crystal_id)
    crystal = get_crystal(crystal_id) or crystal
    monsters = get_monsters_in_crystal(crystal_id)
    loc = "на руках" if crystal.get("location", "on_hand") == "on_hand" else "у Варга"
    state_text = {"normal": "в порядке", "cracked": "треснул", "broken": "разбит"}.get(crystal.get("state", "normal"), "неизвестно")

    lines = [
        f"💎 {crystal['name']}",
        f"Редкость: {crystal['rarity']}",
        f"Эмоциональная настройка: {crystal['emotion_affinity']}",
        f"Состояние: {state_text}",
        f"Где находится: {loc}",
        f"Вместимость: {crystal['current_monsters']}/{crystal['max_monsters']} монстр.",
        f"Объём: {crystal['current_volume']}/{crystal['max_volume']}",
        "",
        CRYSTAL_TEMPLATES.get(crystal.get("template_code"), {}).get("desc", ""),
        "",
        "Монстры внутри:",
    ]

    if not monsters:
        lines.append("• Пусто")
    else:
        for monster in monsters:
            bond = get_bond_level(monster["id"], crystal_id)
            active = " ⚡" if monster.get("is_summoned") else (" ⭐" if monster.get("is_active") else "")
            dead = " 💀" if monster.get("is_dead") else ""
            lines.append(
                f"• {monster['name']} ур.{monster.get('level', 1)}{active}{dead} | "
                f"объём {monster.get('storage_volume', calculate_monster_volume(monster))} | "
                f"связь {bond}"
            )

    return "\n".join(line for line in lines if line is not None)
