"""
combat_profiles.py — Боевые профили монстров.

Автогенерация профилей по типу/эмоции/роли/редкости.
Интеграция с существующими монстрами через get_combat_profile().
"""
import random
from game.type_service import (
    TYPE_MATRIX, ROLE_STAT_MODIFIERS, EMOTION_COMBAT_MODIFIERS,
    get_monster_role, render_matchup_preview, get_type_label,
    get_role_label, get_type_strengths_text,
)
from game.combat_skills import generate_monster_skills, render_skills_card

# Scaling по редкости
RARITY_SCALING = {
    "common":    1.0,
    "rare":      1.15,
    "epic":      1.3,
    "legendary": 1.5,
    "mythic":    1.8,
}

# Базовые статы по уровню (growth per level)
BASE_GROWTH = {"hp": 8, "attack": 2, "defense": 1, "speed": 1}


def build_combat_profile(monster: dict) -> dict:
    """
    Строит боевой профиль монстра для UI предпросмотра и расчёта урона.
    Не меняет сам монстр — только возвращает профиль.
    """
    mtype = monster.get("monster_type", "void")
    emotion = monster.get("mood", "instinct")
    rarity = monster.get("rarity", "common")
    level = monster.get("level", 1)

    # Роль: из монстра если есть, иначе по типу
    role = monster.get("role") or get_monster_role(mtype)

    # Базовые статы из монстра
    base_hp = monster.get("max_hp", monster.get("hp", 10))
    base_atk = monster.get("attack", 3)

    # Дефолтные defense и speed (в БД их нет — считаем по роли)
    role_mods = ROLE_STAT_MODIFIERS.get(role, {})
    rarity_scale = RARITY_SCALING.get(rarity, 1.0)

    defense = max(0, int(base_atk * 0.3 * role_mods.get("defense", 1.0)))
    speed = max(1, int(5 * role_mods.get("speed", 1.0)))

    # Эмоциональные теги
    emotion_data = EMOTION_COMBAT_MODIFIERS.get(emotion, {})
    emotion_tags = emotion_data.get("tags", [])

    # Трейты из типа
    type_tags = TYPE_MATRIX.get(mtype, {}).get("combat_tags", [])

    # Генерируем скиллы если нет кэша
    skills = generate_monster_skills(mtype, emotion, role, rarity)

    return {
        "monster_id": monster.get("id"),
        "name": monster.get("name", "Монстр"),
        "type": mtype,
        "type_label": get_type_label(mtype),
        "emotion": emotion,
        "role": role,
        "role_label": get_role_label(role),
        "rarity": rarity,
        "level": level,
        "hp": base_hp,
        "attack": base_atk,
        "defense": defense,
        "speed": speed,
        "strengths": TYPE_MATRIX.get(mtype, {}).get("strengths", []),
        "weaknesses": TYPE_MATRIX.get(mtype, {}).get("weaknesses", []),
        "combat_tags": list(set(type_tags + emotion_tags)),
        "skills": skills,
        "rarity_scale": rarity_scale,
    }


def render_enemy_preview(encounter: dict) -> str:
    """UI предпросмотра врага перед боем."""
    etype = encounter.get("monster_type", "void")
    lines = [
        f"👁 Осмотр врага: {encounter.get('monster_name', '???')}",
        f"Тип: {get_type_label(etype)}",
    ]
    if encounter.get("rarity_label"):
        lines.append(f"Редкость: {encounter['rarity_label']}")
    if encounter.get("hp"):
        lines.append(f"HP: {encounter['hp']}/{encounter.get('max_hp', encounter['hp'])}")
    if encounter.get("attack"):
        lines.append(f"Атака: {encounter['attack']}")

    strengths = TYPE_MATRIX.get(etype, {}).get("strengths", [])
    weaknesses = TYPE_MATRIX.get(etype, {}).get("weaknesses", [])
    if strengths:
        lines.append(f"Силён против: {', '.join(get_type_label(t) for t in strengths)}")
    if weaknesses:
        lines.append(f"Слаб против: {', '.join(get_type_label(t) for t in weaknesses)}")

    return "\n".join(lines)


def render_monster_matchup(my_monster: dict, enemy_type: str) -> str:
    """Оценка матчапа конкретного монстра против врага."""
    my_type = my_monster.get("monster_type", "void")
    rating = render_matchup_preview(my_type, enemy_type)
    type_info = get_type_strengths_text(my_type)

    lines = [
        f"🐲 {my_monster.get('name', 'Монстр')} ({get_type_label(my_type)})",
        f"Роль: {get_role_label(get_monster_role(my_type))}",
    ]
    if type_info:
        lines.append(type_info)
    if rating:
        lines.append(rating)
    return "\n".join(lines)


def render_pre_battle_selector(monsters: list[dict], enemy_type: str) -> str:
    """
    Полный UI выбора монстра перед боем.
    Сортирует монстров по выгодности матчапа.
    """
    from game.type_service import get_damage_multiplier, get_defense_multiplier, get_type_label

    enemy_label = get_type_label(enemy_type)
    lines = [f"⚔️ Выбор монстра против {enemy_label}", ""]

    rated = []
    for m in monsters:
        if not m or m.get("is_dead"):
            continue
        my_type = m.get("monster_type", "void")
        mult, _ = get_damage_multiplier(my_type, enemy_type)
        def_mult = get_defense_multiplier(my_type, enemy_type)

        if mult >= 1.5 and def_mult <= 1.0:
            rating_icon = "🟢"
            score = 3
        elif mult <= 0.7 or def_mult >= 1.5:
            rating_icon = "🔴"
            score = 1
        else:
            rating_icon = "🟡"
            score = 2

        hp = m.get("current_hp", m.get("hp", 0))
        max_hp = m.get("max_hp", m.get("hp", 1))
        hp_pct = int(hp / max(1, max_hp) * 100)

        rated.append((score, m, rating_icon, hp_pct))

    rated.sort(key=lambda x: -x[0])

    for _, m, icon, hp_pct in rated:
        my_type = m.get("monster_type", "void")
        name = m.get("name", "???")
        level = m.get("level", 1)
        is_active = "📍 " if m.get("is_active") else ""
        lines.append(
            f"{is_active}{icon} {name} ур.{level} [{get_type_label(my_type)}] HP:{hp_pct}%"
        )

    lines.append("\n📍 = активный монстр")
    return "\n".join(lines)


# ── Боевой экран: карточки врага и игрока ─────────────────────────────────────

def _hp_bar(current: int, maximum: int, length: int = 8) -> str:
    """Возвращает HP-бар из эмодзи."""
    pct = current / max(1, maximum)
    filled = round(pct * length)
    filled = max(0, min(length, filled))
    if pct > 0.6:
        icon = "🟩"
    elif pct > 0.3:
        icon = "🟨"
    else:
        icon = "🟥"
    return icon * filled + "⬛" * (length - filled)


def render_enemy_card(encounter: dict) -> str:
    """
    Полная карточка врага для боевого экрана.
    Показывает: имя, тип, редкость, HP-бар, ATK, DEF, сильные/слабые стороны.
    """
    from game.type_service import get_type_label, TYPE_MATRIX
    etype = encounter.get("monster_type", "void")
    name = encounter.get("monster_name", encounter.get("name", "???"))
    hp = encounter.get("hp", 0)
    max_hp = encounter.get("max_hp", hp)
    atk = encounter.get("attack", 0)
    # DEF считаем как ~30% от ATK (нет в данных врага явно)
    defense = max(0, int(atk * 0.3))
    rarity_label = encounter.get("rarity_label", "")
    mood_label = encounter.get("mood_label", "")
    type_label = get_type_label(etype)
    is_wildlife = encounter.get("type") == "wildlife"

    bar = _hp_bar(hp, max_hp)
    strengths = TYPE_MATRIX.get(etype, {}).get("strengths", [])
    weaknesses = TYPE_MATRIX.get(etype, {}).get("weaknesses", [])

    lines = [
        f"{'🐾 Зверь' if is_wildlife else '👾 Монстр'}: {name}",
        f"{'─' * 28}",
    ]
    if rarity_label and not is_wildlife:
        lines.append(f"Редкость: {rarity_label}  |  Тип: {type_label}")
    else:
        lines.append(f"Тип: {type_label}")
    if mood_label and not is_wildlife:
        lines.append(f"Эмоция: {mood_label}")
    lines.append(f"HP:  {bar} {hp}/{max_hp}")
    lines.append(f"ATK: {atk}  |  DEF: ~{defense}")
    if weaknesses:
        lines.append(f"⚡ Слаб к: {', '.join(get_type_label(t) for t in weaknesses)}")
    if strengths and not is_wildlife:
        lines.append(f"🛡 Силён против: {', '.join(get_type_label(t) for t in strengths)}")
    if not is_wildlife and encounter.get("capture_chance"):
        lines.append(f"🎯 Шанс поимки: {int(encounter['capture_chance'] * 100)}%")
        if encounter.get("bonus_capture", 0) > 0:
            lines.append(f"   +{int(encounter['bonus_capture'] * 100)}% (бонус)")
    lines.append(f"💰 ~{encounter.get('reward_gold', 0)}з  ✨ {encounter.get('reward_exp', 0)} опыта")
    return "\n".join(lines)


def render_my_monster_card(monster: dict, enemy_type: str = "") -> str:
    """
    Карточка своего монстра для боевого экрана.
    Показывает: имя, уровень, тип, HP-бар, ATK, DEF, матчап.
    """
    from game.type_service import get_type_label, get_damage_multiplier, get_defense_multiplier
    if not monster:
        return "⚠️ Нет активного монстра"

    name = monster.get("name", "Монстр")
    level = monster.get("level", 1)
    hp = monster.get("current_hp", monster.get("hp", 0))
    max_hp = monster.get("max_hp", monster.get("hp", 1))
    atk = monster.get("attack", 5)
    mtype = monster.get("monster_type", "void")
    rarity = monster.get("rarity", "common")
    type_label = get_type_label(mtype)

    # DEF из combat_profiles
    role = get_monster_role(mtype)
    role_mods = ROLE_STAT_MODIFIERS.get(role, {})
    defense = max(0, int(atk * 0.3 * role_mods.get("defense", 1.0)))

    bar = _hp_bar(hp, max_hp)

    lines = [
        f"🐲 {name}  (ур. {level}  |  {type_label})",
        f"HP:  {bar} {hp}/{max_hp}",
        f"ATK: {atk}  |  DEF: ~{defense}",
    ]

    # Матчап против врага
    if enemy_type:
        mult, _ = get_damage_multiplier(mtype, enemy_type)
        def_mult = get_defense_multiplier(mtype, enemy_type)
        if mult >= 1.5 and def_mult <= 1.0:
            lines.append("🟢 Выгодный матчап — бьёшь сильнее, держишь хорошо")
        elif mult <= 0.7 or def_mult >= 1.5:
            lines.append("🔴 Невыгодный матчап — рассмотри смену монстра")
        else:
            lines.append("🟡 Нейтральный матчап")

    return "\n".join(lines)


def render_switch_monster_list(monsters: list[dict], enemy_type: str) -> tuple[str, list]:
    """
    Экран выбора монстра для смены.
    Возвращает (текст, список_для_кнопок).
    Кнопки строятся в bot.py, здесь только данные.
    """
    from game.type_service import get_type_label, get_damage_multiplier, get_defense_multiplier
    enemy_label = get_type_label(enemy_type)
    lines = [f"🔄 Выбери монстра для боя против {enemy_label}", "─" * 28, ""]

    button_data = []
    rated = []
    for m in monsters:
        if not m or m.get("is_dead"):
            continue
        mtype = m.get("monster_type", "void")
        mult, _ = get_damage_multiplier(mtype, enemy_type)
        def_mult = get_defense_multiplier(mtype, enemy_type)
        if mult >= 1.5 and def_mult <= 1.0:
            icon, score = "🟢", 3
        elif mult <= 0.7 or def_mult >= 1.5:
            icon, score = "🔴", 1
        else:
            icon, score = "🟡", 2
        rated.append((score, icon, m))

    rated.sort(key=lambda x: -x[0])

    for score, icon, m in rated:
        mtype = m.get("monster_type", "void")
        name = m.get("name", "???")
        level = m.get("level", 1)
        hp = m.get("current_hp", m.get("hp", 0))
        max_hp = m.get("max_hp", m.get("hp", 1))
        active_mark = "📍 " if m.get("is_active") else ""
        bar = _hp_bar(hp, max_hp, length=5)
        type_label = get_type_label(mtype)

        lines.append(
            f"{active_mark}{icon} {name}  ур.{level}\n"
            f"   {type_label}  HP: {bar} {hp}/{max_hp}"
        )
        button_label = f"{active_mark}{icon} {name} ур.{level} HP:{hp}/{max_hp}"
        button_data.append({"id": m["id"], "label": button_label, "is_active": m.get("is_active", False)})

    return "\n".join(lines), button_data


# ── Пункт 6: Маркировка монстра в карточке ────────────────────────────────────

def get_matchup_badge(my_type: str, enemy_type: str) -> str:
    """Быстрый бейдж для карточки монстра: 🟢/🟡/🔴."""
    from game.type_service import get_damage_multiplier, get_defense_multiplier
    mult, _ = get_damage_multiplier(my_type, enemy_type)
    def_mult = get_defense_multiplier(my_type, enemy_type)
    if mult >= 1.5 and def_mult <= 1.0:
        return "🟢 Выгодно"
    elif mult <= 0.7 or def_mult >= 1.5:
        return "🔴 Риск"
    return "🟡 Нейтрально"


# ── Пункт 7: Локационные синергии типов ──────────────────────────────────────

# Биом локации → типы монстров которые получают бонус
BIOME_TYPE_SYNERGY = {
    "лес":    ["nature", "shadow"],
    "поля":   ["nature", "spirit"],
    "горы":   ["bone",   "storm"],
    "болото": ["shadow", "void"],
    "вулкан": ["flame",  "bone"],
    "руины":  ["echo",   "void"],
    "разлом": ["void",   "spirit"],
}

# Бонус синергии: +10% к урону в родном биоме
BIOME_SYNERGY_BONUS = 0.10


def get_biome_synergy_bonus(monster_type: str, location_biome: str) -> float:
    """
    Возвращает бонусный мультипликатор если монстр родной для биома локации.
    Используется в encounter_service как дополнительный множитель.
    """
    synergy_types = BIOME_TYPE_SYNERGY.get(location_biome, [])
    if monster_type in synergy_types:
        return 1.0 + BIOME_SYNERGY_BONUS
    return 1.0


def render_biome_synergy_text(monster_type: str, location_biome: str) -> str:
    """Текст для UI о синергии монстра с локацией."""
    bonus = get_biome_synergy_bonus(monster_type, location_biome)
    if bonus > 1.0:
        from game.type_service import get_type_label
        return f"🌍 Синергия с {location_biome}: +{int(BIOME_SYNERGY_BONUS*100)}% урона для {get_type_label(monster_type)}"
    return ""
