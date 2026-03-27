"""
guild_quests.py — Полноценная система гильдейских поручений.

Механика:
- 3 уровня поручений у каждой гильдии (растут с уровнем профессии)
- Еженедельные особые поручения
- Взять → выполнить → сдать
- Награда: золото + опыт + очко навыка профессии
- Новые поручения после сдачи + при росте уровня профессии
"""

# ── Поручения по профессиям и уровням ────────────────────────────────────────

GUILD_QUEST_POOL = {
    "hunter": [
        # Уровень 1
        {"id": "h_capture_1", "min_level": 1, "max_level": 3,
         "title": "Первая поимка", "desc": "Поймай 1 монстра в любой локации.",
         "type": "capture", "target": 1,
         "reward_gold": 30, "reward_exp": 12, "reward_skill": 1},
        {"id": "h_capture_2", "min_level": 1, "max_level": 3,
         "title": "Охотник начинает", "desc": "Поймай 2 монстра.",
         "type": "capture", "target": 2,
         "reward_gold": 45, "reward_exp": 18, "reward_skill": 1},
        {"id": "h_kill_1", "min_level": 1, "max_level": 3,
         "title": "Зверобой", "desc": "Убей 3 зверя в любой локации.",
         "type": "kill_wildlife", "target": 3,
         "reward_gold": 35, "reward_exp": 14, "reward_skill": 1},
        # Уровень 4+
        {"id": "h_capture_3", "min_level": 4, "max_level": 7,
         "title": "Опытный ловец", "desc": "Поймай 3 монстра разных типов.",
         "type": "capture", "target": 3,
         "reward_gold": 80, "reward_exp": 35, "reward_skill": 2},
        {"id": "h_rare_1", "min_level": 4, "max_level": 7,
         "title": "Охота на редкость", "desc": "Поймай монстра редкости Редкий или выше.",
         "type": "capture_rare", "target": 1,
         "reward_gold": 120, "reward_exp": 50, "reward_skill": 2},
        {"id": "h_kill_2", "min_level": 4, "max_level": 7,
         "title": "Зачистка территории", "desc": "Убей 5 зверей в Тёмном лесу.",
         "type": "kill_wildlife_loc", "target": 5, "location": "dark_forest",
         "reward_gold": 90, "reward_exp": 40, "reward_skill": 2},
        # Уровень 8+
        {"id": "h_capture_4", "min_level": 8, "max_level": 99,
         "title": "Мастер поимки", "desc": "Поймай 5 монстров за одну сессию.",
         "type": "capture", "target": 5,
         "reward_gold": 200, "reward_exp": 90, "reward_skill": 3},
        {"id": "h_epic_1", "min_level": 8, "max_level": 99,
         "title": "Эпическая охота", "desc": "Поймай Эпического монстра.",
         "type": "capture_rarity_exact", "target": 1, "rarity": "epic",
         "reward_gold": 300, "reward_exp": 150, "reward_skill": 3},
    ],

    "gatherer": [
        {"id": "g_gather_1", "min_level": 1, "max_level": 3,
         "title": "Первый сбор", "desc": "Собери 4 любых ресурса.",
         "type": "gather", "target": 4,
         "reward_gold": 30, "reward_exp": 12, "reward_skill": 1},
        {"id": "g_herb_1", "min_level": 1, "max_level": 3,
         "title": "Травяная корзина", "desc": "Собери 3 Лесную траву.",
         "type": "gather_resource", "target": 3, "resource": "forest_herb",
         "reward_gold": 35, "reward_exp": 14, "reward_skill": 1},
        {"id": "g_gather_2", "min_level": 4, "max_level": 7,
         "title": "Усердный собиратель", "desc": "Собери 8 ресурсов.",
         "type": "gather", "target": 8,
         "reward_gold": 70, "reward_exp": 30, "reward_skill": 2},
        {"id": "g_rare_1", "min_level": 4, "max_level": 7,
         "title": "Редкая находка", "desc": "Собери 2 редких ресурса.",
         "type": "gather_rare", "target": 2,
         "reward_gold": 100, "reward_exp": 45, "reward_skill": 2},
        {"id": "g_gather_3", "min_level": 8, "max_level": 99,
         "title": "Мастер сбора", "desc": "Собери 15 ресурсов за неделю.",
         "type": "gather", "target": 15,
         "reward_gold": 180, "reward_exp": 80, "reward_skill": 3},
    ],

    "geologist": [
        {"id": "geo_mine_1", "min_level": 1, "max_level": 3,
         "title": "Первая руда", "desc": "Добудь 2 каменных ресурса.",
         "type": "gather_resource_type", "target": 2, "res_type": "stone",
         "reward_gold": 35, "reward_exp": 14, "reward_skill": 1},
        {"id": "geo_crystal_1", "min_level": 1, "max_level": 3,
         "title": "Кристальный ученик", "desc": "Собери 1 кристальный ресурс.",
         "type": "gather_resource_type", "target": 1, "res_type": "crystal",
         "reward_gold": 40, "reward_exp": 16, "reward_skill": 1},
        {"id": "geo_mine_2", "min_level": 4, "max_level": 7,
         "title": "Опытный шахтёр", "desc": "Добудь 5 каменных ресурсов.",
         "type": "gather_resource_type", "target": 5, "res_type": "stone",
         "reward_gold": 85, "reward_exp": 38, "reward_skill": 2},
        {"id": "geo_mine_3", "min_level": 8, "max_level": 99,
         "title": "Мастер горных недр", "desc": "Добудь 10 редких минералов.",
         "type": "gather_rare", "target": 10,
         "reward_gold": 200, "reward_exp": 90, "reward_skill": 3},
    ],

    "alchemist": [
        {"id": "alc_craft_1", "min_level": 1, "max_level": 3,
         "title": "Первый настой", "desc": "Создай 2 предмета в лаборатории.",
         "type": "craft_any", "target": 2,
         "reward_gold": 40, "reward_exp": 16, "reward_skill": 1},
        {"id": "alc_potion_1", "min_level": 1, "max_level": 3,
         "title": "Зелейник", "desc": "Создай 1 зелье лечения.",
         "type": "craft_type", "target": 1, "item_type": "potion",
         "reward_gold": 45, "reward_exp": 18, "reward_skill": 1},
        {"id": "alc_craft_2", "min_level": 4, "max_level": 7,
         "title": "Алхимик среднего звена", "desc": "Создай 5 предметов.",
         "type": "craft_any", "target": 5,
         "reward_gold": 90, "reward_exp": 40, "reward_skill": 2},
        {"id": "alc_elixir_1", "min_level": 4, "max_level": 7,
         "title": "Мастер эликсиров", "desc": "Создай 2 эликсира лугов.",
         "type": "craft_specific", "target": 2, "item_slug": "field_elixir",
         "reward_gold": 110, "reward_exp": 48, "reward_skill": 2},
        {"id": "alc_craft_3", "min_level": 8, "max_level": 99,
         "title": "Великий алхимик", "desc": "Создай 10 предметов разных видов.",
         "type": "craft_any", "target": 10,
         "reward_gold": 220, "reward_exp": 100, "reward_skill": 3},
    ],
}

# Еженедельные поручения (одно активное на каждую гильдию)
WEEKLY_GUILD_QUESTS = {
    "hunter": {
        "id": "wh_hunter", "title": "🌟 Недельная охота",
        "desc": "Поймай 10 монстров за неделю.",
        "type": "capture", "target": 10,
        "reward_gold": 300, "reward_exp": 150, "reward_skill": 5,
    },
    "gatherer": {
        "id": "wh_gatherer", "title": "🌟 Недельный сбор",
        "desc": "Собери 25 ресурсов за неделю.",
        "type": "gather", "target": 25,
        "reward_gold": 280, "reward_exp": 140, "reward_skill": 5,
    },
    "geologist": {
        "id": "wh_geologist", "title": "🌟 Недельная добыча",
        "desc": "Добудь 15 каменных ресурсов за неделю.",
        "type": "gather_resource_type", "target": 15, "res_type": "stone",
        "reward_gold": 280, "reward_exp": 140, "reward_skill": 5,
    },
    "alchemist": {
        "id": "wh_alchemist", "title": "🌟 Недельная алхимия",
        "desc": "Создай 12 предметов за неделю.",
        "type": "craft_any", "target": 12,
        "reward_gold": 300, "reward_exp": 150, "reward_skill": 5,
    },
}

PROFESSION_NAMES = {
    "hunter": ("hunter_level", "hunter_exp"),
    "gatherer": ("gatherer_level", "gatherer_exp"),
    "geologist": ("geologist_level", "geologist_exp"),
    "alchemist": ("alchemist_level", "alchemist_exp"),
}


# ── БД ────────────────────────────────────────────────────────────────────────

from database.repositories import get_connection


def _ensure_guild_quest_table():
    with get_connection() as conn:
        # Основная таблица активных/взятых квестов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_guild_quests (
                telegram_id  INTEGER NOT NULL,
                quest_id     TEXT    NOT NULL,
                guild_key    TEXT    NOT NULL DEFAULT '',
                action_type  TEXT    NOT NULL DEFAULT '',
                count        INTEGER NOT NULL DEFAULT 1,
                title        TEXT    NOT NULL DEFAULT '',
                reward_gold  INTEGER NOT NULL DEFAULT 0,
                reward_exp   INTEGER NOT NULL DEFAULT 0,
                reward_skill INTEGER NOT NULL DEFAULT 0,
                is_weekly    INTEGER NOT NULL DEFAULT 0,
                expires_at   INTEGER DEFAULT NULL,
                progress     INTEGER NOT NULL DEFAULT 0,
                completed    INTEGER NOT NULL DEFAULT 0,
                taken_at     INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                PRIMARY KEY (telegram_id, quest_id)
            )
        """)
        # История завершённых квестов — предотвращает повторное взятие до кулдауна
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_quest_completions (
                telegram_id   INTEGER NOT NULL,
                quest_id      TEXT    NOT NULL,
                guild_key     TEXT    NOT NULL DEFAULT '',
                is_weekly     INTEGER NOT NULL DEFAULT 0,
                completed_at  INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                PRIMARY KEY (telegram_id, quest_id)
            )
        """)
        # Добавляем недостающие колонки в старые таблицы (миграция)
        needed = {
            "guild_key":   "TEXT NOT NULL DEFAULT ''",
            "action_type": "TEXT NOT NULL DEFAULT ''",
            "count":       "INTEGER NOT NULL DEFAULT 1",
            "title":       "TEXT NOT NULL DEFAULT ''",
            "reward_gold": "INTEGER NOT NULL DEFAULT 0",
            "reward_exp":  "INTEGER NOT NULL DEFAULT 0",
            "reward_skill":"INTEGER NOT NULL DEFAULT 0",
            "is_weekly":   "INTEGER NOT NULL DEFAULT 0",
            "expires_at":  "INTEGER DEFAULT NULL",
            "taken_at":    "INTEGER NOT NULL DEFAULT 0",
        }
        existing = [r[1] for r in conn.execute("PRAGMA table_info(player_guild_quests)").fetchall()]
        for col, definition in needed.items():
            if col not in existing:
                try:
                    conn.execute(f"ALTER TABLE player_guild_quests ADD COLUMN {col} {definition}")
                except Exception:
                    pass
        conn.commit()


_gq_ok = False
def _lazy():
    global _gq_ok
    if not _gq_ok:
        _ensure_guild_quest_table()
        _gq_ok = True


# ── Получение доступных квестов ───────────────────────────────────────────────

def get_available_quests(telegram_id: int, profession: str) -> list[dict]:
    """Квесты доступные для взятия (по уровню профессии, ещё не взятые и не в кулдауне)."""
    _lazy()
    from database.repositories import get_player
    player = get_player(telegram_id)
    if not player:
        return []

    level_field = PROFESSION_NAMES.get(profession, ("gatherer_level",))[0]
    prof_level = getattr(player, level_field, 1)

    import time
    now = int(time.time())

    # Активные квесты (взятые, не сданные)
    with get_connection() as conn:
        active_ids = {r["quest_id"] for r in conn.execute(
            "SELECT quest_id FROM player_guild_quests WHERE telegram_id=? AND guild_key=?",
            (telegram_id, profession)
        ).fetchall()}

    # Завершённые в кулдауне:
    # - обычные: 24 часа (нельзя взять ту же задачу снова сегодня)
    # - еженедельные: 7 дней
    with get_connection() as conn:
        cooldown_rows = conn.execute(
            "SELECT quest_id, is_weekly, completed_at FROM player_quest_completions "
            "WHERE telegram_id=? AND guild_key=?",
            (telegram_id, profession)
        ).fetchall()

    on_cooldown = set()
    for r in cooldown_rows:
        cooldown_secs = 7 * 86400 if r["is_weekly"] else 86400
        if now - r["completed_at"] < cooldown_secs:
            on_cooldown.add(r["quest_id"])

    pool = GUILD_QUEST_POOL.get(profession, [])
    available = [
        q for q in pool
        if q["id"] not in active_ids
        and q["id"] not in on_cooldown
        and q["min_level"] <= prof_level <= q["max_level"]
    ]
    return available[:3]


def get_active_quests(telegram_id: int, profession: str) -> list[dict]:
    """Активные квесты игрока в гильдии."""
    _lazy()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT quest_id, progress, completed, reward_gold, reward_exp,
                   reward_skill, title, count, is_weekly
            FROM player_guild_quests
            WHERE telegram_id=? AND guild_key=?
        """, (telegram_id, profession)).fetchall()

    result = []
    all_quests = GUILD_QUEST_POOL.get(profession, [])
    weekly = WEEKLY_GUILD_QUESTS.get(profession, {})
    quest_map = {q["id"]: q for q in all_quests}
    if weekly:
        quest_map[weekly["id"]] = weekly

    for row in rows:
        q = quest_map.get(row["quest_id"])
        if q:
            result.append({
                **q,
                "progress": row["progress"],
                "completed": row["completed"],
                "quest_id": row["quest_id"],
            })
    return result


def take_quest(telegram_id: int, quest_id: str, profession: str) -> tuple[bool, str]:
    """Берёт поручение."""
    _lazy()
    all_quests = GUILD_QUEST_POOL.get(profession, [])
    weekly = WEEKLY_GUILD_QUESTS.get(profession, {})
    quest = next((q for q in all_quests if q["id"] == quest_id), None)
    if not quest and weekly.get("id") == quest_id:
        quest = weekly

    if not quest:
        return False, "Поручение не найдено."

    import time
    now = int(time.time())
    is_weekly = quest["id"].startswith("wh_")

    with get_connection() as conn:
        # Проверяем: не взято ли уже
        exists = conn.execute(
            "SELECT quest_id FROM player_guild_quests WHERE telegram_id=? AND quest_id=?",
            (telegram_id, quest_id)
        ).fetchone()
        if exists:
            return False, "Ты уже взял это поручение."

        # Проверяем кулдаун после завершения
        hist = conn.execute(
            "SELECT completed_at, is_weekly FROM player_quest_completions "
            "WHERE telegram_id=? AND quest_id=?",
            (telegram_id, quest_id)
        ).fetchone()
        if hist:
            cooldown_secs = 7 * 86400 if hist["is_weekly"] else 86400
            elapsed = now - hist["completed_at"]
            if elapsed < cooldown_secs:
                remaining_h = (cooldown_secs - elapsed) // 3600
                remaining_m = ((cooldown_secs - elapsed) % 3600) // 60
                if remaining_h > 0:
                    return False, f"🕐 Это поручение снова доступно через {remaining_h} ч. {remaining_m} мин."
                return False, f"🕐 Это поручение снова доступно через {remaining_m} мин."

        expires = now + 7 * 86400 if is_weekly else None
        conn.execute("""
            INSERT INTO player_guild_quests
            (telegram_id, quest_id, guild_key, action_type, count, title,
             reward_gold, reward_exp, reward_skill, is_weekly, expires_at, progress, completed, taken_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,0,0,?)
        """, (
            telegram_id, quest_id, profession,
            quest.get("type", ""), quest.get("target", 1), quest["title"],
            quest["reward_gold"], quest["reward_exp"], quest.get("reward_skill", 1),
            1 if is_weekly else 0, expires, now
        ))
        conn.commit()
    return True, f"✅ Поручение взято: {quest['title']}"


def _quest_matches_extra(quest: dict, extra: dict | None) -> bool:
    extra = extra or {}
    qtype = quest.get("type")

    if qtype == "gather_resource":
        return extra.get("resource") == quest.get("resource")
    if qtype == "gather_resource_type":
        return extra.get("res_type") == quest.get("res_type")
    if qtype == "gather_rare":
        return bool(extra.get("rare"))
    if qtype == "craft_type":
        return extra.get("item_type") == quest.get("item_type")
    if qtype == "craft_specific":
        return extra.get("item_slug") == quest.get("item_slug")
    if qtype == "capture_rare":
        rarity = str(extra.get("rarity", "common"))
        order = {"common": 1, "rare": 2, "epic": 3, "legendary": 4, "mythic": 5}
        return order.get(rarity, 0) >= order.get("rare", 2)
    if qtype == "capture_rarity_exact":
        return extra.get("rarity") == quest.get("rarity")
    if qtype == "kill_wildlife_loc":
        return extra.get("location") == quest.get("location")
    return True


def progress_quest(telegram_id: int, profession: str, action_type: str,
                   amount: int = 1, extra: dict = None) -> list[dict]:
    """Обновляет прогресс квестов. Возвращает завершённые."""
    _lazy()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT quest_id, action_type, progress, count, title,
                   reward_gold, reward_exp, reward_skill
            FROM player_guild_quests
            WHERE telegram_id=? AND guild_key=? AND completed=0
        """, (telegram_id, profession)).fetchall()

    pool = {q["id"]: q for q in GUILD_QUEST_POOL.get(profession, [])}
    weekly = WEEKLY_GUILD_QUESTS.get(profession)
    if weekly:
        pool[weekly["id"]] = weekly

    completed = []
    for row in rows:
        quest = pool.get(row["quest_id"], {})
        if row["action_type"] != action_type:
            continue
        if not _quest_matches_extra(quest, extra):
            continue
        new_progress = row["progress"] + amount
        is_done = new_progress >= row["count"]
        with get_connection() as conn:
            conn.execute(
                "UPDATE player_guild_quests SET progress=?, completed=? WHERE telegram_id=? AND quest_id=?",
                (new_progress, int(is_done), telegram_id, row["quest_id"])
            )
            conn.commit()
        if is_done:
            payload = dict(row)
            payload.update(quest)
            payload["progress"] = new_progress
            payload["completed"] = 1
            completed.append(payload)
    return completed


def claim_quest(telegram_id: int, quest_id: str, profession: str) -> tuple[bool, str]:
    """Сдаёт выполненное поручение и выдаёт награду."""
    _lazy()
    import time

    with get_connection() as conn:
        row = conn.execute("""
            SELECT title, reward_gold, reward_exp, reward_skill, completed, is_weekly
            FROM player_guild_quests
            WHERE telegram_id=? AND quest_id=?
        """, (telegram_id, quest_id)).fetchone()

    if not row:
        return False, "Поручение не найдено."
    if not row["completed"]:
        return False, "Поручение ещё не выполнено."

    from database.repositories import (
        add_player_gold, add_player_experience, get_player, _update_player_field
    )
    add_player_gold(telegram_id, row["reward_gold"])
    add_player_experience(telegram_id, row["reward_exp"])

    # Очки навыка профессии
    skill_pts = row["reward_skill"]
    if skill_pts and profession in PROFESSION_NAMES:
        exp_field = PROFESSION_NAMES[profession][1]
        player = get_player(telegram_id)
        if player:
            cur_exp = getattr(player, exp_field, 0)
            _update_player_field(telegram_id, **{exp_field: cur_exp + skill_pts})

    now = int(time.time())
    is_weekly = bool(row["is_weekly"])

    with get_connection() as conn:
        # Удаляем из активных
        conn.execute(
            "DELETE FROM player_guild_quests WHERE telegram_id=? AND quest_id=?",
            (telegram_id, quest_id)
        )
        # Записываем в историю завершённых (кулдаун)
        conn.execute("""
            INSERT OR REPLACE INTO player_quest_completions
            (telegram_id, quest_id, guild_key, is_weekly, completed_at)
            VALUES (?,?,?,?,?)
        """, (telegram_id, quest_id, profession, 1 if is_weekly else 0, now))
        conn.commit()

    cooldown_str = "7 дней" if is_weekly else "24 часа"
    return True, (
        f"✅ Поручение сдано: {row['title']}\n"
        f"💰 +{row['reward_gold']} золота\n"
        f"✨ +{row['reward_exp']} опыта\n"
        f"📈 +{row['reward_skill']} опыта навыка «{profession}»\n"
        f"🕐 Повторно доступно через {cooldown_str}"
    )


# ── Отображение ───────────────────────────────────────────────────────────────

def render_guild_panel(telegram_id: int, profession: str,
                       guild_name: str, description: str) -> str:
    """Полная панель гильдии с квестами."""
    _lazy()
    import time
    now = int(time.time())

    active = get_active_quests(telegram_id, profession)
    available = get_available_quests(telegram_id, profession)
    weekly = WEEKLY_GUILD_QUESTS.get(profession, {})

    lines = [guild_name, "", description, ""]

    # Активные поручения
    if active:
        lines.append("📋 Твои активные поручения:")
        for q in active:
            prog = q.get("progress", 0)
            total = q.get("target", 1)
            pct = int(prog / max(1, total) * 10)
            bar = "█" * pct + "░" * (10 - pct)
            weekly_mark = " 🌟" if q.get("id", "").startswith("wh_") else ""
            if q.get("completed"):
                status = "✅ Готово к сдаче! Нажми кнопку ниже."
            else:
                status = f"[{bar}] {prog}/{total}"
            lines.append(f"• {q['title']}{weekly_mark}: {status}")
        lines.append("")

    # Доступные для взятия
    if available:
        lines.append("📌 Доступные поручения:")
        for q in available:
            reward_skill = q.get("reward_skill", 1)
            lines.append(
                f"• {q['title']}\n"
                f"  {q['desc']}\n"
                f"  💰{q['reward_gold']}з ✨{q['reward_exp']}оп 📈+{reward_skill} навык"
            )
        lines.append("")

    # Еженедельное
    weekly_active = next((q for q in active if q.get("id", "").startswith("wh_")), None)
    if weekly and not weekly_active:
        # Проверяем кулдаун на еженедельное
        with get_connection() as conn:
            hist = conn.execute(
                "SELECT completed_at FROM player_quest_completions "
                "WHERE telegram_id=? AND quest_id=?",
                (telegram_id, weekly["id"])
            ).fetchone()
        if hist and (now - hist["completed_at"]) < 7 * 86400:
            remaining = 7 * 86400 - (now - hist["completed_at"])
            days = remaining // 86400
            hours = (remaining % 86400) // 3600
            lines.append(f"🌟 Недельное: {weekly['title']} — 🕐 доступно через {days}д. {hours}ч.")
        else:
            lines.append(
                f"🌟 Недельное: {weekly['title']}\n"
                f"  {weekly['desc']}\n"
                f"  💰{weekly['reward_gold']}з ✨{weekly['reward_exp']}оп 📈+{weekly['reward_skill']} навык"
            )

    if not active and not available and not (weekly and not weekly_active):
        lines.append("Все поручения выполнены или недоступны. Возвращайся позже!")

    return "\n".join(lines)
