"""
grid_exploration_service.py — Система исследования локаций на сетке 10×10.

Статусы ячеек:
  normal      — обычное событие / бой
  gathering   — бонусные ресурсы (+50% к сбору)
  danger      — повышенная опасность (враги сильнее)
  discovery   — лор, тайник, артефакт
  dungeon     — вход в подземелье (открывается на 45%+)
  boss_zone   — территория мирового босса (открывается на 60%+)
  cleared     — зачищена (монстр/зверь побеждён), доступен только сбор

Респаун раз в сутки: cleared-ячейки с шансом 40% восстанавливаются.
"""
import random
import json
import time
from database.repositories import get_connection

CELL_TYPES = {
    "normal":    {"icon": "🟩", "name": "Обычная местность"},
    "gathering": {"icon": "🟦", "name": "Место сбора",       "gather_bonus": 0.5},
    "danger":    {"icon": "🟥", "name": "Опасная зона",      "enemy_bonus": 1.3},
    "discovery": {"icon": "🟨", "name": "Находка"},
    "dungeon":   {"icon": "🕳",  "name": "Вход в подземелье"},
    "boss_zone": {"icon": "💀", "name": "Территория босса"},
    "cleared":   {"icon": "🟢", "name": "Зачищено",          "gather_bonus": 0.3},
}

ZONE_WEIGHTS = {
    "shallow": {"normal": 55, "gathering": 25, "danger": 15, "discovery": 5,  "dungeon": 0,  "boss_zone": 0},
    "mid":     {"normal": 40, "gathering": 20, "danger": 20, "discovery": 10, "dungeon": 8,  "boss_zone": 2},
    "deep":    {"normal": 30, "gathering": 15, "danger": 25, "discovery": 15, "dungeon": 10, "boss_zone": 5},
    "extreme": {"normal": 25, "gathering": 10, "danger": 30, "discovery": 15, "dungeon": 5,  "boss_zone": 15},
}

THRESHOLDS = {
    "dungeon_unlocks": 45,
    "boss_zone_unlocks": 60,
    "world_boss_spawns": 85,
    "completion": 100,
}

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

# Иконки тумана войны
_FOG_ICONS_NEAR = {
    "normal":    "🌫",
    "gathering": "🌱",
    "danger":    "⚠️",
    "discovery": "🔆",
    "dungeon":   "🕳",
    "boss_zone": "☠️",
    "cleared":   "🟢",
}
_FOG_ICONS_FAR = {
    "normal":    "░",
    "gathering": "·🌱",
    "danger":    "·⚠",
    "discovery": "·✨",
    "dungeon":   "·🕳",
    "boss_zone": "·☠",
    "cleared":   "·🟢",
}
# Однословные подписи предсказаний для легенды
_FOG_LEGEND = {
    "🌫": "туман",
    "🌱": "ресурсы",
    "⚠️": "опасно",
    "🔆": "находка",
    "🕳": "подзем",
    "☠️": "босс",
    "🟢": "зачищ",
    "░":  "даль",
    "·⚠": "опасно",
    "·🌱": "ресурсы",
    "·✨": "находка",
    "·🕳": "подзем",
    "·☠": "босс",
    "·🟢": "зачищ",
}


# ── Генерация сетки ───────────────────────────────────────────────────────────

def _get_zone(row: int) -> str:
    if row <= 2: return "shallow"
    if row <= 5: return "mid"
    if row <= 7: return "deep"
    return "extreme"


def _weighted_cell_type(row: int, explored_pct: int) -> str:
    zone = _get_zone(row)
    weights = dict(ZONE_WEIGHTS[zone])
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
    cells = {}
    for row in range(10):
        for col in range(10):
            cells[f"{col},{row}"] = {
                "type": None,
                "visited": False,
                "cleared": False,
                "original_type": None,
            }
    entry = "5,0"
    cells[entry]["visited"] = True
    cells[entry]["type"] = "normal"
    cells[entry]["original_type"] = "normal"
    return {
        "cells": cells,
        "current_pos": [5, 0],
        "visited_count": 1,
        "location_slug": location_slug,
        "last_respawn_day": 0,
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
        grid = json.loads(row["grid_data"])
        grid.setdefault("last_respawn_day", 0)
        for cell in grid["cells"].values():
            cell.setdefault("cleared", False)
            cell.setdefault("original_type", cell.get("type"))
        return grid
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


# ── Респаун ───────────────────────────────────────────────────────────────────

def _today_day() -> int:
    return int(time.time()) // 86400


def try_daily_respawn(telegram_id: int, location_slug: str) -> bool:
    """Раз в сутки: cleared-ячейки с шансом 40% восстанавливают монстров."""
    grid = get_grid(telegram_id, location_slug)
    today = _today_day()
    if grid.get("last_respawn_day", 0) >= today:
        return False

    respawned = 0
    for key, cell in grid["cells"].items():
        if not cell.get("visited") or not cell.get("cleared"):
            continue
        orig = cell.get("original_type", "normal")
        if orig in ("dungeon", "boss_zone"):
            continue
        chance = 0.40 if orig in ("danger", "normal") else 0.20
        if random.random() < chance:
            cell["cleared"] = False
            cell["type"] = orig
            respawned += 1

    grid["last_respawn_day"] = today
    _save_grid(telegram_id, location_slug, grid)
    return respawned > 0


def mark_cell_cleared(telegram_id: int, location_slug: str):
    """Помечает текущую ячейку как зачищенную (монстр/зверь побеждён)."""
    grid = get_grid(telegram_id, location_slug)
    col, row = grid["current_pos"]
    key = f"{col},{row}"
    cell = grid["cells"].get(key)
    if cell and cell.get("visited"):
        orig = cell.get("original_type") or cell.get("type", "normal")
        cell["original_type"] = orig
        if orig not in ("dungeon", "boss_zone"):
            cell["cleared"] = True
            cell["type"] = "cleared"
    _save_grid(telegram_id, location_slug, grid)


def is_cell_cleared(telegram_id: int, location_slug: str) -> bool:
    grid = get_grid(telegram_id, location_slug)
    col, row = grid["current_pos"]
    key = f"{col},{row}"
    cell = grid["cells"].get(key, {})
    return bool(cell.get("cleared")) or cell.get("type") == "cleared"


# ── Направления ───────────────────────────────────────────────────────────────

def get_available_directions(grid: dict) -> list:
    col, row = grid["current_pos"]

    forward_candidates = [
        {"dir": "forward", "label": "⬆️ Вперёд", "col": col,     "row": row + 1},
        {"dir": "side_l",  "label": "⬅️ Влево",  "col": col - 1, "row": row},
        {"dir": "side_r",  "label": "➡️ Вправо", "col": col + 1, "row": row},
    ]

    new_cells = []
    visited_cells = []

    for c in forward_candidates:
        nc, nr = c["col"], c["row"]
        if not (0 <= nc <= 9 and 0 <= nr <= 9):
            continue
        key = f"{nc},{nr}"
        cell = grid["cells"][key]
        c["key"] = key
        if not cell["visited"]:
            c["new"] = True
            new_cells.append(c)
        else:
            c["new"] = False
            visited_cells.append(c)

    back = None
    if row > 0:
        bkey = f"{col},{row - 1}"
        back = {"dir": "back", "label": "⬇️ Назад", "col": col, "row": row - 1,
                "key": bkey, "new": False}

    result = new_cells[:3]
    if not result:
        result = visited_cells[:2]
    if back and len(result) < 4:
        result.append(back)
    if not result:
        result.append({"dir": "back", "label": "🔄 Вернуться к входу",
                       "col": 5, "row": 0, "key": "5,0", "new": False})
    return result


# ── Исследование клетки ───────────────────────────────────────────────────────

def explore_cell(telegram_id: int, location_slug: str, direction: str) -> dict:
    from game.exploration_service import _lazy_ensure, get_cartographer_level, _add_cartographer_exp
    _lazy_ensure()

    # Суточный респаун перед каждым шагом
    try_daily_respawn(telegram_id, location_slug)

    grid = get_grid(telegram_id, location_slug)
    directions = get_available_directions(grid)

    chosen = next((d for d in directions if d["dir"] == direction), None)
    if not chosen:
        chosen = directions[0] if directions else None
    if not chosen:
        return {"error": "Некуда идти."}

    nc, nr = chosen["col"], chosen["row"]
    key = f"{nc},{nr}"
    cell = grid["cells"][key]
    visited_before = cell["visited"]

    if not visited_before:
        explored_pct = int(grid["visited_count"] / 100 * 100)
        cell_type = _weighted_cell_type(nr, explored_pct)
        cell["type"] = cell_type
        cell["original_type"] = cell_type
        cell["visited"] = True
        cell["cleared"] = False
        grid["visited_count"] += 1

    grid["current_pos"] = [nc, nr]
    _save_grid(telegram_id, location_slug, grid)

    cart_level = get_cartographer_level(telegram_id)
    _add_cartographer_exp(telegram_id, 1)

    visited_count = grid["visited_count"]
    pct = min(100, visited_count)

    threshold_reward = None
    for threshold in sorted(EXPLORATION_REWARDS.keys()):
        if pct == threshold:
            threshold_reward = EXPLORATION_REWARDS[threshold].copy()
            break

    current_type = cell.get("type", "normal")
    is_cleared = current_type == "cleared" or cell.get("cleared", False)
    cell_info = CELL_TYPES.get(current_type, CELL_TYPES["normal"])

    return {
        "pct": pct,
        "visited_count": visited_count,
        "col": nc,
        "row": nr,
        "cell_type": current_type,
        "cell_icon": cell_info["icon"],
        "cell_name": cell_info["name"],
        "cell_info": cell_info,
        "new_cell": not visited_before,
        "is_cleared": is_cleared,
        "direction": chosen["label"],
        "threshold_reward": threshold_reward,
        "dungeon_available": pct >= THRESHOLDS["dungeon_unlocks"],
        "boss_zone": current_type == "boss_zone",
        "is_dungeon": current_type == "dungeon",
        "cart_level": cart_level,
    }


# ── Туман войны ───────────────────────────────────────────────────────────────

def _get_fog_cells(grid: dict, cart_level: int, location_slug: str = "") -> dict:
    if cart_level < 4:
        return {}

    cells = grid["cells"]
    visited_set = set()
    for key, cell in cells.items():
        if cell.get("visited"):
            col, row = map(int, key.split(","))
            visited_set.add((col, row))

    fog = {}

    def _get_predicted_type(key: str, row: int) -> str:
        cell = cells.get(key, {})
        if cell.get("predicted_type"):
            return cell["predicted_type"]
        pct = min(100, grid.get("visited_count", 1))
        ctype = _weighted_cell_type(row, pct)
        cell["predicted_type"] = ctype
        return ctype

    for col, row in visited_set:
        for dc, dr in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nc, nr = col + dc, row + dr
            if not (0 <= nc <= 9 and 0 <= nr <= 9):
                continue
            nkey = f"{nc},{nr}"
            if (nc, nr) in visited_set or nkey in fog:
                continue
            ptype = _get_predicted_type(nkey, nr)
            fog[nkey] = _FOG_ICONS_NEAR.get(ptype, "🌫")

    if cart_level >= 10:
        layer1_keys = set(fog.keys())
        for fkey in layer1_keys:
            fc, fr = map(int, fkey.split(","))
            for dc, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
                nc, nr = fc + dc, fr + dr
                if not (0 <= nc <= 9 and 0 <= nr <= 9):
                    continue
                nkey = f"{nc},{nr}"
                if (nc, nr) in visited_set or nkey in fog:
                    continue
                ptype = _get_predicted_type(nkey, nr)
                fog[nkey] = _FOG_ICONS_FAR.get(ptype, "░")

    return fog


# ── Рендер карты ──────────────────────────────────────────────────────────────

def render_mini_map(grid: dict, cart_level: int = 1) -> str:
    """
    Карта: всегда 10 столбцов в ширину, 3 строки вперёд от позиции + 1 назад.
    Предсказания картографа подписаны одним словом в легенде.
    """
    col_cur, row_cur = grid["current_pos"]

    ICONS = {
        "normal":    "🟩",
        "gathering": "🟦",
        "danger":    "🟥",
        "discovery": "🟨",
        "dungeon":   "🕳",
        "boss_zone": "💀",
        "cleared":   "🟢",
    }

    row_start = max(0, row_cur - 1)
    row_end   = min(9, row_cur + 3)

    fog = _get_fog_cells(grid, cart_level, grid.get("location_slug", ""))

    lines = []
    header = f"🗺 Карта [1–10 / гл.{row_start+1}–{row_end+1}]"
    lines.append(header)

    for row in range(row_end, row_start - 1, -1):
        row_str = ""
        for col in range(10):
            key = f"{col},{row}"
            cell = grid["cells"].get(key, {})
            if col == col_cur and row == row_cur:
                row_str += "📍"
            elif cell.get("visited"):
                ctype = cell.get("type", "normal")
                if cell.get("cleared") and ctype != "cleared":
                    ctype = "cleared"
                row_str += ICONS.get(ctype, "🟩")
            elif key in fog:
                row_str += fog[key]
            else:
                row_str += "⬜"
        suffix = f" ← гл.{row+1}" if row == row_cur else ""
        if row == 0:
            suffix = " ← вход"
        lines.append(row_str + suffix)

    # Базовая легенда
    lines.append("📍ты  🟩норм  🟦сбор  🟥опасно  🟨находка  🟢зачищ  🕳подзем  💀босс")

    # Предсказания картографа — одно слово на иконку
    if cart_level >= 4:
        fog_icons_used = set(fog.values())
        fog_parts = []
        for icon in ["🌫","🌱","⚠️","🔆","🕳","☠️","🟢","░","·⚠","·🌱","·✨","·🕳","·☠","·🟢"]:
            if icon in fog_icons_used:
                word = _FOG_LEGEND.get(icon, "?")
                fog_parts.append(f"{icon}{word}")

        prefix = "🔭 Картограф:" if cart_level >= 10 else "🗺 Картограф:"
        if fog_parts:
            lines.append(f"{prefix} {' · '.join(fog_parts)}")
        else:
            lines.append(f"{prefix} видны зоны рядом с исследованными")

    return "\n".join(lines)


def render_grid_map(grid: dict) -> str:
    col_cur, row_cur = grid["current_pos"]
    ICONS = {
        "normal": "🟩", "gathering": "🟦", "danger": "🟥",
        "discovery": "🟨", "dungeon": "🕳", "boss_zone": "💀", "cleared": "🟢",
    }
    lines = []
    for row in range(9, -1, -1):
        row_str = ""
        for col in range(10):
            key = f"{col},{row}"
            cell = grid["cells"][key]
            if col == col_cur and row == row_cur:
                row_str += "📍"
            elif not cell["visited"]:
                row_str += "⬜"
            else:
                ctype = cell.get("type", "normal")
                if cell.get("cleared") and ctype != "cleared":
                    ctype = "cleared"
                row_str += ICONS.get(ctype, "🟩")
        lines.append(row_str)
    lines.append("")
    lines.append("⬜неизв  🟩норм  🟦сбор  🟥опасно  🟨находка  🟢зачищ  🕳подзем  💀босс")
    return "\n".join(lines)


def render_exploration_result(result: dict, location_slug: str) -> str:
    if result.get("error"):
        return result["error"]

    lines = []
    depth_bar = "▓" * (result['row'] + 1) + "░" * (9 - result['row'])

    if result["new_cell"]:
        lines.append(f"{result['direction']} → {result['cell_icon']} {result['cell_name']}")
    elif result.get("is_cleared"):
        lines.append("🟢 Зачищенная территория — здесь можно только собирать ресурсы.")
    else:
        lines.append(f"🔄 Знакомое место: {result['cell_icon']} {result['cell_name']}")

    lines.append(f"Глубина: [{depth_bar}] {result['row']+1}/10")
    lines.append(f"🗺 Исследовано: {result['pct']}%  📐 Картограф {result.get('cart_level', 1)} ур.")

    if result.get("is_cleared"):
        lines.append("🌿 Монстры здесь не появятся до следующего дня.")
    elif result["cell_type"] == "gathering":
        lines.append("🧺 Хорошее место для сбора — здесь больше ресурсов!")
    elif result["cell_type"] == "danger":
        lines.append("⚠️ Опасная зона — враги здесь сильнее обычного.")
    elif result["cell_type"] == "discovery":
        lines.append("✨ Ты чувствуешь что здесь что-то особенное.")
    elif result["cell_type"] == "dungeon":
        lines.append("🕳 Ты обнаружил вход в подземелье!")
    elif result["cell_type"] == "boss_zone":
        lines.append("💀 Ты входишь на территорию, где правят сильнейшие.")

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
    grid = get_grid(telegram_id, location_slug)
    pct = min(100, grid["visited_count"])
    col, row = grid["current_pos"]

    bar_filled = pct // 10
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    from game.exploration_service import get_cartographer_level
    cart_level = get_cartographer_level(telegram_id)

    depth_bar = "▓" * (row + 1) + "░" * (9 - row)
    lines = [
        f"🗺 Исследовано: [{bar}] {pct}%",
        f"📐 Картограф {cart_level} ур. | Глубина [{depth_bar}] {row+1}/10",
    ]

    if pct >= THRESHOLDS["dungeon_unlocks"]:
        lines.append("🕳 Подземелье доступно")
    else:
        lines.append(f"🕳 Подземелье откроется на {THRESHOLDS['dungeon_unlocks']}%")

    if pct >= 100:
        lines.append("✅ Регион полностью исследован!")

    return "\n".join(lines)


def is_dungeon_available(telegram_id: int, location_slug: str) -> bool:
    grid = get_grid(telegram_id, location_slug)
    return grid["visited_count"] >= THRESHOLDS["dungeon_unlocks"]


def is_world_boss_available(telegram_id: int, location_slug: str) -> bool:
    grid = get_grid(telegram_id, location_slug)
    return grid["visited_count"] >= THRESHOLDS["world_boss_spawns"]


def get_current_cell_bonuses(telegram_id: int, location_slug: str) -> dict:
    grid = get_grid(telegram_id, location_slug)
    col, row = grid["current_pos"]
    key = f"{col},{row}"
    cell = grid["cells"].get(key, {})
    ctype = cell.get("type", "normal")
    is_cleared = cell.get("cleared", False) or ctype == "cleared"
    cell_info = CELL_TYPES.get(ctype, {})
    is_danger = ctype in ("danger", "boss_zone")
    rare_bonus = 0.05 if ctype == "discovery" else 0.0
    return {
        "gather_bonus": cell_info.get("gather_bonus", 0.0),
        "enemy_bonus":  cell_info.get("enemy_bonus",  1.0),
        "cell_type":    ctype,
        "is_danger":    is_danger,
        "rare_bonus":   rare_bonus,
        "is_cleared":   is_cleared,
    }
