RECIPES = {
    "big_potion": {
        "name": "Большое зелье",
        "emoji": "🧪",
        "ingredients": {"forest_herb": 2, "mushroom_cap": 1},
        "result_item": "big_potion",
        "result_amount": 1,
        "description": "Сильное лечебное зелье для активного монстра.",
        "min_alchemist_level": 1,
    },
    "basic_trap_bundle": {
        "name": "Связка простых ловушек",
        "emoji": "🪤",
        "ingredients": {"raw_ore": 1, "forest_herb": 1},
        "result_item": "basic_trap",
        "result_amount": 2,
        "description": "Набор простых ловушек для частых вылазок.",
        "min_alchemist_level": 1,
    },
    "spark_tonic": {
        "name": "Настой искры",
        "emoji": "✨",
        "ingredients": {"ember_stone": 1, "ash_leaf": 2},
        "result_item": "spark_tonic",
        "result_amount": 1,
        "description": "Тоник для быстрого восстановления энергии.",
        "min_alchemist_level": 1,
    },
    "field_elixir": {
        "name": "Эликсир лугов",
        "emoji": "🌼",
        "ingredients": {"field_grass": 2, "sun_blossom": 1, "dew_crystal": 1},
        "result_item": "field_elixir",
        "result_amount": 1,
        "description": "Помогает в полевых экспедициях и усиливает шанс поимки.",
        "min_alchemist_level": 2,
    },
    "poison_trap": {
        "name": "Ядовитая ловушка",
        "emoji": "🪤",
        "ingredients": {"swamp_moss": 1, "toxic_spore": 2},
        "result_item": "poison_trap",
        "result_amount": 1,
        "description": "Ловушка для сложных поимок и вязких боёв.",
        "min_alchemist_level": 2,
    },
    "crystal_focus": {
        "name": "Кристальный концентрат",
        "emoji": "💎",
        "ingredients": {"raw_ore": 1, "granite_shard": 1, "sky_crystal": 1},
        "result_item": "crystal_focus",
        "result_amount": 1,
        "description": "Даёт энергию и защиту в каменных и жарких зонах.",
        "min_alchemist_level": 3,
    },
    "swamp_antidote": {
        "name": "Болотный антидот",
        "emoji": "🪷",
        "ingredients": {"bog_flower": 1, "dark_resin": 1},
        "result_item": "swamp_antidote",
        "result_amount": 1,
        "description": "Защищает от болотных эффектов на несколько исследований.",
        "min_alchemist_level": 3,
    },
    "greater_spark_batch": {
        "name": "Связка настоя искры",
        "emoji": "✨",
        "ingredients": {"ember_stone": 2, "ash_leaf": 3, "magma_core": 1},
        "result_item": "spark_tonic",
        "result_amount": 2,
        "description": "Улучшенная партия настоя искры. Даёт сразу 2 штуки.",
        "min_alchemist_level": 4,
    },
    "hunter_trap_kit": {
        "name": "Охотничий набор ловушек",
        "emoji": "🪤",
        "ingredients": {"raw_ore": 1, "toxic_spore": 1, "ghost_reed": 1},
        "result_item": "poison_trap",
        "result_amount": 2,
        "description": "Комплект для серьёзных охот. Даёт 2 ядовитые ловушки.",
        "min_alchemist_level": 4,
    },
    "master_healing_pack": {
        "name": "Набор мастера-целителя",
        "emoji": "🧪",
        "ingredients": {"forest_herb": 3, "mushroom_cap": 2, "silver_moss": 1},
        "result_item": "big_potion",
        "result_amount": 2,
        "description": "Продвинутая варка. Даёт сразу 2 больших зелья.",
        "min_alchemist_level": 5,
    },
    "field_elixir_batch": {
        "name": "Полевой комплект алхимика",
        "emoji": "🌼",
        "ingredients": {"field_grass": 3, "sun_blossom": 2, "dew_crystal": 1},
        "result_item": "field_elixir",
        "result_amount": 2,
        "description": "Партия эликсиров для длинной экспедиции по полям.",
        "min_alchemist_level": 5,
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
    "silver_moss": "✨ Серебряный мох",
    "swamp_moss": "🪴 Болотный мох",
    "toxic_spore": "🧫 Токсичная спора",
    "ember_stone": "🔥 Угольный камень",
    "ash_leaf": "🍂 Пепельный лист",
    "magma_core": "💠 Ядро магмы",
}


def recipe_button_text(recipe: dict) -> str:
    return f"{recipe['emoji']} Создать: {recipe['name']}"


def get_recipe_by_button(button_text: str):
    normalized = (button_text or "").strip()
    for recipe_id, recipe in RECIPES.items():
        if recipe_button_text(recipe) == normalized:
            return recipe_id, recipe
    return None, None


def get_unlocked_recipes(alchemist_level: int) -> list[tuple[str, dict]]:
    result = []
    for recipe_id, recipe in RECIPES.items():
        if alchemist_level >= recipe["min_alchemist_level"]:
            result.append((recipe_id, recipe))
    result.sort(key=lambda item: (item[1]["min_alchemist_level"], item[1]["name"]))
    return result


def get_next_locked_recipes(alchemist_level: int) -> list[tuple[str, dict]]:
    result = []
    for recipe_id, recipe in RECIPES.items():
        if recipe["min_alchemist_level"] > alchemist_level:
            result.append((recipe_id, recipe))
    result.sort(key=lambda item: (item[1]["min_alchemist_level"], item[1]["name"]))
    return result


def can_craft_recipe(recipe: dict, resources: dict) -> bool:
    for slug, need in recipe["ingredients"].items():
        if resources.get(slug, 0) < need:
            return False
    return True


def render_resources_text(resources: dict):
    lines = ["📦 Ресурсы", ""]
    shown = False
    for slug, label in RESOURCE_LABELS.items():
        qty = resources.get(slug, 0)
        if qty <= 0:
            continue
        shown = True
        lines.append(f"{label} x{qty}")

    if not shown:
        lines.append("У тебя пока нет ресурсов.")

    lines.append("")
    lines.append("Ресурсы добываются вне города через «🌲 Исследовать» и «🧺 Собирать ресурсы».")
    return "\n".join(lines)


def render_craft_text(player, resources: dict):
    level = player.alchemist_level
    lines = [
        "⚗ Алхимическая лаборатория",
        "",
        f"Уровень алхимика: {level}",
        "Чем выше уровень, тем больше рецептов открывается и выше шанс бонусного создания.",
        "",
    ]

    unlocked = get_unlocked_recipes(level)
    if not unlocked:
        lines.append("Пока нет доступных рецептов.")
    else:
        lines.append("Доступные рецепты:")
        lines.append("")
        for _, recipe in unlocked:
            lines.append(
                f"{recipe['emoji']} {recipe['name']} "
                f"(ур. {recipe['min_alchemist_level']}, результат: x{recipe['result_amount']})"
            )
            lines.append(recipe["description"])
            lines.append("Нужно:")
            ready = True
            for slug, need in recipe["ingredients"].items():
                have = resources.get(slug, 0)
                if have < need:
                    ready = False
                lines.append(f"— {RESOURCE_LABELS.get(slug, slug)}: {have}/{need}")
            lines.append("Готово к созданию ✅" if ready else "Недостаточно ресурсов ❌")
            lines.append("")

    next_locked = get_next_locked_recipes(level)
    if next_locked:
        lines.append("Откроется позже:")
        shown_levels = set()
        for _, recipe in next_locked[:4]:
            lvl = recipe["min_alchemist_level"]
            if (lvl, recipe["name"]) in shown_levels:
                continue
            shown_levels.add((lvl, recipe["name"]))
            lines.append(f"— ур. {lvl}: {recipe['emoji']} {recipe['name']}")
        lines.append("")

    lines.append("Используй кнопки ниже для создания открытых рецептов.")
    return "\n".join(lines)
