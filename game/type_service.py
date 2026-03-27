"""
type_service.py — Полная матрица типов по ТЗ Combat Layer v3.

Матрица преимуществ из ТЗ monster_types.json:
  nature:  силён против bone, spirit | слаб против flame, void
  shadow:  силён против echo, spirit | слаб против storm, flame
  flame:   силён против nature, bone | слаб против storm, void
  bone:    силён против storm, shadow | слаб против nature, spirit
  storm:   силён против shadow, flame | слаб против bone, echo
  echo:    силён против storm, void | слаб против shadow, bone
  spirit:  силён против bone, void | слаб против nature, shadow
  void:    силён против nature, flame | слаб против echo, spirit

Множители по ТЗ:
  преимущество → ×1.5
  слабость (атакующий слаб против защитника) → ×0.7
  сопротивление → ×0.8 входящего
  уязвимость → ×1.5 входящего
"""

TYPE_LABELS = {
    "flame":  "🔥 Пламя",
    "shadow": "🌑 Тень",
    "nature": "🌿 Природа",
    "spirit": "✨ Дух",
    "bone":   "🦴 Кость",
    "storm":  "⚡ Буря",
    "void":   "🌀 Пустота",
    "echo":   "🔊 Эхо",
}

# Полная матрица: type → {strengths, weaknesses, resistances, vulnerabilities}
TYPE_MATRIX = {
    "nature": {
        "strengths":       ["bone", "spirit"],
        "weaknesses":      ["flame", "void"],
        "resistances":     ["nature"],
        "vulnerabilities": ["flame"],
        "combat_tags":     ["regen", "stability"],
        "default_role":    "hybrid",
    },
    "shadow": {
        "strengths":       ["echo", "spirit"],
        "weaknesses":      ["storm", "flame"],
        "resistances":     ["shadow"],
        "vulnerabilities": ["storm"],
        "combat_tags":     ["evasion", "debuff"],
        "default_role":    "controller",
    },
    "flame": {
        "strengths":       ["nature", "bone"],
        "weaknesses":      ["storm", "void"],
        "resistances":     ["flame"],
        "vulnerabilities": ["storm"],
        "combat_tags":     ["burst"],
        "default_role":    "assault",
    },
    "bone": {
        "strengths":       ["storm", "shadow"],
        "weaknesses":      ["nature", "spirit"],
        "resistances":     ["flame"],
        "vulnerabilities": ["spirit"],
        "combat_tags":     ["armor"],
        "default_role":    "tank",
    },
    "storm": {
        "strengths":       ["shadow", "flame"],
        "weaknesses":      ["bone", "echo"],
        "resistances":     ["storm"],
        "vulnerabilities": ["bone"],
        "combat_tags":     ["double_hit"],
        "default_role":    "hunter",
    },
    "echo": {
        "strengths":       ["storm", "void"],
        "weaknesses":      ["shadow", "bone"],
        "resistances":     ["echo"],
        "vulnerabilities": ["shadow"],
        "combat_tags":     ["armor_pen"],
        "default_role":    "controller",
    },
    "spirit": {
        "strengths":       ["bone", "void"],
        "weaknesses":      ["nature", "shadow"],
        "resistances":     ["spirit"],
        "vulnerabilities": ["shadow"],
        "combat_tags":     ["heal"],
        "default_role":    "support",
    },
    "void": {
        "strengths":       ["nature", "flame"],
        "weaknesses":      ["echo", "spirit"],
        "resistances":     ["void"],
        "vulnerabilities": ["spirit"],
        "combat_tags":     ["chaos"],
        "default_role":    "hybrid",
    },
}

# Роли монстров — мультипликаторы статов по ТЗ monster_roles.json
ROLE_STAT_MODIFIERS = {
    "assault":    {"attack": 1.25, "hp": 0.9,  "defense": 0.9,  "speed": 1.05},
    "tank":       {"hp": 1.3,      "defense": 1.2, "attack": 0.9, "speed": 0.8},
    "hunter":     {"speed": 1.3,   "attack": 1.1,  "defense": 0.9},
    "controller": {"hp": 1.0,      "attack": 1.0,  "defense": 1.0, "speed": 1.0},
    "support":    {"hp": 1.2,      "attack": 0.85, "defense": 1.1},
    "hybrid":     {"hp": 1.05,     "attack": 1.05, "defense": 1.05, "speed": 1.05},
}

ROLE_LABELS = {
    "assault":    "⚔️ Штурмовик",
    "tank":       "🛡 Танк",
    "hunter":     "🎯 Охотник",
    "controller": "🌀 Контроллер",
    "support":    "💚 Поддержка",
    "hybrid":     "⚖️ Гибрид",
}

# Эмоции — боевые модификаторы по ТЗ monster_emotions.json
EMOTION_COMBAT_MODIFIERS = {
    "rage":        {"attack_mult": 1.2, "defense_mult": 0.9, "tags": ["aggressive"]},
    "fear":        {"evasion_bonus": 0.15, "tags": ["evasion"]},
    "instinct":    {"accuracy_bonus": 0.10, "tags": ["stable"]},
    "inspiration": {"tags": ["regen", "buff"]},
    "sadness":     {"tags": ["debuff"]},
    "joy":         {"speed_mult": 1.15, "tags": ["extra_action"]},
    "disgust":     {"tags": ["poison"]},
    "surprise":    {"tags": ["crit_random"]},
}


def get_type_label(type_key: str | None) -> str:
    if not type_key:
        return "—"
    return TYPE_LABELS.get(type_key, type_key)


def get_role_label(role_key: str | None) -> str:
    if not role_key:
        return "—"
    return ROLE_LABELS.get(role_key, role_key)


def get_monster_role(monster_type: str | None) -> str:
    """Возвращает дефолтную роль по типу."""
    if not monster_type:
        return "hybrid"
    return TYPE_MATRIX.get(monster_type, {}).get("default_role", "hybrid")


def get_damage_multiplier(
    attacker_type: str | None,
    defender_type: str | None,
    attacker_emotion: str | None = None,
) -> tuple[float, str]:
    """
    Возвращает (multiplier, hint_text).
    Учитывает полную матрицу типов из ТЗ:
      strength → ×1.5
      weakness → ×0.7
      нейтрально → ×1.0
    Эмоция rage добавляет +20% к атаке.
    """
    if not attacker_type or not defender_type:
        base = 1.0
        hint = ""
    else:
        att_data = TYPE_MATRIX.get(attacker_type, {})
        strengths = att_data.get("strengths", [])
        weaknesses = att_data.get("weaknesses", [])

        if defender_type in strengths:
            base = 1.5
            hint = f"🟢 Преимущество типа ({get_type_label(attacker_type)} → {get_type_label(defender_type)}): ×1.5"
        elif defender_type in weaknesses:
            base = 0.7
            hint = f"🔴 Слабость типа ({get_type_label(attacker_type)} ↓ {get_type_label(defender_type)}): ×0.7"
        else:
            base = 1.0
            hint = "Типы нейтральны"

    # Эмоциональный модификатор атаки
    emotion_mult = 1.0
    if attacker_emotion:
        em = EMOTION_COMBAT_MODIFIERS.get(attacker_emotion, {})
        emotion_mult = em.get("attack_mult", 1.0)

    return round(base * emotion_mult, 3), hint


def get_defense_multiplier(defender_type: str | None, attacker_type: str | None) -> float:
    """
    Множитель входящего урона для защитника.
    resistance → ×0.8 входящего
    vulnerability → ×1.5 входящего
    """
    if not defender_type or not attacker_type:
        return 1.0
    def_data = TYPE_MATRIX.get(defender_type, {})
    resistances = def_data.get("resistances", [])
    vulnerabilities = def_data.get("vulnerabilities", [])

    if attacker_type in vulnerabilities:
        return 1.5
    if attacker_type in resistances:
        return 0.8
    return 1.0


def render_type_hint(attacker_type: str | None, defender_type: str | None) -> str:
    """Обратная совместимость — возвращает только текст подсказки."""
    _, hint = get_damage_multiplier(attacker_type, defender_type)
    return hint


def render_matchup_preview(my_type: str | None, enemy_type: str | None) -> str:
    """Полный предпросмотр матчапа для UI перед боем."""
    if not my_type or not enemy_type:
        return ""
    mult, hint = get_damage_multiplier(my_type, enemy_type)
    def_mult = get_defense_multiplier(my_type, enemy_type)

    lines = [hint]
    if def_mult < 1.0:
        lines.append(f"🛡 Сопротивление: ×{def_mult} входящего урона")
    elif def_mult > 1.0:
        lines.append(f"⚠️ Уязвимость: ×{def_mult} входящего урона")

    if mult >= 1.5 and def_mult <= 1.0:
        rating = "🟢 Выгодный выбор"
    elif mult <= 0.7 or def_mult >= 1.5:
        rating = "🔴 Рискованный выбор"
    else:
        rating = "🟡 Нейтральный выбор"

    lines.append(rating)
    return "\n".join(lines)


def get_type_strengths_text(monster_type: str | None) -> str:
    if not monster_type:
        return ""
    data = TYPE_MATRIX.get(monster_type, {})
    strengths = [get_type_label(t) for t in data.get("strengths", [])]
    weaknesses = [get_type_label(t) for t in data.get("weaknesses", [])]
    parts = []
    if strengths:
        parts.append(f"Силён против: {', '.join(strengths)}")
    if weaknesses:
        parts.append(f"Слаб против: {', '.join(weaknesses)}")
    return "\n".join(parts)
