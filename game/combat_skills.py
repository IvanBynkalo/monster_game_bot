"""
combat_skills.py — Пул способностей и система генерации скиллов по ТЗ.

Структура:
  SKILLS_POOL — все боевые способности
  EFFECTS_POOL — все эффекты (DoT, баффы, дебаффы, контроль)
  PASSIVE_POOL — пассивные способности
  generate_monster_skills() — автогенерация по типу/эмоции/роли/редкости
"""

import random

# ── Пул скиллов ───────────────────────────────────────────────────────────────

SKILLS_POOL = {
    # Базовые атаки
    "strike": {
        "name": "Удар", "type": "attack", "power": 1.0, "cooldown": 0,
        "target": "enemy", "scaling": "attack", "effect": None,
        "desc": "Обычный удар без кулдауна.",
    },
    "heavy_strike": {
        "name": "Тяжёлый удар", "type": "burst", "power": 1.35, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": None,
        "desc": "Мощный удар с кулдауном.",
    },
    "quick_hit": {
        "name": "Быстрый удар", "type": "attack", "power": 0.85, "cooldown": 0,
        "target": "enemy", "scaling": "attack", "effect": None,
        "desc": "Быстрый точный удар.",
    },
    "piercing_blow": {
        "name": "Пробивающий удар", "type": "attack", "power": 1.0, "cooldown": 1,
        "target": "enemy", "scaling": "attack", "effect": "armor_pen_20",
        "desc": "Игнорирует 20% защиты.",
    },
    # Burst
    "savage_bite": {
        "name": "Жестокий укус", "type": "burst", "power": 1.5, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": None,
        "desc": "Мощный рывок и укус.",
    },
    "crushing_slam": {
        "name": "Сокрушительный удар", "type": "burst", "power": 1.6, "cooldown": 3,
        "target": "enemy", "scaling": "attack", "effect": "slow_1",
        "desc": "Замедляет врага на 1 ход.",
    },
    "flame_surge": {
        "name": "Всплеск пламени", "type": "burst_dot", "power": 1.3, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": "burn_2",
        "desc": "Поджигает врага на 2 хода.",
    },
    "storm_lunge": {
        "name": "Молниевый рывок", "type": "burst", "power": 1.2, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": "double_hit_25",
        "desc": "25% шанс дополнительного удара.",
    },
    "echo_pulse": {
        "name": "Эхо-импульс", "type": "attack", "power": 1.1, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": "break_defense_2",
        "desc": "Снижает защиту врага на 2 хода.",
    },
    "void_fracture": {
        "name": "Разлом пустоты", "type": "burst", "power": 1.25, "cooldown": 3,
        "target": "enemy", "scaling": "attack", "effect": "no_heal_2",
        "desc": "Запрещает лечение врагу на 2 хода.",
    },
    # DoT
    "burning_claw": {
        "name": "Горящий коготь", "type": "dot", "power": 0.9, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": "burn_3",
        "desc": "Поджигает на 3 хода.",
    },
    "toxic_spit": {
        "name": "Ядовитый плевок", "type": "dot", "power": 0.8, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": "poison_3",
        "desc": "Отравляет на 3 хода.",
    },
    "rot_touch": {
        "name": "Касание гнили", "type": "dot", "power": 0.7, "cooldown": 3,
        "target": "enemy", "scaling": "attack", "effect": "decay_3",
        "desc": "Разрушает HP врага каждый ход.",
    },
    "shadow_mark": {
        "name": "Теневая метка", "type": "debuff", "power": 0.85, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": "vuln_2",
        "desc": "Цель получает +15% урона 2 хода.",
    },
    # Контроль
    "fear_gaze": {
        "name": "Взгляд страха", "type": "control", "power": 0.5, "cooldown": 3,
        "target": "enemy", "scaling": "attack", "effect": "stun_chance",
        "desc": "Шанс оглушить врага на 1 ход.",
    },
    "bone_prison": {
        "name": "Костяная тюрьма", "type": "control", "power": 0.7, "cooldown": 3,
        "target": "enemy", "scaling": "attack", "effect": "root_slow",
        "desc": "Обездвиживает и замедляет врага.",
    },
    "mind_ripple": {
        "name": "Ментальная рябь", "type": "debuff", "power": 0.8, "cooldown": 2,
        "target": "enemy", "scaling": "attack", "effect": "weaken_2",
        "desc": "Снижает атаку и точность врага.",
    },
    "corrupt_mist": {
        "name": "Туман распада", "type": "debuff", "power": 0.75, "cooldown": 3,
        "target": "enemy", "scaling": "attack", "effect": "defense_heal_debuff",
        "desc": "Снижает защиту и лечение врага.",
    },
    # Защита/выживание
    "stone_guard": {
        "name": "Каменная стража", "type": "buff", "power": 0, "cooldown": 3,
        "target": "self", "scaling": None, "effect": "defense_up_2",
        "desc": "Повышает защиту на 2 хода.",
    },
    "spirit_mend": {
        "name": "Духовное лечение", "type": "heal", "power": 0, "cooldown": 3,
        "target": "self", "scaling": "hp", "effect": "heal_25pct",
        "desc": "Восстанавливает 25% макс. HP.",
    },
    "nature_renewal": {
        "name": "Природное обновление", "type": "heal", "power": 0, "cooldown": 4,
        "target": "self", "scaling": "hp", "effect": "regen_3",
        "desc": "Регенерация 3 хода.",
    },
    "shadow_veil": {
        "name": "Теневой покров", "type": "buff", "power": 0, "cooldown": 3,
        "target": "self", "scaling": None, "effect": "evasion_up_2",
        "desc": "Повышает уклонение на 2 хода.",
    },
    "haste_spark": {
        "name": "Искра ускорения", "type": "buff", "power": 0, "cooldown": 3,
        "target": "self", "scaling": None, "effect": "speed_up_2",
        "desc": "Повышает скорость и инициативу.",
    },
    # Гибриды
    "predatory_rush": {
        "name": "Хищный рывок", "type": "burst", "power": 1.2, "cooldown": 3,
        "target": "enemy", "scaling": "attack", "effect": "atk_self_up_1",
        "desc": "Атакует и усиливает себя на 1 ход.",
    },
    "resonant_break": {
        "name": "Резонансный пробой", "type": "burst", "power": 1.1, "cooldown": 3,
        "target": "enemy", "scaling": "attack", "effect": "ignore_def_break",
        "desc": "Игнорирует защиту и снижает её.",
    },
    "soul_link": {
        "name": "Душевная связь", "type": "hybrid", "power": 0.9, "cooldown": 4,
        "target": "enemy", "scaling": "attack", "effect": "lifesteal",
        "desc": "Крадёт жизнь у врага.",
    },
    "chaos_bloom": {
        "name": "Цветок хаоса", "type": "hybrid", "power": 1.0, "cooldown": 4,
        "target": "enemy", "scaling": "attack", "effect": "chaos_random",
        "desc": "Случайный мощный эффект.",
    },
    "joyful_momentum": {
        "name": "Радостный порыв", "type": "buff", "power": 0.9, "cooldown": 3,
        "target": "self", "scaling": "attack", "effect": "extra_action_25",
        "desc": "25% шанс второго действия.",
    },
    # Боссовые
    "devour_weakness": {
        "name": "Пожрать слабость", "type": "burst", "power": 1.8, "cooldown": 4,
        "target": "enemy", "scaling": "attack", "effect": "finisher_30pct",
        "desc": "Бонус ×1.8 если враг ниже 30% HP.",
    },
    "cataclysm_roar": {
        "name": "Катастрофический рёв", "type": "boss_ability", "power": 1.4, "cooldown": 4,
        "target": "enemy", "scaling": "attack", "effect": "mass_debuff",
        "desc": "Массовое ослабление врага.",
    },
}

# ── Пул пассивок ─────────────────────────────────────────────────────────────

PASSIVE_POOL = {
    "thick_hide":     {"name": "Толстая шкура",       "desc": "−10% входящего урона."},
    "sharp_instinct": {"name": "Острый инстинкт",     "desc": "+10% точности."},
    "frenzy":         {"name": "Исступление",          "desc": "При HP<50% +15% атаки."},
    "regeneration":   {"name": "Регенерация",          "desc": "Лечение в конце хода."},
    "arc_shield":     {"name": "Дуговой щит",          "desc": "Снижает первый удар."},
    "evasive_form":   {"name": "Уклончивая форма",     "desc": "+10% уклонения."},
    "spirit_grace":   {"name": "Духовная грация",      "desc": "Сопротивление контролю."},
    "bone_armor":     {"name": "Костяная броня",       "desc": "+защита против burst."},
    "resonance":      {"name": "Резонанс",             "desc": "Дебаффы длятся +1 ход."},
    "void_hunger":    {"name": "Голод пустоты",        "desc": "Бонус по ослабленным."},
}

# ── Генерация скиллов ─────────────────────────────────────────────────────────

# Таблица активных скиллов по типу
TYPE_SKILLS = {
    "nature":  ["savage_bite", "nature_renewal", "predatory_rush"],
    "shadow":  ["fear_gaze", "shadow_mark", "shadow_veil"],
    "flame":   ["flame_surge", "burning_claw", "heavy_strike"],
    "bone":    ["crushing_slam", "bone_prison", "stone_guard"],
    "storm":   ["storm_lunge", "haste_spark", "joyful_momentum"],
    "echo":    ["echo_pulse", "mind_ripple", "resonant_break"],
    "spirit":  ["spirit_mend", "soul_link", "mind_ripple"],
    "void":    ["void_fracture", "corrupt_mist", "chaos_bloom", "rot_touch"],
}

# Приоритеты по эмоции
EMOTION_SKILL_PRIORITY = {
    "rage":        ["heavy_strike", "savage_bite", "flame_surge"],
    "fear":        ["fear_gaze", "shadow_veil", "mind_ripple"],
    "instinct":    ["quick_hit", "predatory_rush", "piercing_blow"],
    "inspiration": ["spirit_mend", "nature_renewal", "haste_spark"],
    "sadness":     ["rot_touch", "mind_ripple", "corrupt_mist"],
    "joy":         ["joyful_momentum", "storm_lunge", "haste_spark"],
    "disgust":     ["toxic_spit", "corrupt_mist", "rot_touch"],
    "surprise":    ["chaos_bloom", "storm_lunge", "devour_weakness"],
}

# Базовые атаки по роли
ROLE_BASE_ATTACK = {
    "assault":    ["strike", "heavy_strike"],
    "tank":       ["strike", "crushing_slam"],
    "hunter":     ["quick_hit", "predatory_rush"],
    "controller": ["piercing_blow", "quick_hit"],
    "support":    ["strike"],
    "hybrid":     ["strike"],
}

# Пассивки по роли
ROLE_PASSIVES = {
    "assault":    ["frenzy", "void_hunger"],
    "tank":       ["thick_hide", "bone_armor"],
    "hunter":     ["sharp_instinct", "evasive_form"],
    "controller": ["resonance", "arc_shield"],
    "support":    ["regeneration", "spirit_grace"],
    "hybrid":     ["thick_hide", "sharp_instinct", "arc_shield"],
}


def generate_monster_skills(
    monster_type: str,
    emotion: str,
    role: str,
    rarity: str,
) -> dict:
    """
    Автогенерация набора скиллов монстра по типу/эмоции/роли/редкости.
    Возвращает {base_attack, active_skills, passive}.
    """
    # Базовая атака
    base_options = ROLE_BASE_ATTACK.get(role, ["strike"])
    base_attack = random.choice(base_options)

    # Активные способности
    type_pool = TYPE_SKILLS.get(monster_type, ["strike"])
    emotion_priority = EMOTION_SKILL_PRIORITY.get(emotion, [])

    # Выбираем приоритетный скилл из эмоции если он есть в пуле
    chosen_active = []
    for s in emotion_priority:
        if s in type_pool and s not in chosen_active:
            chosen_active.append(s)
            break

    # Добавляем из типового пула
    for s in type_pool:
        if s not in chosen_active and s != base_attack:
            chosen_active.append(s)

    # Количество активных по редкости
    max_active = 1
    if rarity in ("epic", "legendary", "mythic"):
        max_active = 2

    chosen_active = chosen_active[:max_active]
    if not chosen_active:
        chosen_active = ["strike"]

    # Пассивка
    passive_options = ROLE_PASSIVES.get(role, ["arc_shield"])
    passive = random.choice(passive_options)

    return {
        "base_attack": base_attack,
        "active_skills": chosen_active,
        "passive": passive,
    }


def get_skill_info(skill_id: str) -> dict:
    return SKILLS_POOL.get(skill_id, {"name": skill_id, "desc": "", "power": 1.0, "cooldown": 0})


def get_passive_info(passive_id: str) -> dict:
    return PASSIVE_POOL.get(passive_id, {"name": passive_id, "desc": ""})


def render_skills_card(skills: dict) -> str:
    """Рендер карточки скиллов монстра."""
    lines = []
    base = get_skill_info(skills.get("base_attack", "strike"))
    lines.append(f"⚔️ Базовая атака: {base['name']}")
    if base.get("desc"):
        lines.append(f"   {base['desc']}")

    for skill_id in skills.get("active_skills", []):
        s = get_skill_info(skill_id)
        cd_text = f" (КД: {s['cooldown']})" if s.get("cooldown", 0) > 0 else ""
        lines.append(f"✨ {s['name']}{cd_text}")
        if s.get("desc"):
            lines.append(f"   {s['desc']}")

    passive_id = skills.get("passive")
    if passive_id:
        p = get_passive_info(passive_id)
        lines.append(f"🔹 Пассивно: {p['name']}")
        if p.get("desc"):
            lines.append(f"   {p['desc']}")

    return "\n".join(lines)
