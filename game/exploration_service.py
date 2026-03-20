"""
exploration_service.py — система исследования регионов (Картограф).

Механика:
- Каждый регион имеет 100% исследования, у каждого игрока своё значение.
- За одну вылазку: 1-3% в зависимости от уровня Картографа (профессия).
- Каждый % открывает что-то: событие, подсказку, НПС, подземелье, тайник.
- На 100% показывается что открыто в этом регионе.
- При добавлении нового контента — % сбрасывается частично (не ниже 80%).

Профессия Картограф растёт с каждой вылазкой.
Уровень влияет на % за вылазку и на скорость перемещения (в будущем).
"""
import random
from database.repositories import get_connection

# ── Награды за каждый % исследования ─────────────────────────────────────────
# Структура: процент → (тип, данные)
# Типы: hint, treasure, npc_hint, dungeon_hint, lore, bonus_encounter

EXPLORATION_REWARDS: dict[int, dict] = {
    5:   {"type": "hint",    "text": "🗺 Ты замечаешь старую тропу, ведущую вглубь."},
    10:  {"type": "lore",    "text": "📜 На коре дерева — вырезанные знаки. Кто-то был здесь раньше."},
    15:  {"type": "treasure","text": "💰 Ты находишь старый тайник охотников.", "gold": 25},
    20:  {"type": "hint",    "text": "🗺 Ты начинаешь понимать, где здесь опасно, а где — нет."},
    25:  {"type": "lore",    "text": "📜 Отпечатки лап ведут к скалам. Здесь живут серьёзные существа."},
    30:  {"type": "treasure","text": "🌿 Ты находишь рощу редких трав.", "resource": "silver_moss", "amount": 2},
    35:  {"type": "npc_hint","text": "👁 Ты встречаешь следы чьего-то лагеря. Кто-то ещё исследует этот регион."},
    40:  {"type": "hint",    "text": "🗺 Ты составил подробную карту ключевых троп."},
    45:  {"type": "treasure","text": "💰 Ты раскапываешь спрятанный клад.", "gold": 50},
    50:  {"type": "lore",    "text": "📜 Половина пути пройдена. Регион начинает открывать тайны."},
    55:  {"type": "bonus",   "text": "✨ Твоё понимание региона глубже: +5% шанс поимки монстров здесь."},
    60:  {"type": "treasure","text": "💎 Ты находишь кристалл в забытой нише.", "resource": "sky_crystal", "amount": 1},
    65:  {"type": "lore",    "text": "📜 Ты обнаруживаешь следы древней цивилизации."},
    70:  {"type": "dungeon_hint", "text": "🕳 Ты замечаешь вход в подземный тоннель!"},
    75:  {"type": "treasure","text": "💰 Ты находишь запасы опытного следопыта.", "gold": 80},
    80:  {"type": "bonus",   "text": "✨ Регион хорошо изучен: +10% к сбору редких ресурсов."},
    85:  {"type": "lore",    "text": "📜 Ты читаешь знаки природы как открытую книгу."},
    90:  {"type": "treasure","text": "🔮 Ты находишь реликт прошлого — предмет с аурой.", "item": "crystal_focus"},
    95:  {"type": "lore",    "text": "📜 Почти всё изучено. Только самые глубокие тайны скрыты."},
    100: {"type": "complete","text": "🏆 Регион полностью исследован! Ты — знаток этих мест."},
}

# Что открыто на 100% в каждом регионе
REGION_COMPLETION_BONUSES = {
    "dark_forest":    "🌲 Тёмный лес: +15% шанс встретить редкого монстра, +10% к сбору трав.",
    "emerald_fields": "🌿 Изумрудные поля: +20% к сбору полевых трав, шанс найти Кристалл росы удвоен.",
    "stone_hills":    "⛰ Каменные холмы: +15% к добыче руды, тайные шахты открыты.",
    "shadow_marsh":   "🕸 Болота теней: +10% к поимке теневых существ, найдена тайная тропа.",
    "shadow_swamp":   "🌫 Болото теней: редкие болотные монстры появляются чаще.",
    "volcano_wrath":  "🔥 Вулкан ярости: +20% к добыче магмовой руды, вулканические монстры ослаблены.",
    "stone_hills":    "⛰ Каменные холмы: все жилы известны, добыча более эффективна.",
}


# ── Работа с БД ───────────────────────────────────────────────────────────────

def get_exploration(telegram_id: int, location_slug: str) -> int:
    """Возвращает % исследования региона (0-100)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT pct FROM player_exploration WHERE telegram_id=? AND location_slug=?",
            (telegram_id, location_slug)
        ).fetchone()
    return int(row["pct"]) if row else 0


def _set_exploration(telegram_id: int, location_slug: str, pct: int):
    pct = max(0, min(100, pct))
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO player_exploration (telegram_id, location_slug, pct)
            VALUES (?,?,?)
            ON CONFLICT(telegram_id, location_slug) DO UPDATE SET pct=?
        """, (telegram_id, location_slug, pct, pct))
        conn.commit()


def get_cartographer_level(telegram_id: int) -> int:
    """Уровень профессии Картограф (1-10)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT cartographer_level FROM players WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()
    return int(row["cartographer_level"]) if row and row["cartographer_level"] else 1


def _add_cartographer_exp(telegram_id: int, amount: int = 1):
    """Добавляет опыт картографа, повышает уровень при достижении порога."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT cartographer_level, cartographer_exp FROM players WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()
        if not row:
            return
        level = int(row["cartographer_level"] or 1)
        exp   = int(row["cartographer_exp"] or 0) + amount
        threshold = level * 10
        leveled = False
        while exp >= threshold and level < 10:
            exp -= threshold
            level += 1
            threshold = level * 10
            leveled = True
        conn.execute(
            "UPDATE players SET cartographer_level=?, cartographer_exp=? WHERE telegram_id=?",
            (level, exp, telegram_id)
        )
        conn.commit()
    return leveled, level


# ── Основная функция вылазки ──────────────────────────────────────────────────

def advance_exploration(telegram_id: int, location_slug: str) -> dict:
    """
    Вызывается при каждой вылазке (исследовании).
    Возвращает словарь с результатом: новый %, награда если есть, левелап картографа.
    """
    current_pct = get_exploration(telegram_id, location_slug)
    if current_pct >= 100:
        return {"pct": 100, "gained": 0, "reward": None, "level_up": False}

    cart_level = get_cartographer_level(telegram_id)
    # 1-3% за вылазку, зависит от уровня картографа
    gain = random.randint(1, min(3, 1 + cart_level // 3))

    new_pct = min(100, current_pct + gain)
    _set_exploration(telegram_id, location_slug, new_pct)

    # Проверяем все пороги которые пересекли
    reward = None
    for threshold in sorted(EXPLORATION_REWARDS.keys()):
        if current_pct < threshold <= new_pct:
            reward = EXPLORATION_REWARDS[threshold].copy()
            reward["pct_reached"] = threshold
            break  # одна награда за вылазку

    # Опыт картографа
    leveled, cart_new_level = _add_cartographer_exp(telegram_id, 1)

    return {
        "pct": new_pct,
        "gained": gain,
        "prev_pct": current_pct,
        "reward": reward,
        "level_up": leveled,
        "cart_level": cart_new_level,
    }


def render_exploration_text(result: dict, location_slug: str) -> str:
    """Форматирует результат исследования для отправки игроку."""
    if not result or result["gained"] == 0:
        return ""

    lines = [f"🗺 Исследование региона: {result['pct']}%"]

    reward = result.get("reward")
    if reward:
        lines.append(reward["text"])
        if reward["type"] == "complete":
            bonus = REGION_COMPLETION_BONUSES.get(location_slug, "")
            if bonus:
                lines.append(bonus)

    if result.get("level_up"):
        lines.append(f"📐 Картограф повышен до {result['cart_level']} уровня!")

    return "\n".join(lines)


def render_exploration_panel(telegram_id: int, location_slug: str) -> str:
    """Панель исследования для отображения в карточке локации или профиле."""
    pct = get_exploration(telegram_id, location_slug)
    cart_level = get_cartographer_level(telegram_id)

    bar_filled = pct // 10
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    lines = [
        f"🗺 Исследование: [{bar}] {pct}%",
        f"📐 Картограф: {cart_level} ур.",
    ]

    if pct >= 100:
        bonus = REGION_COMPLETION_BONUSES.get(location_slug, "")
        lines.append("✅ Регион полностью исследован!")
        if bonus:
            lines.append(bonus)
    else:
        next_threshold = next((t for t in sorted(EXPLORATION_REWARDS.keys()) if t > pct), None)
        if next_threshold:
            lines.append(f"До следующего открытия: {next_threshold - pct}%")

    return "\n".join(lines)


def apply_exploration_bonuses(telegram_id: int, location_slug: str) -> dict:
    """Возвращает бонусы которые активны для игрока в этой локации."""
    pct = get_exploration(telegram_id, location_slug)
    bonuses = {
        "capture_bonus": 0.0,
        "gather_bonus": 0.0,
        "rare_bonus": 0.0,
    }
    if pct >= 55:
        bonuses["capture_bonus"] += 0.05
    if pct >= 80:
        bonuses["gather_bonus"] += 0.10
        bonuses["rare_bonus"] += 0.10
    if pct >= 100:
        bonuses["capture_bonus"] += 0.05
        bonuses["rare_bonus"] += 0.05
    return bonuses
