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

# Иконки тумана войны — все двухширокие квадраты для ровного выравнивания в сетке
# Слой 1 (ближний круг): цветные квадраты, отличные от посещённых
_FOG_ICONS_NEAR = {
    "normal":    None,   # обычная зона — не показываем, нечего предсказывать
    "gathering": "🟫",   # ресурсы — намёк что здесь можно собирать
    "danger":    "🟧",   # опасно — монстр или зверь
    "discovery": "🟡",   # находка — предмет, сундук, подземелье, развалины
    "dungeon":   "🟡",   # подземелье — особая находка
    "boss_zone": "🔴",   # территория босса — серьёзная угроза
    "cleared":   "🟢",   # зачищено — безопасно
}
# Слои 2+ (дальние круги): более тусклые/нейтральные
_FOG_ICONS_FAR = {
    "normal":    None,   # обычная — не показываем
    "gathering": "▫️",   # слабый намёк на ресурсы
    "danger":    "▪️",   # слабый намёк на опасность
    "discovery": "▫️",   # слабый намёк на находку
    "dungeon":   "▫️",
    "boss_zone": "▪️",
    "cleared":   None,   # зачищенное вдали не показываем
}
# Однословные подписи для легенды (по иконке ближнего круга)
_FOG_LEGEND = {
    "🟫": "ресурсы",
    "🟧": "опасно",
    "🟡": "находка",
    "🔴": "босс",
    "🟢": "зачищ",
    "▫️": "ресурсы?",
    "▪️": "опасно?",
}


# ── Генерация сетки ───────────────────────────────────────────────────────────

def _get_zone(row: int) -> str:
    if row <= 2: return "shallow"
    if row <= 5: return "mid"
    if row <= 7: return "deep"
    return "extreme"


def _weighted_cell_type(row: int, explored_pct: int, location_slug: str = "") -> str:
    zone = _get_zone(row)
    weights = dict(ZONE_WEIGHTS[zone])

    # ✅ Подземелье генерируется ТОЛЬКО в локациях из словаря DUNGEONS.
    # boss_zone генерируется ТОЛЬКО если в локации есть мировой босс.
    # Во всех остальных локациях эти клетки заменяются на "discovery".
    from game.dungeon_service import DUNGEONS
    if location_slug not in DUNGEONS:
        weights["dungeon"] = 0

    try:
        from game.world_boss_service import WORLD_BOSSES
        has_world_boss = location_slug in WORLD_BOSSES
    except Exception:
        has_world_boss = False

    if not has_world_boss or explored_pct < THRESHOLDS["boss_zone_unlocks"]:
        weights["boss_zone"] = 0

    # Перераспределяем обнулённые веса в "discovery" чтобы не потерять интерес
    removed = (ZONE_WEIGHTS[zone].get("dungeon", 0) if weights["dungeon"] == 0 else 0) + \
              (ZONE_WEIGHTS[zone].get("boss_zone", 0) if weights["boss_zone"] == 0 else 0)
    weights["discovery"] = weights.get("discovery", 0) + removed

    total = sum(weights.values())
    if total <= 0:
        return "normal"
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


def _grid_key(location_slug: str, district_slug: str | None = None) -> str:
    """Составной ключ хранения: location:district или просто location."""
    if district_slug:
        return f"{location_slug}:{district_slug}"
    return location_slug


def get_grid(telegram_id: int, location_slug: str, district_slug: str | None = None) -> dict:
    _lazy()
    key = _grid_key(location_slug, district_slug)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT grid_data FROM player_grid_exploration WHERE telegram_id=? AND location_slug=?",
            (telegram_id, key)
        ).fetchone()
    if row:
        grid = json.loads(row["grid_data"])
        grid.setdefault("last_respawn_day", 0)
        for cell in grid["cells"].values():
            cell.setdefault("cleared", False)
            cell.setdefault("original_type", cell.get("type"))
        return grid
    grid = generate_grid(location_slug)
    _save_grid(telegram_id, location_slug, grid, district_slug)
    return grid


def _save_grid(telegram_id: int, location_slug: str, grid: dict, district_slug: str | None = None):
    _lazy()
    key = _grid_key(location_slug, district_slug)
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO player_grid_exploration (telegram_id, location_slug, grid_data)
            VALUES (?,?,?)
            ON CONFLICT(telegram_id, location_slug) DO UPDATE SET grid_data=?
        """, (telegram_id, key, json.dumps(grid), json.dumps(grid)))
        conn.commit()


# ── Респаун ───────────────────────────────────────────────────────────────────

def _today_day() -> int:
    return int(time.time()) // 86400


def try_daily_respawn(telegram_id: int, location_slug: str, district_slug: str | None = None) -> bool:
    """Раз в сутки: cleared-ячейки с шансом 40% восстанавливают монстров."""
    grid = get_grid(telegram_id, location_slug, district_slug)
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
    _save_grid(telegram_id, location_slug, grid, district_slug)
    return respawned > 0


def mark_cell_cleared(telegram_id: int, location_slug: str, district_slug: str | None = None):
    """Помечает текущую ячейку как зачищенную (монстр/зверь побеждён)."""
    grid = get_grid(telegram_id, location_slug, district_slug)
    col, row = grid["current_pos"]
    key = f"{col},{row}"
    cell = grid["cells"].get(key)
    if cell and cell.get("visited"):
        orig = cell.get("original_type") or cell.get("type", "normal")
        cell["original_type"] = orig
        if orig not in ("dungeon", "boss_zone"):
            cell["cleared"] = True
            cell["type"] = "cleared"
    _save_grid(telegram_id, location_slug, grid, district_slug)


def is_cell_cleared(telegram_id: int, location_slug: str, district_slug: str | None = None) -> bool:
    grid = get_grid(telegram_id, location_slug, district_slug)
    col, row = grid["current_pos"]
    key = f"{col},{row}"
    cell = grid["cells"].get(key, {})
    return bool(cell.get("cleared")) or cell.get("type") == "cleared"


# ── Направления ───────────────────────────────────────────────────────────────

def get_available_directions(grid: dict) -> list:
    """
    Возвращает ВСЕ доступные направления в пределах сетки.
    Новые клетки помечены new=True, посещённые (включая cleared) — new=False.
    Cleared-клетки всегда доступны для перехода (сбор ресурсов).
    """
    col, row = grid["current_pos"]

    candidates = [
        {"dir": "forward", "label": "⬆️ Вперёд", "col": col,     "row": row + 1},
        {"dir": "side_l",  "label": "⬅️ Влево",  "col": col - 1, "row": row},
        {"dir": "side_r",  "label": "➡️ Вправо", "col": col + 1, "row": row},
    ]
    if row > 0:
        candidates.append({"dir": "back", "label": "⬇️ Назад", "col": col, "row": row - 1})

    result = []
    for c in candidates:
        nc, nr = c["col"], c["row"]
        if not (0 <= nc <= 9 and 0 <= nr <= 9):
            continue
        key = f"{nc},{nr}"
        cell = grid["cells"][key]
        c["key"] = key
        c["new"] = not cell["visited"]
        result.append(c)

    # Если совсем некуда (стартовая точка без соседей) — возврат к входу
    if not result:
        result.append({"dir": "back", "label": "🔄 Вернуться к входу",
                       "col": 5, "row": 0, "key": "5,0", "new": False})
    return result


# ── Исследование клетки ───────────────────────────────────────────────────────

def explore_cell(telegram_id: int, location_slug: str, direction: str, district_slug: str | None = None) -> dict:
    from game.exploration_service import _lazy_ensure, get_cartographer_level, _add_cartographer_exp
    _lazy_ensure()

    # Суточный респаун перед каждым шагом
    try_daily_respawn(telegram_id, location_slug, district_slug)

    grid = get_grid(telegram_id, location_slug, district_slug)
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
        # Новая клетка — генерируем тип с учётом локации
        explored_pct = int(grid["visited_count"] / 100 * 100)
        cell_type = _weighted_cell_type(nr, explored_pct, location_slug=location_slug)
        cell["type"] = cell_type
        cell["original_type"] = cell_type
        cell["visited"] = True
        cell["cleared"] = False
        grid["visited_count"] += 1
    else:
        # Уже посещённая — тип НЕ меняем, cleared сохраняется
        # Исключение: если это dungeon/boss_zone — всегда можно зайти
        pass

    grid["current_pos"] = [nc, nr]
    _save_grid(telegram_id, location_slug, grid, district_slug)

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
        "dungeon_available": current_type == "dungeon",  # доступно только на клетке подземелья
        "boss_zone": current_type == "boss_zone",
        "is_dungeon": current_type == "dungeon",
        "cart_level": cart_level,
    }


# ── Туман войны ───────────────────────────────────────────────────────────────

def _get_fog_cells(grid: dict, cart_level: int, location_slug: str = "") -> dict:
    """
    Туман войны масштабируется по уровню картографа:
    - 1-3:  нет предсказаний
    - 4-6:  1 круг (ближние соседи — полные иконки)
    - 7-9:  2 круга (2й круг — тусклые)
    - 10-12: 3 круга
    - 13+:  4 круга (максимум)
    """
    if cart_level < 4:
        return {}

    # Количество кругов по уровню картографа
    max_layers = min(4, (cart_level - 4) // 3 + 1)

    cells = grid["cells"]
    col_cur, row_cur = grid["current_pos"]

    # Набор всех посещённых клеток — они не получают предсказания (уже известны)
    visited_set = set()
    for key, cell in cells.items():
        if cell.get("visited"):
            c, r = map(int, key.split(","))
            visited_set.add((c, r))

    predictions = {}

    def _get_predicted_type(key: str, row: int) -> str:
        """Берём сохранённое предсказание или генерируем новое."""
        cell = cells.get(key, {})
        if cell.get("predicted_type"):
            return cell["predicted_type"]
        pct = min(100, grid.get("visited_count", 1))
        ctype = _weighted_cell_type(row, pct, location_slug=location_slug)
        cell["predicted_type"] = ctype
        return ctype

    # Слой 1 — соседи ТОЛЬКО текущей позиции игрока (не всех посещённых)
    for dc, dr in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
        nc, nr = col_cur + dc, row_cur + dr
        if not (0 <= nc <= 9 and 0 <= nr <= 9):
            continue
        nkey = f"{nc},{nr}"
        if (nc, nr) in visited_set or nkey in predictions:
            continue
        ptype = _get_predicted_type(nkey, nr)
        icon = _FOG_ICONS_NEAR.get(ptype)
        if icon is not None:   # None = обычная зона, не показываем
            predictions[nkey] = icon

    # Слои 2, 3, 4 — расширяем от предыдущего слоя
    for _layer in range(2, max_layers + 1):
        prev_keys = set(predictions.keys())
        for fkey in prev_keys:
            fc, fr = map(int, fkey.split(","))
            for dc, dr in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                nc, nr = fc + dc, fr + dr
                if not (0 <= nc <= 9 and 0 <= nr <= 9):
                    continue
                nkey = f"{nc},{nr}"
                if (nc, nr) in visited_set or nkey in predictions:
                    continue
                ptype = _get_predicted_type(nkey, nr)
                icon = _FOG_ICONS_FAR.get(ptype)
                if icon is not None:   # None = не показываем
                    predictions[nkey] = icon

    return predictions


# ── Рендер карты ──────────────────────────────────────────────────────────────

def render_mini_map(grid: dict, cart_level: int = 1) -> str:
    """
    Карта 10×10 — полная сетка, всегда все 100 клеток.

    Логика отображения каждой клетки:
    1. Игрок          → 👣
    2. Посещено       → реальный тип (🟩🟦🟥🟨🟢🕳💀) — ВСЕГДА, независимо от расстояния
    3. Предсказание   → иконка картографа (зависит от уровня)
    4. Неизвестно     → ⬜

    Предсказания картографа (уровень 4+):
    - Уровень 4-6:  1 круг вокруг посещённых клеток
    - Уровень 7-9:  2 круга
    - Уровень 10-12: 3 круга
    - Уровень 13+:  4 круга
    """
    col_cur, row_cur = grid["current_pos"]
    cells = grid["cells"]

    ICONS = {
        "normal":    "🟩",
        "gathering": "🟦",
        "danger":    "🟥",
        "discovery": "🟨",
        "dungeon":   "🕳",
        "boss_zone": "💀",
        "cleared":   "🟢",
    }

    # Предсказания картографа — только вокруг текущей позиции
    predictions = _get_fog_cells(grid, cart_level, grid.get("location_slug", ""))

    lines = []
    for row in range(9, -1, -1):
        row_str = ""
        for col in range(10):
            key = f"{col},{row}"
            cell = cells.get(key, {})
            visited = cell.get("visited", False)
            ctype = cell.get("type", "normal")
            is_cleared = cell.get("cleared", False) or ctype == "cleared"

            if col == col_cur and row == row_cur:
                # Позиция игрока
                row_str += "👣"
            elif visited:
                # ✅ ИСПРАВЛЕНО: все посещённые клетки показываем с реальным типом
                # Cleared-клетки — зелёные 🟢, остальные — по типу
                if is_cleared:
                    row_str += "🟢"
                else:
                    row_str += ICONS.get(ctype, "🟩")
            elif key in predictions:
                # Предсказание картографа для непосещённых клеток
                row_str += predictions[key]
            else:
                # Не посещено и нет предсказания — серый туман
                row_str += "⬜"
        lines.append(row_str)

    # Легенда
    lines.append("👣ты  🟩норм  🟦сбор  🟥опасно  🟨находка  🟢зачищ  🕳подзем  💀босс")

    # Подпись предсказаний картографа — только если они есть
    if cart_level >= 4 and predictions:
        used_icons = set(predictions.values())
        parts = []
        for icon in ["🟫", "🟧", "🟡", "🔴", "🟢", "▫️", "▪️"]:
            if icon in used_icons:
                word = _FOG_LEGEND.get(icon, "?")
                parts.append(f"{icon}{word}")
        layers = min(4, (cart_level - 4) // 3 + 1)
        if parts:
            lines.append(f"🗺 Картограф ур.{cart_level} · {layers} кр.: {' · '.join(parts)}")

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


def render_exploration_panel(telegram_id: int, location_slug: str, district_slug: str | None = None) -> str:
    grid = get_grid(telegram_id, location_slug, district_slug)
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

    # Подземелье появляется на карте как клетка 🕳 при 45% исследования
    # Строку-подсказку убираем — игрок должен найти его сам на карте
    if pct >= 100:
        lines.append("✅ Регион полностью исследован!")

    return "\n".join(lines)


def is_dungeon_available(telegram_id: int, location_slug: str, district_slug: str | None = None) -> bool:
    """
    Подземелье доступно если:
    1. Локация есть в словаре DUNGEONS (подземелье для неё предусмотрено).
    2. Игрок стоит на клетке типа 'dungeon' в гриде.
    Клетка 'dungeon' генерируется только в локациях из DUNGEONS (см. _weighted_cell_type),
    поэтому двойная проверка защищает от любых edge-case.
    """
    from game.dungeon_service import DUNGEONS
    if location_slug not in DUNGEONS:
        return False
    grid = get_grid(telegram_id, location_slug, district_slug)
    col, row = grid["current_pos"]
    key = f"{col},{row}"
    cell = grid["cells"].get(key, {})
    return cell.get("type") == "dungeon"


def has_any_dungeon_cell(telegram_id: int, location_slug: str) -> bool:
    """
    Возвращает True если в гриде локации есть хоть одна посещённая клетка-подземелье.
    """
    from game.dungeon_service import DUNGEONS
    if location_slug not in DUNGEONS:
        return False
    grid = get_grid(telegram_id, location_slug)
    for cell in grid["cells"].values():
        if cell.get("visited") and cell.get("type") == "dungeon":
            return True
    return False


def is_world_boss_available(telegram_id: int, location_slug: str) -> bool:
    grid = get_grid(telegram_id, location_slug)
    return grid["visited_count"] >= THRESHOLDS["world_boss_spawns"]


def get_current_cell_bonuses(telegram_id: int, location_slug: str, district_slug: str | None = None) -> dict:
    grid = get_grid(telegram_id, location_slug, district_slug)
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
