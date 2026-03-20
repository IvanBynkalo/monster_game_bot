"""
hunting_quests.py — Квесты на охоту (убийство зверей).
Три типа: дневные, гильдейские, особые.
"""
import random
from database.repositories import get_connection

# ── Определения квестов ───────────────────────────────────────────────────────

DAILY_HUNTING_QUESTS = [
    {"id": "hunt_fox_3",     "title": "🦊 Охота на лисиц",      "target": "Лесная лисица",  "count": 3,  "reward_gold": 30,  "reward_exp": 15},
    {"id": "hunt_wolf_2",    "title": "🐺 Волчья охота",         "target": "Волк",           "count": 2,  "reward_gold": 40,  "reward_exp": 20},
    {"id": "hunt_rabbit_5",  "title": "🐰 Заяц на ужин",         "target": "Дикий заяц",     "count": 5,  "reward_gold": 25,  "reward_exp": 12},
    {"id": "hunt_boar_2",    "title": "🐗 Кабаний клык",         "target": "Дикий кабан",    "count": 2,  "reward_gold": 45,  "reward_exp": 22},
    {"id": "hunt_frog_4",    "title": "🐸 Болотная слизь",       "target": "Болотная жаба",  "count": 4,  "reward_gold": 28,  "reward_exp": 14},
    {"id": "hunt_snake_3",   "title": "🐍 Змеиный яд",           "target": "Уж",             "count": 3,  "reward_gold": 50,  "reward_exp": 25},
    {"id": "hunt_goat_3",    "title": "🐐 Горные козлы",         "target": "Горный козёл",   "count": 3,  "reward_gold": 35,  "reward_exp": 18},
    {"id": "hunt_lizard_2",  "title": "🦎 Огненная кожа",        "target": "Огненная ящерица","count": 2, "reward_gold": 60,  "reward_exp": 30},
]

GUILD_HUNTING_QUESTS = [
    {"id": "ghunt_wolf_5",      "title": "🐺 Зачистка волков",    "target": "Матёрый волк",      "count": 5,  "reward_gold": 120, "reward_exp": 60,  "min_level": 3},
    {"id": "ghunt_bear_3",      "title": "🐻 Медвежий трофей",    "target": "Медведь",           "count": 3,  "reward_gold": 150, "reward_exp": 75,  "min_level": 4},
    {"id": "ghunt_deer_4",      "title": "🦌 Оленьи рога",        "target": "Молодой олень",     "count": 4,  "reward_gold": 100, "reward_exp": 50,  "min_level": 2},
    {"id": "ghunt_croc_2",      "title": "🐊 Охота на крокодилов","target": "Болотный крокодил", "count": 2,  "reward_gold": 180, "reward_exp": 90,  "min_level": 5},
    {"id": "ghunt_lion_1",      "title": "🦁 Горный лев",         "target": "Горный лев",        "count": 1,  "reward_gold": 200, "reward_exp": 100, "min_level": 6},
    {"id": "ghunt_eagle_2",     "title": "🪶 Золотые перья",      "target": "Золотой орёл",      "count": 2,  "reward_gold": 160, "reward_exp": 80,  "min_level": 5},
    {"id": "ghunt_magma_1",     "title": "🌋 Магматический кабан","target": "Магматический кабан","count": 1, "reward_gold": 250, "reward_exp": 125, "min_level": 8},
    {"id": "ghunt_giant_1",     "title": "🌲 Лесной великан",     "target": "Лесной великан",    "count": 1,  "reward_gold": 220, "reward_exp": 110, "min_level": 7},
]

SPECIAL_HUNTING_QUESTS = [
    {
        "id": "special_rare_trophies",
        "title": "🏆 Редкие трофеи",
        "description": "Добудь 2 трофея с редких зверей",
        "type": "trophy",
        "count": 2,
        "reward_gold": 300,
        "reward_exp": 150,
        "reward_item": "crystal_focus",
        "min_level": 5,
    },
    {
        "id": "special_variety",
        "title": "🗺 Охотник-следопыт",
        "description": "Убей зверей из 3 разных локаций",
        "type": "variety",
        "count": 3,
        "reward_gold": 200,
        "reward_exp": 100,
        "min_level": 3,
    },
]


# ── БД ────────────────────────────────────────────────────────────────────────

def _ensure_hunting_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_hunting_quests (
                telegram_id  INTEGER NOT NULL,
                quest_id     TEXT    NOT NULL,
                progress     INTEGER NOT NULL DEFAULT 0,
                completed    INTEGER NOT NULL DEFAULT 0,
                assigned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, quest_id)
            )
        """)
        conn.commit()


_hunting_table_ok = False
def _lazy():
    global _hunting_table_ok
    if not _hunting_table_ok:
        _ensure_hunting_table()
        _hunting_table_ok = True


def assign_daily_hunting_quest(telegram_id: int) -> dict | None:
    """Выдаёт случайный дневной квест на охоту если нет активного."""
    _lazy()
    with get_connection() as conn:
        # Есть ли незавершённый дневной?
        active = conn.execute("""
            SELECT quest_id FROM player_hunting_quests
            WHERE telegram_id=? AND completed=0
            AND quest_id LIKE 'hunt_%'
        """, (telegram_id,)).fetchone()
        if active:
            return None
        quest = random.choice(DAILY_HUNTING_QUESTS)
        conn.execute("""
            INSERT OR IGNORE INTO player_hunting_quests (telegram_id, quest_id, progress)
            VALUES (?,?,0)
        """, (telegram_id, quest["id"]))
        conn.commit()
    return quest


def get_active_hunting_quests(telegram_id: int) -> list[dict]:
    """Возвращает все активные квесты охоты."""
    _lazy()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT quest_id, progress FROM player_hunting_quests
            WHERE telegram_id=? AND completed=0
        """, (telegram_id,)).fetchall()

    result = []
    all_quests = DAILY_HUNTING_QUESTS + GUILD_HUNTING_QUESTS + SPECIAL_HUNTING_QUESTS
    quest_map = {q["id"]: q for q in all_quests}
    for row in rows:
        q = quest_map.get(row["quest_id"])
        if q:
            result.append({**q, "progress": row["progress"]})
    return result


def progress_hunting_kill(telegram_id: int, animal_name: str) -> list[dict]:
    """
    Засчитывает убийство зверя в квесты охоты.
    Возвращает список завершённых квестов.
    """
    _lazy()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT quest_id, progress FROM player_hunting_quests
            WHERE telegram_id=? AND completed=0
        """, (telegram_id,)).fetchall()

    all_quests = DAILY_HUNTING_QUESTS + GUILD_HUNTING_QUESTS
    quest_map = {q["id"]: q for q in all_quests}
    completed = []

    with get_connection() as conn:
        for row in rows:
            q = quest_map.get(row["quest_id"])
            if not q:
                continue
            if q.get("target") != animal_name:
                continue
            new_progress = row["progress"] + 1
            if new_progress >= q["count"]:
                conn.execute("""
                    UPDATE player_hunting_quests SET progress=?, completed=1
                    WHERE telegram_id=? AND quest_id=?
                """, (new_progress, telegram_id, row["quest_id"]))
                completed.append(q)
            else:
                conn.execute("""
                    UPDATE player_hunting_quests SET progress=?
                    WHERE telegram_id=? AND quest_id=?
                """, (new_progress, telegram_id, row["quest_id"]))
        conn.commit()
    return completed


def claim_hunting_reward(telegram_id: int, quest_id: str) -> dict | None:
    """Забрать награду за выполненный квест."""
    _lazy()
    all_quests = DAILY_HUNTING_QUESTS + GUILD_HUNTING_QUESTS + SPECIAL_HUNTING_QUESTS
    q = next((x for x in all_quests if x["id"] == quest_id), None)
    if not q:
        return None
    with get_connection() as conn:
        row = conn.execute("""
            SELECT completed FROM player_hunting_quests
            WHERE telegram_id=? AND quest_id=? AND completed=1
        """, (telegram_id, quest_id)).fetchone()
        if not row:
            return None
        conn.execute("DELETE FROM player_hunting_quests WHERE telegram_id=? AND quest_id=?",
                     (telegram_id, quest_id))
        conn.commit()
    return q
