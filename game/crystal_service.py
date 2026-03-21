"""
crystal_service.py — Система кристаллов для хранения монстров.

Архитектура:
- Каждый монстр хранится в кристалле
- У игрока есть несколько кристаллов разной вместимости
- Активный монстр автоматически призывается/возвращается
- Эмоциональная совместимость даёт бонусы (фаза 2)
"""
import random
from database.repositories import get_connection

# ── Шаблоны кристаллов ────────────────────────────────────────────────────────
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
        "desc": "Резонирует с радостью. Монстры радости здесь сильнее.",
    },
    "crimson_crystal": {
        "name": "🔴 Багровый кристалл",
        "rarity": "rare",
        "emotion_affinity": "rage",
        "max_volume": 8,
        "max_monsters": 1,
        "buy_price": 250,
        "sell_price": 100,
        "desc": "Усиливает ярость. Один, но мощный монстр.",
    },
    "shadow_shard": {
        "name": "🖤 Осколок тени",
        "rarity": "rare",
        "emotion_affinity": "fear",
        "max_volume": 9,
        "max_monsters": 2,
        "buy_price": 220,
        "sell_price": 90,
        "desc": "Резонирует со страхом. Монстры страха быстрее регенерируют.",
    },
    "crystal_of_sadness": {
        "name": "🔵 Кристалл печали",
        "rarity": "uncommon",
        "emotion_affinity": "sadness",
        "max_volume": 7,
        "max_monsters": 2,
        "buy_price": 140,
        "sell_price": 60,
        "desc": "Хранит грусть. Монстры грусти устойчивее.",
    },
}

# Совместимость эмоций → бонус к ATK монстра
EMOTION_AFFINITY_BONUS = {
    # (monster_mood, crystal_affinity): atk_multiplier
    ("rage",        "rage"):        1.10,
    ("joy",         "joy"):         1.08,
    ("fear",        "fear"):        1.05,
    ("sadness",     "sadness"):     1.05,
    ("instinct",    "neutral"):     1.03,
    ("inspiration", "neutral"):     1.03,
    # Конфликт — небольшой штраф
    ("rage",        "joy"):         0.95,
    ("joy",         "rage"):        0.95,
}

# HP регенерация в "домашнем" кристалле (% от max_hp за бой)
HOME_CRYSTAL_REGEN_PCT = 0.15  # 15% HP после каждого боя

# Уровни связи монстра с кристаллом
# Каждые 10 боёв = уровень связи +1 (макс 5)
BOND_BATTLES_PER_LEVEL = 10
BOND_MAX_LEVEL = 5
BOND_ATK_BONUS = 0.05  # +5% ATK за каждый уровень связи

# Трещины: если монстр проигрывает бой в кристалле
# После 3 поражений кристалл трескается (cracked)
# Треснутый кристалл даёт -10% ATK монстру внутри
# После 6 поражений = broken (нельзя использовать, нужен ремонт)
CRACK_THRESHOLD_CRACKED = 3
CRACK_THRESHOLD_BROKEN = 6
CRACK_ATK_PENALTY = 0.10

# Нестабильность: монстр без кристалла
UNSTABLE_ATK_PENALTY = 0.15  # -15% ATK если нет кристалла


def calculate_monster_volume(monster: dict) -> int:
    """Объём который монстр занимает в кристалле."""
    level = monster.get("level", 1)
    rarity = monster.get("rarity", "common")
    # Базовый объём по уровню
    base = (level - 1) // 2 + 1  # 1-2=1, 3-4=2, 5-6=3...
    base = min(base, 5)
    # Модификатор редкости
    rarity_mod = {"common": 0, "rare": 1, "uncommon": 1,
                  "epic": 2, "legendary": 3, "mythic": 4}.get(rarity, 0)
    return base + rarity_mod


def get_affinity_bonus(monster_mood: str, crystal_affinity: str) -> float:
    """Бонус/штраф к ATK от совместимости монстра и кристалла."""
    return EMOTION_AFFINITY_BONUS.get((monster_mood, crystal_affinity), 1.0)


# ── БД ────────────────────────────────────────────────────────────────────────

def _ensure_crystal_tables():
    with get_connection() as conn:
        conn.execute("""
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
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Таблица связи монстр-кристалл
        conn.execute("""
            CREATE TABLE IF NOT EXISTS monster_crystal_bond (
                monster_id    INTEGER NOT NULL,
                crystal_id    INTEGER NOT NULL,
                battles       INTEGER NOT NULL DEFAULT 0,
                bond_level    INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (monster_id, crystal_id)
            )
        """)
        # Добавляем crystal_id в player_monsters если нет
        cols = [r[1] for r in conn.execute("PRAGMA table_info(player_monsters)").fetchall()]
        if "crystal_id" not in cols:
            conn.execute("ALTER TABLE player_monsters ADD COLUMN crystal_id INTEGER DEFAULT NULL")
        if "storage_volume" not in cols:
            conn.execute("ALTER TABLE player_monsters ADD COLUMN storage_volume INTEGER NOT NULL DEFAULT 1")
        if "is_summoned" not in cols:
            conn.execute("ALTER TABLE player_monsters ADD COLUMN is_summoned INTEGER NOT NULL DEFAULT 0")
        # Лог операций
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crystal_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER NOT NULL,
                crystal_id   INTEGER,
                monster_id   INTEGER,
                action       TEXT NOT NULL,
                detail       TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


_crystal_tables_ok = False
def _lazy():
    global _crystal_tables_ok
    if not _crystal_tables_ok:
        _ensure_crystal_tables()
        _crystal_tables_ok = True


def _log(telegram_id: int, action: str, crystal_id=None, monster_id=None, detail=""):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO crystal_log (telegram_id, crystal_id, monster_id, action, detail) VALUES (?,?,?,?,?)",
                (telegram_id, crystal_id, monster_id, action, detail)
            )
            conn.commit()
    except Exception:
        pass


# ── Создание кристаллов ───────────────────────────────────────────────────────

def create_crystal(telegram_id: int, template_code: str) -> dict:
    """Создаёт кристалл игроку по шаблону."""
    _lazy()
    tmpl = CRYSTAL_TEMPLATES.get(template_code, CRYSTAL_TEMPLATES["simple_quartz"])
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO player_crystals
            (telegram_id, template_code, name, rarity, emotion_affinity,
             max_volume, max_monsters, current_volume, current_monsters)
            VALUES (?,?,?,?,?,?,?,0,0)
        """, (telegram_id, template_code, tmpl["name"], tmpl["rarity"],
              tmpl["emotion_affinity"], tmpl["max_volume"], tmpl["max_monsters"]))
        cid = cur.lastrowid
        conn.commit()
    _log(telegram_id, "crystal_created", crystal_id=cid, detail=template_code)
    return {**tmpl, "id": cid}


def ensure_starter_crystal(telegram_id: int) -> bool:
    """Выдаёт стартовый кристалл если нет ни одного. Возвращает True если создан."""
    _lazy()
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM player_crystals WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()[0]
    if count == 0:
        create_crystal(telegram_id, "simple_quartz")
        return True
    return False


# ── Получение данных ──────────────────────────────────────────────────────────

def get_player_crystals(telegram_id: int) -> list[dict]:
    """Список всех кристаллов игрока."""
    _lazy()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM player_crystals WHERE telegram_id=? ORDER BY id",
            (telegram_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_crystal(crystal_id: int) -> dict | None:
    _lazy()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM player_crystals WHERE id=?", (crystal_id,)).fetchone()
    return dict(row) if row else None


def get_monsters_in_crystal(crystal_id: int) -> list[dict]:
    """Монстры в конкретном кристалле."""
    _lazy()
    from database.db import json_get
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM player_monsters WHERE crystal_id=?",
            (crystal_id,)
        ).fetchall()
    result = []
    for row in rows:
        m = dict(row)
        m["abilities"] = json_get(m.get("abilities", "[]"))
        result.append(m)
    return result


def recalculate_crystal_load(crystal_id: int):
    """Пересчитывает текущую загрузку кристалла из реальных данных монстров."""
    _lazy()
    monsters = get_monsters_in_crystal(crystal_id)
    total_volume = sum(calculate_monster_volume(m) for m in monsters)
    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET current_volume=?, current_monsters=? WHERE id=?",
            (total_volume, len(monsters), crystal_id)
        )
        conn.commit()


# ── Размещение монстров ───────────────────────────────────────────────────────

def find_free_crystal(telegram_id: int, volume_needed: int) -> dict | None:
    """Находит первый кристалл с достаточным свободным объёмом."""
    _lazy()
    crystals = get_player_crystals(telegram_id)
    for c in crystals:
        if c["state"] != "normal":
            continue
        free_volume = c["max_volume"] - c["current_volume"]
        free_slots = c["max_monsters"] - c["current_monsters"]
        if free_volume >= volume_needed and free_slots > 0:
            return c
    return None


def store_monster_in_crystal(telegram_id: int, monster_id: int,
                              crystal_id: int) -> tuple[bool, str]:
    """Помещает монстра в кристалл."""
    _lazy()
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден."
    if crystal["state"] != "normal":
        return False, f"Кристалл недоступен: {crystal['state']}"

    from database.db import json_get
    with get_connection() as conn:
        mrow = conn.execute(
            "SELECT * FROM player_monsters WHERE id=? AND telegram_id=?",
            (monster_id, telegram_id)
        ).fetchone()
    if not mrow:
        return False, "Монстр не найден."

    monster = dict(mrow)
    volume = calculate_monster_volume(monster)
    free_v = crystal["max_volume"] - crystal["current_volume"]
    free_s = crystal["max_monsters"] - crystal["current_monsters"]

    if free_v < volume:
        return False, f"Недостаточно объёма в кристалле ({volume} нужно, {free_v} свободно)."
    if free_s < 1:
        return False, f"Кристалл полон ({crystal['max_monsters']}/{crystal['max_monsters']} монстров)."

    with get_connection() as conn:
        conn.execute(
            "UPDATE player_monsters SET crystal_id=?, storage_volume=?, is_summoned=0 WHERE id=?",
            (crystal_id, volume, monster_id)
        )
        conn.execute(
            "UPDATE player_crystals SET current_volume=current_volume+?, current_monsters=current_monsters+1 WHERE id=?",
            (volume, crystal_id)
        )
        conn.commit()

    _log(telegram_id, "store", crystal_id, monster_id, f"volume={volume}")
    return True, f"✅ {monster['name']} помещён в {crystal['name']}."


def auto_store_new_monster(telegram_id: int, monster_id: int) -> tuple[bool, str]:
    """Автоматически находит кристалл и помещает монстра."""
    _lazy()
    from database.db import json_get
    with get_connection() as conn:
        mrow = conn.execute(
            "SELECT * FROM player_monsters WHERE id=? AND telegram_id=?",
            (monster_id, telegram_id)
        ).fetchone()
    if not mrow:
        return False, "Монстр не найден."
    volume = calculate_monster_volume(dict(mrow))
    crystal = find_free_crystal(telegram_id, volume)
    if not crystal:
        _log(telegram_id, "failed_store_no_crystal", monster_id=monster_id)
        return False, (
            f"❌ Нет подходящего кристалла для {mrow['name']}!\n"
            f"Нужно: {volume} ед. объёма.\n"
            f"Купи кристалл у торговца или освободи место."
        )
    return store_monster_in_crystal(telegram_id, monster_id, crystal["id"])


# ── Призыв/возврат ────────────────────────────────────────────────────────────

def get_summoned_monster(telegram_id: int) -> dict | None:
    """Возвращает текущего призванного монстра или None."""
    _lazy()
    from database.db import json_get
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_monsters WHERE telegram_id=? AND is_summoned=1 LIMIT 1",
            (telegram_id,)
        ).fetchone()
    if not row:
        return None
    m = dict(row)
    m["abilities"] = json_get(m.get("abilities", "[]"))
    return m


def summon_monster(telegram_id: int, monster_id: int) -> tuple[bool, str]:
    """Призывает монстра из кристалла для боя."""
    _lazy()
    # Снимаем текущий призыв если есть
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id FROM player_monsters WHERE telegram_id=? AND is_summoned=1",
            (telegram_id,)
        ).fetchone()
        if cur:
            conn.execute("UPDATE player_monsters SET is_summoned=0 WHERE id=?", (cur["id"],))
        # Призываем нового
        mrow = conn.execute(
            "SELECT * FROM player_monsters WHERE id=? AND telegram_id=?",
            (monster_id, telegram_id)
        ).fetchone()
        if not mrow:
            conn.commit()
            return False, "Монстр не найден."
        if mrow["is_dead"]:
            conn.commit()
            return False, "Этот монстр пал — возроди его сначала."
        conn.execute(
            "UPDATE player_monsters SET is_summoned=1, is_active=1 WHERE id=?",
            (monster_id,)
        )
        # Обновляем предыдущего активного
        conn.execute(
            "UPDATE player_monsters SET is_active=0 WHERE telegram_id=? AND id!=?",
            (telegram_id, monster_id)
        )
        conn.commit()
    _log(telegram_id, "summon", monster_id=monster_id)
    monster_name = mrow["name"]
    return True, f"✨ {monster_name} призван и готов к бою!"


def return_summoned_monster(telegram_id: int, heal_in_home_crystal: bool = True):
    """Возвращает призванного монстра обратно в кристалл после боя."""
    _lazy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM player_monsters WHERE telegram_id=? AND is_summoned=1",
            (telegram_id,)
        ).fetchone()
        if not row:
            return
        monster_id = row["id"]
        crystal_id = row["crystal_id"]

        # Регенерация HP в "домашнем" кристалле
        if heal_in_home_crystal and crystal_id and row["current_hp"] > 0:
            heal = max(1, int(row["max_hp"] * HOME_CRYSTAL_REGEN_PCT))
            new_hp = min(row["max_hp"], row["current_hp"] + heal)
            conn.execute(
                "UPDATE player_monsters SET is_summoned=0, current_hp=? WHERE id=?",
                (new_hp, monster_id)
            )
        else:
            conn.execute(
                "UPDATE player_monsters SET is_summoned=0 WHERE id=?",
                (monster_id,)
            )
        conn.commit()
    _log(telegram_id, "return", monster_id=monster_id)


# ── Миграция существующих игроков ─────────────────────────────────────────────

def migrate_existing_players():
    """
    Миграция: раздаёт кристаллы всем игрокам у кого их нет,
    и помещает существующих монстров в кристаллы.
    Безопасно запускать многократно (идемпотентно).
    """
    _lazy()
    with get_connection() as conn:
        players = conn.execute("SELECT telegram_id FROM players").fetchall()

    migrated = 0
    for prow in players:
        uid = prow["telegram_id"]
        # Убеждаемся что есть кристаллы
        ensure_starter_crystal(uid)

        # Находим монстров без crystal_id
        with get_connection() as conn:
            orphans = conn.execute(
                "SELECT * FROM player_monsters WHERE telegram_id=? AND (crystal_id IS NULL OR crystal_id=0)",
                (uid,)
            ).fetchall()

        for m in orphans:
            monster = dict(m)
            volume = calculate_monster_volume(monster)
            crystal = find_free_crystal(uid, volume)
            if not crystal:
                # Создаём дополнительный кристалл
                create_crystal(uid, "simple_quartz")
                crystal = find_free_crystal(uid, volume)
            if crystal:
                store_monster_in_crystal(uid, monster["id"], crystal["id"])
                migrated += 1

    return migrated


# ── Отображение ───────────────────────────────────────────────────────────────

def get_combat_modifiers(telegram_id: int, monster_id: int) -> dict:
    """
    Возвращает все боевые модификаторы от кристалла для монстра.
    Вызывается перед боем.
    """
    _lazy()
    with get_connection() as conn:
        mrow = conn.execute(
            "SELECT * FROM player_monsters WHERE id=? AND telegram_id=?",
            (monster_id, telegram_id)
        ).fetchone()
    if not mrow:
        return {"atk_multiplier": 1.0, "note": ""}

    crystal_id = mrow["crystal_id"] if mrow else None
    monster_mood = mrow["mood"] if mrow else "instinct"

    # Нет кристалла — нестабильность
    if not crystal_id:
        return {
            "atk_multiplier": 1 - UNSTABLE_ATK_PENALTY,
            "note": f"⚠️ Нестабильность (-{int(UNSTABLE_ATK_PENALTY*100)}% ATK): монстр без кристалла",
        }

    crystal = get_crystal(crystal_id)
    if not crystal:
        return {"atk_multiplier": 1 - UNSTABLE_ATK_PENALTY, "note": "⚠️ Кристалл потерян"}

    multiplier = 1.0
    notes = []

    # 1. Эмоциональная совместимость
    affinity_bonus = get_affinity_bonus(monster_mood, crystal["emotion_affinity"])
    if affinity_bonus != 1.0:
        diff = int((affinity_bonus - 1.0) * 100)
        sign = "+" if diff > 0 else ""
        notes.append(f"💎 Совместимость: {sign}{diff}% ATK")
    multiplier *= affinity_bonus

    # 2. Бонус связи (bond level)
    with get_connection() as conn:
        bond = conn.execute(
            "SELECT bond_level, battles FROM monster_crystal_bond WHERE monster_id=? AND crystal_id=?",
            (monster_id, crystal_id)
        ).fetchone()
    if bond and bond["bond_level"] > 0:
        bond_bonus = bond["bond_level"] * BOND_ATK_BONUS
        multiplier *= (1 + bond_bonus)
        notes.append(f"🔗 Связь ур.{bond['bond_level']}: +{int(bond_bonus*100)}% ATK")

    # 3. Штраф трещин
    crack = crystal.get("crack_count", 0)
    state = crystal.get("state", "normal")
    if state == "cracked":
        multiplier *= (1 - CRACK_ATK_PENALTY)
        notes.append(f"⚠️ Трещина: -{int(CRACK_ATK_PENALTY*100)}% ATK")
    elif state == "broken":
        multiplier *= 0.5
        notes.append("💔 Кристалл разбит: -50% ATK! Нужен ремонт.")

    return {
        "atk_multiplier": round(multiplier, 2),
        "note": " | ".join(notes),
    }


def record_battle_result(telegram_id: int, monster_id: int, victory: bool):
    """
    Записывает результат боя — обновляет связь и трещины кристалла.
    Вызывается после каждого боя.
    """
    _lazy()
    with get_connection() as conn:
        mrow = conn.execute(
            "SELECT crystal_id FROM player_monsters WHERE id=? AND telegram_id=?",
            (monster_id, telegram_id)
        ).fetchone()
    if not mrow or not mrow["crystal_id"]:
        return

    crystal_id = mrow["crystal_id"]

    with get_connection() as conn:
        # Обновляем bond
        conn.execute("""
            INSERT INTO monster_crystal_bond (monster_id, crystal_id, battles, bond_level)
            VALUES (?, ?, 1, 0)
            ON CONFLICT(monster_id, crystal_id) DO UPDATE SET battles = battles + 1
        """, (monster_id, crystal_id))

        # Повышаем уровень связи если порог достигнут
        bond = conn.execute(
            "SELECT battles, bond_level FROM monster_crystal_bond WHERE monster_id=? AND crystal_id=?",
            (monster_id, crystal_id)
        ).fetchone()
        if bond:
            new_level = min(BOND_MAX_LEVEL, bond["battles"] // BOND_BATTLES_PER_LEVEL)
            if new_level > bond["bond_level"]:
                conn.execute(
                    "UPDATE monster_crystal_bond SET bond_level=? WHERE monster_id=? AND crystal_id=?",
                    (new_level, monster_id, crystal_id)
                )

        # Трещины при поражении
        if not victory:
            conn.execute(
                "UPDATE player_crystals SET crack_count=crack_count+1 WHERE id=?",
                (crystal_id,)
            )
            crystal = conn.execute(
                "SELECT crack_count FROM player_crystals WHERE id=?",
                (crystal_id,)
            ).fetchone()
            if crystal:
                cracks = crystal["crack_count"]
                new_state = "normal"
                if cracks >= CRACK_THRESHOLD_BROKEN:
                    new_state = "broken"
                elif cracks >= CRACK_THRESHOLD_CRACKED:
                    new_state = "cracked"
                conn.execute(
                    "UPDATE player_crystals SET state=? WHERE id=?",
                    (new_state, crystal_id)
                )

        # Обновляем battle_count кристалла
        conn.execute(
            "UPDATE player_crystals SET battle_count=battle_count+1 WHERE id=?",
            (crystal_id,)
        )
        conn.commit()


def repair_crystal(telegram_id: int, crystal_id: int, gold: int) -> tuple[bool, str, int]:
    """Ремонт треснутого/разбитого кристалла."""
    _lazy()
    crystal = get_crystal(crystal_id)
    if not crystal or crystal["telegram_id"] != telegram_id:
        return False, "Кристалл не найден.", gold
    if crystal["state"] == "normal":
        return False, "Кристалл в порядке, ремонт не нужен.", gold

    # Стоимость ремонта зависит от редкости
    repair_costs = {"common": 40, "uncommon": 80, "rare": 150}
    cost = repair_costs.get(crystal["rarity"], 60)
    if crystal["state"] == "broken":
        cost *= 2

    if gold < cost:
        return False, f"Нужно {cost}з для ремонта. У тебя {gold}з", gold

    with get_connection() as conn:
        conn.execute(
            "UPDATE player_crystals SET state='normal', crack_count=0 WHERE id=?",
            (crystal_id,)
        )
        conn.commit()
    return True, f"✅ {crystal['name']} восстановлен!", gold - cost


def get_bond_level(monster_id: int, crystal_id: int) -> int:
    """Уровень связи монстра с кристаллом (0-5)."""
    _lazy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT bond_level FROM monster_crystal_bond WHERE monster_id=? AND crystal_id=?",
            (monster_id, crystal_id)
        ).fetchone()
    return row["bond_level"] if row else 0


def render_crystal_list(telegram_id: int) -> str:
    """Список кристаллов игрока."""
    crystals = get_player_crystals(telegram_id)
    if not crystals:
        return "У тебя нет кристаллов. Купи у торговца!"

    lines = ["💎 Твои кристаллы\n"]
    for c in crystals:
        vol_bar = "█" * int(c["current_volume"] / max(1, c["max_volume"]) * 10)
        vol_bar += "░" * (10 - len(vol_bar))
        state_icon = {"normal": "✅", "cracked": "⚠️", "overloaded": "❌"}.get(c["state"], "❓")
        lines.append(
            f"{state_icon} {c['name']}\n"
            f"  Объём: [{vol_bar}] {c['current_volume']}/{c['max_volume']}\n"
            f"  Монстры: {c['current_monsters']}/{c['max_monsters']}"
        )
    return "\n\n".join(lines)


def render_crystal_detail(crystal_id: int) -> str:
    """Детальный вид одного кристалла."""
    crystal = get_crystal(crystal_id)
    if not crystal:
        return "Кристалл не найден."
    monsters = get_monsters_in_crystal(crystal_id)
    tmpl = CRYSTAL_TEMPLATES.get(crystal["template_code"], {})

    lines = [
        f"{crystal['name']}",
        f"Редкость: {crystal['rarity']} | Аффинность: {crystal['emotion_affinity']}",
        f"Объём: {crystal['current_volume']}/{crystal['max_volume']}",
        f"Монстров: {crystal['current_monsters']}/{crystal['max_monsters']}",
        f"Состояние: {crystal['state']}",
    ]
    if tmpl.get("desc"):
        lines.append(f"📋 {tmpl['desc']}")

    if monsters:
        lines.append("\n🐲 Монстры внутри:")
        for m in monsters:
            summoned = " ⚡призван" if m.get("is_summoned") else ""
            dead = " 💀мёртв" if m.get("is_dead") else ""
            lines.append(
                f"  • {m['name']} ур.{m['level']} "
                f"HP:{m['current_hp']}/{m['max_hp']}{summoned}{dead}"
            )
    else:
        lines.append("\n(пусто)")
    return "\n".join(lines)
