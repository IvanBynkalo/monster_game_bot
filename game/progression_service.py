ATTRIBUTE_LABELS = {
    "strength": "💪 Сила",
    "agility": "🤸 Ловкость",
    "intellect": "🧠 Интеллект",
}

PROFESSION_LABELS = {
    "gatherer_level": "🧺 Собиратель",
    "hunter_level": "🎯 Ловец",
    "geologist_level": "⛏ Геолог",
    "alchemist_level": "⚗ Алхимик",
    "merchant_level": "💼 Торговец",
}


def get_profession_exp_required(level: int) -> int:
    return 6 + level * 4


def render_attributes(player):
    return "\n".join([
        "Характеристики героя:",
        f"{ATTRIBUTE_LABELS['strength']}: {player.strength} — повышает шансы геолога и качество тяжёлой добычи.",
        f"{ATTRIBUTE_LABELS['agility']}: {player.agility} — повышает шанс поимки и успех ловца.",
        f"{ATTRIBUTE_LABELS['intellect']}: {player.intellect} — усиливает сбор редких трав и успех алхимии.",
        f"Свободные очки: {player.stat_points}",
    ])


def _profession_line(icon_name: str, level: int, exp: int):
    if level >= 10:
        return f"{icon_name}: {level} ур. (макс.)"

    need = get_profession_exp_required(level)
    return f"{icon_name}: {level} ур. | опыт: {exp}/{need}"


def render_professions(player):
    return "\n".join([
        "Профессии:",
        _profession_line(
            PROFESSION_LABELS["gatherer_level"],
            player.gatherer_level,
            getattr(player, "gatherer_exp", 0),
        ),
        _profession_line(
            PROFESSION_LABELS["hunter_level"],
            player.hunter_level,
            getattr(player, "hunter_exp", 0),
        ),
        _profession_line(
            PROFESSION_LABELS["geologist_level"],
            player.geologist_level,
            getattr(player, "geologist_exp", 0),
        ),
        _profession_line(
            PROFESSION_LABELS["alchemist_level"],
            player.alchemist_level,
            getattr(player, "alchemist_exp", 0),
        ),
        _profession_line(
            PROFESSION_LABELS["merchant_level"],
            player.merchant_level,
            getattr(player, "merchant_exp", 0),
        ),
        "",
        "Что дают профессии:",
        "🧺 Собиратель — лучше сбор трав, растений и обычных природных ресурсов.",
        "🎯 Ловец — усиливает поимку монстров и охотничьи действия.",
        "⛏ Геолог — улучшает добычу руды, кристаллов и каменных материалов.",
        "⚗ Алхимик — повышает качество крафта и шанс бонусного результата.",
        "💼 Торговец — повышает прибыль от продажи ресурсов.",
    ])
