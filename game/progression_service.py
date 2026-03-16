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

def render_attributes(player):
    return "\n".join([
        "Характеристики героя:",
        f"{ATTRIBUTE_LABELS['strength']}: {player.strength} — повышает шансы геолога и качество тяжёлой добычи.",
        f"{ATTRIBUTE_LABELS['agility']}: {player.agility} — повышает шанс поимки и успех ловца.",
        f"{ATTRIBUTE_LABELS['intellect']}: {player.intellect} — усиливает сбор редких трав и успех алхимии.",
        f"Свободные очки: {player.stat_points}",
    ])

def render_professions(player):
    return "\n".join([
        "Профессии:",
        f"{PROFESSION_LABELS['gatherer_level']}: {player.gatherer_level} — влияет на обычный сбор и травы.",
        f"{PROFESSION_LABELS['hunter_level']}: {player.hunter_level} — повышает шанс поимки монстров.",
        f"{PROFESSION_LABELS['geologist_level']}: {player.geologist_level} — улучшает добычу камней и редких жил.",
        f"{PROFESSION_LABELS['alchemist_level']}: {player.alchemist_level} — даёт шанс создать дополнительный предмет.",
        f"{PROFESSION_LABELS['merchant_level']}: {player.merchant_level} — повышает цену продажи ресурсов.",
    ])
