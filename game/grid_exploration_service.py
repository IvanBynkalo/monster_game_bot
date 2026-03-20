"""
grid_exploration_service.py — Система исследования локаций на сетке 10×10.

Концепция:
- Каждая локация = сетка 10×10 = 100 клеток
- Игрок начинает с точки входа (5, 0) — центр-низ
- Каждая вылазка предлагает 3 направления: ↑ Вперёд, ↖ Влево, ↗ Вправо
- Игрок выбирает направление → открывает новую клетку
- Уже открытые клетки повторно не исследуются (нет смысла идти туда)
- % исследования = открытые клетки / 100 * 100

Клетки:
  normal      — обычное событие / бой
  gathering   — бонусные ресурсы (+50% к сбору)
  danger      — повышенная опасность (враги сильнее)
  discovery   — лор, тайник, артефакт
  dungeon     — вход в подземелье (открывается на 45%+)
  boss_zone   — территория мирового босса (открывается на 60%+)

Ключевые пороги:
  0%  — Точка входа
  30% — Редкие ресурсы начинают встречаться
  45% — Подземелье становится доступным
  60% — Территория боссов открыта
  85% — Мировой босс может появиться
  100% — Полное исследование, еженедельный квест
"""
import random
import json
from database.repositories import get_connection

# ── Типы клеток и их веса по зонам ───────────────────────────────────────────

CELL_TYPES = {
    "normal":    {"icon": "🌿", "name": "Обычная местность"},
    "gathering": {"icon": "🧺", "name": "Место сбора",      "gather_bonus": 0.5},
    "danger":    {"icon": "⚠️",  "name": "Опасная зона",     "enemy_bonus": 1.3},
    "discovery": {"icon": "✨", "name": "Находка"},
    "dungeon":   {"icon": "🕳", "name": "Вход в подземелье"},
    "boss_zone": {"icon": "💀", "name": "Территория босса"},
}

# Веса по глубине (row: 0=вход, 9=глубина)
ZONE_WEIGHTS = {
    "shallow": {"normal": 55, "gathering": 25, "danger": 15, "discovery": 5,  "dungeon": 0,  "boss_zone": 0},   # rows 0-2
    "mid":     {"normal": 40, "gathering": 20, "danger": 20, "discovery": 10, "dungeon": 8,  "boss_zone": 2},   # rows 3-5
    "deep":    {"normal": 30, "gathering": 15, "danger": 25, "discovery": 15, "dungeon": 10, "boss_zone": 5},   # rows 6-7
    "extreme": {"normal": 25, "gathering": 10, "danger": 30, "discovery": 15, "dungeon": 5,  "boss_zone": 15},  # rows 8-9
}

# Ключевые пороги % для разблокировок
THRESHOLDS = {
    "dungeon_unlocks": 45,    # подземелье появляется в меню только после этого
    "boss_zone_unlocks": 60,  # территория боссов
    "world_boss_spawns": 85,  # мировой босс может появиться
    "completion": 100,        # полное исследование
}

# Пороги с событиями (как в старой системе, но теперь привязаны к клеткам)
EXPLORATION_REWARDS = {
    5:   {"type": "hint",     "text": "🗺 Ты замечаешь старую тропу вглубь."},
    10:  {"type": "lore",     "text": "📜 На коре вырезаны знаки. Кто-то был здесь раньше."},
    15:  {"type": "treasure", "text": "💰 Ты находишь тайник охотников.", "gold": 25},
    20:  {"type": "hint",     "text": "🗺 Ты начинаешь понимать, где здесь опасно."},
    25:  {"type": "lore",     "text": "📜 Следы ведут к скалам. Здесь живут серьёзные существа."},
    30:  {"type": "treasure", "text": "🌿 Ты находишь рощу редких трав.", "resource": "silver_moss", "amount": 2},
    35:  {"type": "hint",     "text": "🗺 Ты составил подробную карту ключевых троп."},
    40:  {"type": "lore",     "text": "📜 Ты слышишь отдалённый гул из-под земли."},
    45:  {"type": "dungeon",  "text": "🕳 Ты обнаруживаешь вход в подземелье!", "unlock": "dungeon"},
    50:  {"type": "lore",     "text": "📜 Половина пути пройдена. Регион открывает тайны."},
    55:  {"type": "bonus",    "text": "✨ Понимание региона глубже: +5% шанс поимки."},
    60:  {"type": "boss",     "text": "💀 Ты входишь на территорию, где правят сильнейшие существа.", "unlock": "boss_zone"},
    65:  {"type": "lore",     "text": "📜 Ты обнаруживаешь следы древней цивилизации."},
    70:  {"type": "treasure", "text": "💎 Ты находишь кристалл в скрытой нише.", "resource": "sky_crystal", "amount": 1},
    75:  {"type": "treasure", "text": "💰 Ты находишь запасы опытного следопыта.", "gold": 80},
    80:  {"type": "bonus",    "text": "✨ Регион хорошо изучен: +10% к редким ресурсам."},
    85:  {"type": "boss",     "text": "👑 Ты чувствуешь присутствие мирового босса.", "unlock": "world_boss"},
    90:  {"type": "treasure", "text": "🔮 Ты находишь реликт прошлого.", "item": "crystal_focus"},
    95:  {"type": "lore",     "text": "📜 Почти всё изучено. Только глубочайшие тайны скрыты."},
    100: {"type": "complete", "text": "🏆 Регион полностью исследован! Ты — знаток этих мест."},
}

LOCATION_COMPLETION_BONUSES = {
    "dark_forest":    "🌲 +15% шанс встретить монстра, +10% к сбору трав.",
    "emerald_fields": "🌿 +20% к сбору полевых трав, Кристалл росы удвоен.",
    "stone_hills":    "⛰ +15% к добыче руды, тайные шахты открыты.",
    "shadow_marsh":   "🕸 +10% к поимке теневых существ.",
    "shadow_swamp":   "🌫 Редкие болотные монстры появляются чаще.",
    "volcano_wrath":  "🔥 +20% к добыче магмовой руды.",
}


# ── Генерация сетки ───────────────────────────────────────────────────────────

def _get_zone(row: int) -> str:
    if row <= 2:   return "shallow"
    if row <= 5:   return "mid"
    if row <= 7:   return "deep"
    return "extreme"


def _weighted_cell_type(row: int, explored_pct: int) -> str:
    zone = _get_zone(row)
    weights = dict(ZONE_WEIGHTS[zone])
    # Подземелье и босс-зоны не генерируются до их порогов
    if explored_pct < THRESHOLDS["dungeon_unlocks"]:
        weights["dungeon"] = 0
    if explored_pct < THRESHOLDS["boss_zone_unlocks"]:
        weights["boss_zone"] = 0
    total = sum(weights.values())
    roll = random.uniform(0, total)
    cur = 0
    for ctype, w in weights.items():
        cur += w
        if roll <= cur:
            return ctype
    return "normal"


def generate_grid(location_slug: str) -> dict:
    """Генерирует пустую 10×10 сетку. Сохраняется в БД при первом исследовании."""
    cells = {}
    for row in range(10):
        for col in range(10):
            cells[f"{col},{row}"] = {
                "type": None,       # генерируется при первом посещении
                "visited": False,
            }
    # Точка входа — центр-низ (col=5, row=0)
    entry = "5,0"
    cells[entry]["visited"] = True
    cells[entry]["type"] = "normal"
    return {
        "cells": cells,
        "current_pos": [5, 0],   # [col, row]
        "visited_count": 1,
        "location_slug": location_slug,
    }


# ── БД ────────────────────────────────────────────────────────────────────────

def _ensure_grid_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_grid_exploration (
                telegram_id   INTEGER NOT NULL,
                location_slug TEXT    NOT NULL,
                grid_data     TEXT    NOT NULL DEFAULT '{}',
                PRIMARY KEY (telegram_id, location_slug)
            )
        """)
        conn.commit()


_grid_table_ensured = False
def _lazy():
    global _grid_table_ensured
    if not _grid_table_ensured:
        _ensure_grid_table()
        _grid_table_ensured = True


def get_grid(telegram_id: int, location_slug: str) -> dict:
    _lazy()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT grid_data FROM player_grid_exploration WHERE telegram_id=? AND location_slug=?",
            (telegram_id, location_slug)
        ).fetchone()
    if row:
        return json.loads(row["grid_data"])
    # Создаём новую сетку
    grid = generate_grid(location_slug)
    _save_grid(telegram_id, location_slug, grid)
    return grid


def _save_grid(telegram_id: int, location_slug: str, grid: dict):
    _lazy()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO player_grid_exploration (telegram_id, location_slug, grid_data)
            VALUES (?,?,?)
            ON CONFLICT(telegram_id, location_slug) DO UPDATE SET grid_data=?
        """, (telegram_id, location_slug, json.dumps(grid), json.dumps(grid)))
        conn.commit()


# ── Основная логика ───────────────────────────────────────────────────────────

def get_available_directions(grid: dict) -> list[dict]:
    """
    Возвращает до 3 доступных направлений с текущей позиции.
    Направления: вперёд (row+1), влево (col-1, row+1), вправо (col+1, row+1)
    """
    col, row = grid["current_pos"]
    candidates = [
        {"dir": "forward", "label": "⬆️ Вперёд",  "col": col,     "row": row + 1},
        {"dir": "left",    "label": "↖️ Влево",    "col": col - 1, "row": row + 1},
        {"dir": "right",   "label": "↗️ Вправо",   "col": col + 1, "row": row + 1},
        # Также можно двигаться в стороны на той же глубине
        {"dir": "side_left",  "label": "⬅️ В сторону", "col": col - 1, "row": row},
        {"dir": "side_right", "label": "➡️ В сторону", "col": col + 1, "row": row},
    ]
    result = []
    for c in candidates:
        nc, nr = c["col"], c["row"]
        if 0 <= nc <= 9 and 0 <= nr <= 9:
            key = f"{nc},{nr}"
            cell = grid["cells"][key]
            if not cell["visited"]:
                c["key"] = key
                c["new"] = True
                result.append(c)
            # Ограничиваем до 3 направлений
        if len(result) >= 3:
            break
    # Если некуда идти вперёд — разрешаем идти назад/в сторону
    if not result:
        result.append({"dir": "back", "label": "🔄 Обследовать окрестности",
                       "col": col, "row": max(0, row - 1), "key": f"{col},{max(0,row-1)}", "new": False})
    return result


def explore_cell(telegram_id: int, location_slug: str, direction: str) -> dict:
    """
    Двигаемся в выбранном направлении, открываем новую клетку.
    Возвращает результат: тип клетки, событие, новый % исследования.
    """
    from game.exploration_service import _lazy_ensure, get_cartographer_level, _add_cartographer_exp
    _lazy_ensure()

    grid = get_grid(telegram_id, location_slug)
    directions = get_available_directions(grid)

    # Находим выбранное направление
    chosen = next((d for d in directions if d["dir"] == direction), None)
    if not chosen:
        # Берём первое доступное
        chosen = directions[0] if directions else None
    if not chosen:
        return {"error": "Некуда идти."}

    nc, nr = chosen["col"], chosen["row"]
    key = f"{nc},{nr}"
    cell = grid["cells"][key]
    visited_before = cell["visited"]

    # Открываем клетку если новая
    if not visited_before:
        explored_pct = int(grid["visited_count"] / 100 * 100)
        cell_type = _weighted_cell_type(nr, explored_pct)
        cell["type"] = cell_type
        cell["visited"] = True
        grid["visited_count"] += 1

    grid["current_pos"] = [nc, nr]
    _save_grid(telegram_id, location_slug, grid)

    # Прогресс картографа
    cart_level = get_cartographer_level(telegram_id)
    gain = random.randint(1, min(3, 1 + cart_level // 3))
    _add_cartographer_exp(telegram_id, 1)

    visited_count = grid["visited_count"]
    pct = min(100, visited_count)

    # Проверяем пороговые события
    threshold_reward = None
    for threshold in sorted(EXPLORATION_REWARDS.keys()):
        if pct == threshold:
            threshold_reward = EXPLORATION_REWARDS[threshold].copy()
            break

    cell_info = CELL_TYPES.get(cell["type"], CELL_TYPES["normal"])

    return {
        "pct": pct,
        "visited_count": visited_count,
        "col": nc,
        "row": nr,
        "cell_type": cell["type"],
        "cell_icon": cell_info["icon"],
        "cell_name": cell_info["name"],
        "cell_info": cell_info,
        "new_cell": not visited_before,
        "direction": chosen["label"],
        "threshold_reward": threshold_reward,
        "dungeon_available": pct >= THRESHOLDS["dungeon_unlocks"],
        "boss_zone": cell["type"] == "boss_zone",
        "is_dungeon": cell["type"] == "dungeon",
    }


def render_grid_map(grid: dict) -> str:
    """Рендерит мини-карту 10×10 для отображения."""
    col_cur, row_cur = grid["current_pos"]
    lines = []
    for row in range(9, -1, -1):  # сверху вниз (строка 9 = глубина, строка 0 = вход)
        row_str = ""
        for col in range(10):
            key = f"{col},{row}"
            cell = grid["cells"][key]
            if col == col_cur and row == row_cur:
                row_str += "📍"
            elif not cell["visited"]:
                row_str += "⬜"
            else:
                icons = {
                    "normal":    "🟩",
                    "gathering": "🟦",
                    "danger":    "🟥",
                    "discovery": "🟨",
                    "dungeon":   "🕳",
                    "boss_zone": "💀",
                }
                row_str += icons.get(cell["type"], "🟩")
        lines.append(row_str)
    lines.append("")
    lines.append("⬜ Не исследовано  🟩 Обычная  🟦 Сбор  🟥 Опасность  🟨 Находка  🕳 Подземелье  💀 Босс")
    return "\n".join(lines)


def render_exploration_result(result: dict, location_slug: str) -> str:
    """Форматирует результат исследования клетки."""
    if result.get("error"):
        return result["error"]

    lines = []

    if result["new_cell"]:
        lines.append(f"{result['direction']} → {result['cell_icon']} {result['cell_name']}")
        lines.append(f"Позиция: колонка {result['col']+1}, глубина {result['row']+1}")
    else:
        lines.append(f"Ты обследуешь уже знакомое место.")

    lines.append(f"\n🗺 Исследовано: {result['pct']}%  📐 Картограф {result.get('cart_level', 1)} ур.")

    # Особые события клетки
    if result["cell_type"] == "gathering":
        lines.append("🧺 Хорошее место для сбора — здесь больше ресурсов!")
    elif result["cell_type"] == "danger":
        lines.append("⚠️ Опасная зона — враги здесь сильнее обычного.")
    elif result["cell_type"] == "discovery":
        lines.append("✨ Ты чувствуешь что здесь что-то особенное.")
    elif result["cell_type"] == "dungeon":
        lines.append("🕳 Ты обнаружил вход в подземелье!")
    elif result["cell_type"] == "boss_zone":
        lines.append("💀 Ты входишь на территорию, где правят сильнейшие.")

    # Пороговые события
    reward = result.get("threshold_reward")
    if reward:
        lines.append(f"\n{reward['text']}")
        if reward.get("unlock") == "dungeon":
            lines.append("🔓 Подземелье разблокировано!")
        elif reward.get("unlock") == "world_boss":
            lines.append("👑 Территория мирового босса открыта!")
        elif reward["type"] == "complete":
            bonus = LOCATION_COMPLETION_BONUSES.get(location_slug, "")
            if bonus:
                lines.append(bonus)

    return "\n".join(lines)


def render_exploration_panel(telegram_id: int, location_slug: str) -> str:
    """Компактная панель для карточки локации."""
    grid = get_grid(telegram_id, location_slug)
    pct = min(100, grid["visited_count"])
    col, row = grid["current_pos"]

    bar_filled = pct // 10
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    from game.exploration_service import get_cartographer_level
    cart_level = get_cartographer_level(telegram_id)

    lines = [
        f"🗺 Исследование: [{bar}] {pct}%",
        f"📐 Картограф: {cart_level} ур. | Позиция: {col+1}/{row+1}",
    ]

    if pct >= THRESHOLDS["dungeon_unlocks"]:
        lines.append("🕳 Подземелье доступно")
    else:
        lines.append(f"🕳 Подземелье откроется на {THRESHOLDS['dungeon_unlocks']}%")

    if pct >= 100:
        lines.append("✅ Регион полностью исследован!")

    return "\n".join(lines)


def is_dungeon_available(telegram_id: int, location_slug: str) -> bool:
    """Подземелье доступно только после 45% исследования."""
    grid = get_grid(telegram_id, location_slug)
    return grid["visited_count"] >= THRESHOLDS["dungeon_unlocks"]


def is_world_boss_available(telegram_id: int, location_slug: str) -> bool:
    """Мировой босс только после 85%."""
    grid = get_grid(telegram_id, location_slug)
    return grid["visited_count"] >= THRESHOLDS["world_boss_spawns"]


def get_current_cell_bonuses(telegram_id: int, location_slug: str) -> dict:
    """Бонусы текущей клетки (для использования в explore/gather)."""
    grid = get_grid(telegram_id, location_slug)
    col, row = grid["current_pos"]
    key = f"{col},{row}"
    cell = grid["cells"].get(key, {})
    ctype = cell.get("type", "normal")
    cell_info = CELL_TYPES.get(ctype, {})
    return {
        "gather_bonus": cell_info.get("gather_bonus", 0.0),
        "enemy_bonus":  cell_info.get("enemy_bonus",  1.0),
        "cell_type":    ctype,
    }
