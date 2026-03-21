"""
roaming_monsters.py — Монстры-бродяги и Охота недели.

Монстры-бродяги:
- Раз в 2 часа редкий монстр "перемещается" между локациями
- Игрок при исследовании получает слух о бродяге
- Если игрок в той же локации — шанс встречи повышен

Охота недели:
- Каждую неделю выбирается один тип монстра/зверя
- Игроки получают очки за встречу/поимку/убийство
- Топ-охотники получают награды
"""
import random
import time
from database.repositories import get_connection

# ── Бродяги ───────────────────────────────────────────────────────────────────

ROAMING_MONSTERS = [
    {
        "id": "crimson_stalker",
        "name": "Багровый Следопыт",
        "emoji": "🔴",
        "rarity": "epic",
        "mood": "rage",
        "monster_type": "flame",
        "hp": 55, "attack": 14,
        "reward_gold": 120, "reward_exp": 60,
        "rumors": [
            "👁 Охотники из деревни говорят — ночью видели что-то красное между деревьями.",
            "🔥 На скалах нашли следы горения. Говорят, Багровый Следопыт снова здесь.",
            "💬 «Я слышал его рёв на рассвете» — сказал торговец, дрожа.",
        ],
    },
    {
        "id": "whispering_shard",
        "name": "Поющий Осколочник",
        "emoji": "🔵",
        "rarity": "epic",
        "mood": "sadness",
        "monster_type": "spirit",
        "hp": 42, "attack": 11,
        "reward_gold": 100, "reward_exp": 50,
        "rumors": [
            "🎵 В руинах слышна тихая мелодия. Местные не подходят туда после заката.",
            "💧 Путник рассказал: «Я видел синюю тень, она пела и растворилась в тумане».",
            "🌫 Следы на болоте ведут к центру трясины — и обрываются.",
        ],
    },
    {
        "id": "storm_phantom",
        "name": "Грозовой Фантом",
        "emoji": "⚡",
        "rarity": "legendary",
        "mood": "surprise",
        "monster_type": "storm",
        "hp": 70, "attack": 18,
        "reward_gold": 200, "reward_exp": 100,
        "rumors": [
            "⚡ Гром прогремел в ясном небе. Говорят — знак Грозового Фантома.",
            "🌩 Стадо оленей разбежалось без причины. Опытные охотники знают что это значит.",
            "🔔 Колокол в старой башне зазвонил сам по себе этой ночью.",
        ],
    },
    {
        "id": "bone_wanderer",
        "name": "Костяной Странник",
        "emoji": "💀",
        "rarity": "rare",
        "mood": "fear",
        "monster_type": "bone",
        "hp": 38, "attack": 12,
        "reward_gold": 90, "reward_exp": 45,
        "rumors": [
            "🦴 На дороге нашли чьи-то кости аккуратно сложены в круг. Недоброй знак.",
            "👻 Пастух видел белую фигуру на горизонте — она шла против ветра.",
            "🌙 В полнолуние из пустыни доносится скрежет — старики советуют не выходить.",
        ],
    },
]

ROAMING_LOCATIONS = [
    "dark_forest", "shadow_marsh", "shadow_swamp",
    "stone_hills", "ancient_ruins", "bone_desert",
    "volcano_wrath", "storm_ridge",
]


def _ensure_roaming_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS roaming_monsters (
                monster_id   TEXT PRIMARY KEY,
                location_slug TEXT NOT NULL,
                moved_at     INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weekly_hunt (
                week_key     TEXT PRIMARY KEY,
                target_id    TEXT NOT NULL,
                target_name  TEXT NOT NULL,
                started_at   INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weekly_hunt_scores (
                telegram_id  INTEGER NOT NULL,
                week_key     TEXT NOT NULL,
                kills        INTEGER NOT NULL DEFAULT 0,
                captures     INTEGER NOT NULL DEFAULT 0,
                score        INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (telegram_id, week_key)
            )
        """)
        conn.commit()


_roaming_ok = False
def _lazy():
    global _roaming_ok
    if not _roaming_ok:
        _ensure_roaming_tables()
        _roaming_ok = True


# ── Перемещение бродяг ────────────────────────────────────────────────────────

def _get_week_key() -> str:
    import datetime
    now = datetime.datetime.now()
    return f"{now.year}W{now.isocalendar()[1]}"


def update_roaming_positions():
    """Перемещает бродяг раз в 2 часа."""
    _lazy()
    now = int(time.time())
    with get_connection() as conn:
        for monster in ROAMING_MONSTERS:
            row = conn.execute(
                "SELECT location_slug, moved_at FROM roaming_monsters WHERE monster_id=?",
                (monster["id"],)
            ).fetchone()
            if not row or (now - row["moved_at"]) > 7200:  # 2 часа
                new_loc = random.choice(ROAMING_LOCATIONS)
                conn.execute("""
                    INSERT OR REPLACE INTO roaming_monsters (monster_id, location_slug, moved_at)
                    VALUES (?,?,?)
                """, (monster["id"], new_loc, now))
        conn.commit()


def get_roaming_in_location(location_slug: str) -> list[dict]:
    """Возвращает бродяг в данной локации."""
    _lazy()
    update_roaming_positions()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT monster_id FROM roaming_monsters WHERE location_slug=?",
            (location_slug,)
        ).fetchall()
    result = []
    monster_map = {m["id"]: m for m in ROAMING_MONSTERS}
    for row in rows:
        m = monster_map.get(row["monster_id"])
        if m:
            result.append(m)
    return result


def get_roaming_rumor(location_slug: str) -> str | None:
    """Возвращает слух о бродяге если он рядом (в соседней или текущей локации)."""
    _lazy()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT monster_id FROM roaming_monsters"
        ).fetchall()
    if not rows:
        return None
    # 30% шанс получить слух
    if random.random() > 0.30:
        return None
    monster_map = {m["id"]: m for m in ROAMING_MONSTERS}
    row = random.choice(rows)
    m = monster_map.get(row["monster_id"])
    if m and m.get("rumors"):
        return random.choice(m["rumors"])
    return None


def roll_roaming_encounter(location_slug: str) -> dict | None:
    """
    5% шанс встретить бродягу если он в этой локации.
    Возвращает encounter dict или None.
    """
    roaming = get_roaming_in_location(location_slug)
    if not roaming:
        return None
    if random.random() > 0.05:
        return None
    monster = random.choice(roaming)
    return {
        "type": "monster",
        "monster_name": monster["name"],
        "monster_type": monster["monster_type"],
        "rarity": monster["rarity"],
        "mood": monster["mood"],
        "hp": monster["hp"],
        "max_hp": monster["hp"],
        "attack": monster["attack"],
        "reward_gold": monster["reward_gold"],
        "reward_exp": monster["reward_exp"],
        "is_roaming": True,
        "roaming_id": monster["id"],
    }


# ── Охота недели ─────────────────────────────────────────────────────────────

HUNT_TARGETS = [
    {"id": "Лесная лисица",  "name": "Лесная лисица",  "emoji": "🦊", "type": "wildlife", "reward_gold": 150, "reward_exp": 75},
    {"id": "Матёрый волк",   "name": "Матёрый волк",   "emoji": "🐺", "type": "wildlife", "reward_gold": 200, "reward_exp": 100},
    {"id": "Болотный крокодил","name":"Болотный крокодил","emoji":"🐊","type":"wildlife", "reward_gold": 250, "reward_exp": 125},
    {"id": "Горный лев",     "name": "Горный лев",     "emoji": "🦁", "type": "wildlife", "reward_gold": 300, "reward_exp": 150},
    {"id": "Лавовый волк",   "name": "Лавовый волк",   "emoji": "🌋", "type": "wildlife", "reward_gold": 250, "reward_exp": 125},
]


def get_current_hunt() -> dict | None:
    """Возвращает текущую охоту недели."""
    _lazy()
    week = _get_week_key()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM weekly_hunt WHERE week_key=?", (week,)
        ).fetchone()
    if row:
        target = next((t for t in HUNT_TARGETS if t["id"] == row["target_id"]), None)
        return {**dict(row), "target": target} if target else None

    # Создаём охоту недели детерминированно по номеру недели
    import datetime
    week_num = datetime.datetime.now().isocalendar()[1]
    target = HUNT_TARGETS[week_num % len(HUNT_TARGETS)]
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO weekly_hunt (week_key, target_id, target_name, started_at)
            VALUES (?,?,?,?)
        """, (week, target["id"], target["name"], int(time.time())))
        conn.commit()
    return {"week_key": week, "target": target}


def record_hunt_kill(telegram_id: int, animal_name: str, captured: bool = False) -> dict | None:
    """Засчитывает убийство/поимку в охоту недели."""
    _lazy()
    hunt = get_current_hunt()
    if not hunt or not hunt.get("target"):
        return None
    if hunt["target"]["id"] != animal_name:
        return None
    week = hunt["week_key"]
    score = 3 if captured else 1
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO weekly_hunt_scores (telegram_id, week_key, kills, captures, score)
            VALUES (?,?,?,?,?)
            ON CONFLICT(telegram_id, week_key) DO UPDATE SET
                kills=kills+?, captures=captures+?, score=score+?
        """, (telegram_id, week,
              0 if captured else 1, 1 if captured else 0, score,
              0 if captured else 1, 1 if captured else 0, score))
        conn.commit()
    return {"target": hunt["target"], "score_added": score}


def get_hunt_leaderboard(limit: int = 10) -> list[dict]:
    """Топ охотников текущей недели."""
    _lazy()
    week = _get_week_key()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT s.telegram_id, s.kills, s.captures, s.score, p.name
            FROM weekly_hunt_scores s
            JOIN players p ON s.telegram_id = p.telegram_id
            WHERE s.week_key=?
            ORDER BY s.score DESC LIMIT ?
        """, (week, limit)).fetchall()
    return [dict(r) for r in rows]


def render_hunt_status(telegram_id: int) -> str:
    """Текст статуса охоты недели для игрока."""
    hunt = get_current_hunt()
    if not hunt or not hunt.get("target"):
        return "🎯 Охота недели недоступна."
    target = hunt["target"]
    week = hunt["week_key"]
    with get_connection() as conn:
        row = conn.execute(
            "SELECT kills, captures, score FROM weekly_hunt_scores WHERE telegram_id=? AND week_key=?",
            (telegram_id, week)
        ).fetchone()
    kills = row["kills"] if row else 0
    score = row["score"] if row else 0

    board = get_hunt_leaderboard(5)
    board_lines = []
    for i, p in enumerate(board, 1):
        mark = " ← ты" if p["telegram_id"] == telegram_id else ""
        board_lines.append(f"  {i}. {p['name']} — {p['score']} очков{mark}")

    return (
        f"🎯 Охота недели\n\n"
        f"Цель: {target['emoji']} {target['name']}\n"
        f"Твои убийства: {kills} | Очки: {score}\n"
        f"Награда лидера: {target['reward_gold']}з\n\n"
        f"🏆 Топ охотников:\n"
        + ("\n".join(board_lines) if board_lines else "  Никто ещё не охотился")
    )
