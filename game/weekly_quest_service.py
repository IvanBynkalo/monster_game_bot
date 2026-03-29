"""
weekly_quest_service.py — Сезонные/еженедельные квесты.

Механика:
- Для игрока с 100% исследования региона раз в неделю появляется мини-квест.
- Квест привязан к региону и неделе (ISO week number).
- Выполнение — через обычные игровые действия (убить N зверей, собрать ресурс).
- Награда: золото + реликвия / трофей / редкий ресурс.
- Запуск: автоматически при входе в регион с 100% и прошедшей неделей.

Как работает:
1. При переходе в локацию → check_weekly_quest(uid, location_slug)
2. Если 100% и неделя сменилась → выдаётся новый квест
3. Квест хранится в player_weekly_quests (telegram_id, week_key, location_slug, quest_slug, progress, completed)
4. Прогресс обновляется через progress_weekly_quest() при убийстве зверей / сборе
"""
import random
import datetime
from database.repositories import get_connection
from game.exploration_service import get_exploration

# ── Определения квестов по регионам ──────────────────────────────────────────

WEEKLY_QUESTS: dict[str, list[dict]] = {
    "dark_forest": [
        {"slug": "wq_forest_wolves",  "desc": "Победи 5 волков Тёмного леса",
         "action": "defeat_wildlife", "target_name": ["Лесной волк", "Матёрый волк"], "target": 5,
         "reward_gold": 120, "reward_item": "silver_moss", "reward_amount": 3},
        {"slug": "wq_forest_bear",    "desc": "Победи Бурого медведя 3 раза",
         "action": "defeat_wildlife", "target_name": ["Бурый медведь"], "target": 3,
         "reward_gold": 180, "reward_item": "forest_heart_relic", "reward_amount": 1},
        {"slug": "wq_forest_herbs",   "desc": "Собери 10 Лесных трав",
         "action": "gather", "resource": "forest_herb", "target": 10,
         "reward_gold": 90, "reward_item": "silver_moss", "reward_amount": 2},
    ],
    "emerald_fields": [
        {"slug": "wq_fields_deer",    "desc": "Победи 4 Рогатых оленя",
         "action": "defeat_wildlife", "target_name": ["Рогатый олень"], "target": 4,
         "reward_gold": 130, "reward_item": "dew_crystal", "reward_amount": 2},
        {"slug": "wq_fields_eagle",   "desc": "Встреть и победи Золотого орла",
         "action": "defeat_wildlife", "target_name": ["Золотой орёл"], "target": 1,
         "reward_gold": 250, "reward_item": "golden_eagle_feather", "reward_amount": 1},
        {"slug": "wq_fields_flowers", "desc": "Собери 8 Солнечных цветков",
         "action": "gather", "resource": "sun_blossom", "target": 8,
         "reward_gold": 100, "reward_item": "dew_crystal", "reward_amount": 1},
    ],
    "stone_hills": [
        {"slug": "wq_hills_boar",     "desc": "Победи 4 Скальных кабана",
         "action": "defeat_wildlife", "target_name": ["Скальный кабан"], "target": 4,
         "reward_gold": 140, "reward_item": "raw_ore", "reward_amount": 4},
        {"slug": "wq_hills_lion",     "desc": "Победи Горного льва",
         "action": "defeat_wildlife", "target_name": ["Горный лев"], "target": 1,
         "reward_gold": 280, "reward_item": "mountain_lion_fang", "reward_amount": 1},
        {"slug": "wq_hills_ore",      "desc": "Добудь 10 Сырой руды",
         "action": "gather", "resource": "raw_ore", "target": 10,
         "reward_gold": 110, "reward_item": "sky_crystal", "reward_amount": 1},
    ],
    "shadow_marsh": [
        {"slug": "wq_marsh_snake",    "desc": "Победи 5 Болотных змей",
         "action": "defeat_wildlife", "target_name": ["Болотная змея"], "target": 5,
         "reward_gold": 130, "reward_item": "dark_resin", "reward_amount": 3},
        {"slug": "wq_marsh_croc",     "desc": "Победи Болотного крокодила",
         "action": "defeat_wildlife", "target_name": ["Болотный крокодил"], "target": 1,
         "reward_gold": 270, "reward_item": "ghost_reed", "reward_amount": 2},
    ],
    "shadow_swamp": [
        {"slug": "wq_swamp_boar",     "desc": "Победи 4 Топяных кабана",
         "action": "defeat_wildlife", "target_name": ["Топяной кабан"], "target": 4,
         "reward_gold": 140, "reward_item": "toxic_spore", "reward_amount": 3},
        {"slug": "wq_swamp_croc",     "desc": "Победи Болотного крокодила 2 раза",
         "action": "defeat_wildlife", "target_name": ["Болотный крокодил"], "target": 2,
         "reward_gold": 300, "reward_item": "black_pearl", "reward_amount": 1},
    ],
    "volcano_wrath": [
        {"slug": "wq_volcano_wolf",   "desc": "Победи 4 Вулканических волка",
         "action": "defeat_wildlife", "target_name": ["Вулканический волк"], "target": 4,
         "reward_gold": 160, "reward_item": "ember_stone", "reward_amount": 4},
        {"slug": "wq_volcano_boar",   "desc": "Победи Магматического кабана",
         "action": "defeat_wildlife", "target_name": ["Магматический кабан"], "target": 1,
         "reward_gold": 320, "reward_item": "magma_tusk", "reward_amount": 1},
    ],
}

# Трофеи как предметы (добавим в relic_service)
TROPHY_ITEMS: dict[str, dict] = {
    "golden_eagle_feather": {"name": "🦅 Перо Золотого орла",     "desc": "+5% к опыту картографа"},
    "forest_giant_claw":    {"name": "🌲 Коготь лесного великана", "desc": "+3% шанс встретить монстра"},
    "magma_tusk":           {"name": "🔥 Клык магматического кабана","desc": "+10% к добыче вулканических ресурсов"},
    "swamp_croc_scale":     {"name": "🐊 Чешуя болотного крокодила","desc": "+8% защита от болотного урона"},
    "mountain_lion_fang":   {"name": "🦁 Клык горного льва",       "desc": "+5% к атаке в горных локациях"},
    "ancient_horn":         {"name": "🦬 Рог степного тура",       "desc": "+5% к поимке полевых существ"},
    "forest_heart_relic":   {"name": "🌿 Сердце леса",             "desc": "+10% к сбору лесных трав"},
}


def _week_key() -> str:
    now = datetime.datetime.utcnow()
    return f"{now.isocalendar()[0]}W{now.isocalendar()[1]:02d}"


# ── БД ────────────────────────────────────────────────────────────────────────

def get_active_weekly_quest(telegram_id: int, location_slug: str) -> dict | None:
    from game.exploration_service import _lazy_ensure
    _lazy_ensure()
    week = _week_key()
    with get_connection() as conn:
        row = conn.execute("""
            SELECT quest_slug, progress, completed
            FROM player_weekly_quests
            WHERE telegram_id=? AND location_slug=? AND week_key=?
        """, (telegram_id, location_slug, week)).fetchone()
    if not row:
        return None
    quest_def = _find_quest(row["quest_slug"])
    if not quest_def:
        return None
    return {**quest_def, "progress": row["progress"], "completed": bool(row["completed"])}


def _find_quest(slug: str) -> dict | None:
    for quests in WEEKLY_QUESTS.values():
        for q in quests:
            if q["slug"] == slug:
                return q.copy()
    return None


def check_and_assign_weekly_quest(telegram_id: int, location_slug: str) -> dict | None:
    """
    Вызывается при переходе в локацию.
    Выдаёт недельный квест при первом посещении локации (нет минимального порога).
    Возвращает квест если только что выдан, иначе None.
    """
    # Убрали ограничение 100% — квест доступен всем кто посетил локацию
    pass  # no minimum exploration required
    week = _week_key()
    # Проверяем нет ли уже квеста на эту неделю
    with get_connection() as conn:
        existing = conn.execute("""
            SELECT 1 FROM player_weekly_quests
            WHERE telegram_id=? AND location_slug=? AND week_key=?
        """, (telegram_id, location_slug, week)).fetchone()
    if existing:
        return None  # квест уже есть
    # Выдаём случайный квест для региона
    pool = WEEKLY_QUESTS.get(location_slug, [])
    if not pool:
        return None
    quest = random.choice(pool).copy()
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO player_weekly_quests
            (telegram_id, location_slug, week_key, quest_slug, progress, completed)
            VALUES (?,?,?,?,0,0)
        """, (telegram_id, location_slug, week, quest["slug"]))
        conn.commit()
    quest["progress"] = 0
    quest["completed"] = False
    return quest


def progress_weekly_quest(telegram_id: int, location_slug: str,
                           action: str, name: str | None = None,
                           resource: str | None = None, amount: int = 1) -> dict | None:
    """
    Обновляет прогресс еженедельного квеста.
    action: "defeat_wildlife" | "gather"
    name: имя зверя (для defeat_wildlife)
    resource: slug ресурса (для gather)
    Возвращает квест если выполнен только что.
    """
    quest = get_active_weekly_quest(telegram_id, location_slug)
    if not quest or quest["completed"]:
        return None
    if quest["action"] != action:
        return None
    # Проверяем подходит ли цель
    if action == "defeat_wildlife":
        if name not in quest.get("target_name", []):
            return None
    elif action == "gather":
        if resource != quest.get("resource"):
            return None

    week = _week_key()
    new_progress = quest["progress"] + amount
    completed = new_progress >= quest["target"]
    with get_connection() as conn:
        conn.execute("""
            UPDATE player_weekly_quests
            SET progress=?, completed=?
            WHERE telegram_id=? AND location_slug=? AND week_key=?
        """, (new_progress, int(completed), telegram_id, location_slug, week))
        conn.commit()

    if completed:
        return {**quest, "progress": new_progress, "completed": True}
    return None


def claim_weekly_reward(telegram_id: int, quest: dict) -> str:
    """Выдаёт награду за выполненный квест."""
    from database.repositories import add_player_gold, add_resource, add_item
    add_player_gold(telegram_id, quest["reward_gold"])
    reward_lines = [f"💰 +{quest['reward_gold']} золота"]

    item = quest.get("reward_item")
    amount = quest.get("reward_amount", 1)
    if item:
        if item in TROPHY_ITEMS:
            # Трофейный предмет — сохраняем как ресурс
            add_resource(telegram_id, item, amount)
            trophy_name = TROPHY_ITEMS[item]["name"]
            reward_lines.append(f"🏆 {trophy_name} x{amount}")
        else:
            add_resource(telegram_id, item, amount)
            reward_lines.append(f"🎁 {item} x{amount}")
    return "\n".join(reward_lines)


def render_weekly_quest(quest: dict | None) -> str:
    if not quest:
        return ""
    bar = f"{quest['progress']}/{quest['target']}"
    done = "✅" if quest["completed"] else f"[{bar}]"
    return (
        f"📅 Недельный квест:\n"
        f"{done} {quest['desc']}\n"
        f"Награда: {quest['reward_gold']}з + {quest.get('reward_item', '—')}"
    )
