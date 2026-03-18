RECIPES = {
"field_elixir": {
    "name": "Эликсир лугов",
    "emoji": "🌼",
    "ingredients": {"field_grass": 2, "sun_blossom": 1},
    "result_item": "field_elixir",
    "result_amount": 1,
    "description": "Повышает шанс удачной поимки в полях.",
},
"crystal_focus": {
    "name": "Кристальный концентрат",
    "emoji": "💎",
    "ingredients": {"raw_ore": 1, "sky_crystal": 1},
    "result_item": "crystal_focus",
    "result_amount": 1,
    "description": "Редкий концентрат усиливающий интеллект монстра.",
},
"swamp_antidote": {
    "name": "Болотный антидот",
    "emoji": "🪷",
    "ingredients": {"bog_flower": 1, "dark_resin": 1},
    "result_item": "swamp_antidote",
    "result_amount": 1,
    "description": "Защищает от болотных эффектов.",
},

    "big_potion": {
        "name": "Большое зелье",
        "emoji": "🧪",
        "ingredients": {"forest_herb": 2, "mushroom_cap": 1},
        "result_item": "big_potion",
        "result_amount": 1,
        "description": "Сильное лечебное зелье для активного монстра.",
    },
    "poison_trap": {
        "name": "Ядовитая ловушка",
        "emoji": "🪤",
        "ingredients": {"swamp_moss": 1, "toxic_spore": 2},
        "result_item": "poison_trap",
        "result_amount": 1,
        "description": "Ловушка для сложных поимок и вязких боёв.",
    },
    "spark_tonic": {
        "name": "Настой искры",
        "emoji": "✨",
        "ingredients": {"ember_stone": 1, "ash_leaf": 2},
        "result_item": "spark_tonic",
        "result_amount": 1,
        "description": "Тоник для быстрого восстановления энергии.",
    },
}

RESOURCE_LABELS = {
    "field_grass": "🌾 Полевая трава",
    "sun_blossom": "🌼 Солнечный цветок",
    "dew_crystal": "💧 Кристалл росы",
    "raw_ore": "⛏ Сырая руда",
    "granite_shard": "🪨 Осколок гранита",
    "sky_crystal": "💎 Небесный кристалл",
    "bog_flower": "🪷 Болотный цветок",
    "dark_resin": "🕯 Тёмная смола",
    "ghost_reed": "🎐 Призрачный камыш",
    "forest_herb": "🌿 Лесная трава",
    "mushroom_cap": "🍄 Шляпка гриба",
    "swamp_moss": "🪴 Болотный мох",
    "toxic_spore": "🧫 Токсичная спора",
    "ember_stone": "🔥 Угольный камень",
    "ash_leaf": "🍂 Пепельный лист",
}

def render_resources_text(resources: dict):
    lines = ["📦 Ресурсы", ""]
    shown = False
    for slug, qty in resources.items():
        if qty <= 0:
            continue
        shown = True
        lines.append(f"{RESOURCE_LABELS.get(slug, slug)} x{qty}")
    if not shown:
        lines.append("У тебя пока нет ресурсов.")
    return "\n".join(lines)

def render_craft_text(resources: dict):
    lines = ["🛠 Мастерская", ""]
    for recipe in RECIPES.values():
        lines.append(f"{recipe['emoji']} {recipe['name']}")
        lines.append(recipe["description"])
        lines.append("Нужно:")
        can_craft = True
        for slug, need in recipe["ingredients"].items():
            have = resources.get(slug, 0)
            if have < need:
                can_craft = False
            lines.append(f"- {RESOURCE_LABELS.get(slug, slug)}: {have}/{need}")
        lines.append("Готово к созданию ✅" if can_craft else "Недостаточно ресурсов ❌")
        lines.append("")
    lines.append("Используй кнопки ниже для создания предметов.")
    return "\n".join(lines)
