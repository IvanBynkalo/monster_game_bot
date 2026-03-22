RECIPES = {
    "field_elixir": {
        "name": "Эликсир лугов",
        "emoji": "🌼",
        "ingredients": {"field_grass": 2, "sun_blossom": 1},
        "result_item": "field_elixir",
        "result_amount": 1,
        "description": "Повышает шанс удачной поимки в полях.",
        "hero_level": 1,
        "alchemy_level": 1,
    },
    "big_potion": {
        "name": "Большое зелье",
        "emoji": "🧪",
        "ingredients": {"forest_herb": 2, "mushroom_cap": 1},
        "result_item": "big_potion",
        "result_amount": 1,
        "description": "Сильное лечебное зелье для активного монстра.",
        "hero_level": 2,
        "alchemy_level": 2,
    },
    "spark_tonic": {
        "name": "Настой искры",
        "emoji": "✨",
        "ingredients": {"ember_stone": 1, "ash_leaf": 2},
        "result_item": "spark_tonic",
        "result_amount": 1,
        "description": "Тоник для быстрого восстановления энергии.",
        "hero_level": 3,
        "alchemy_level": 2,
    },
    "poison_trap": {
        "name": "Ядовитая ловушка",
        "emoji": "🪤",
        "ingredients": {"swamp_moss": 1, "toxic_spore": 2},
        "result_item": "poison_trap",
        "result_amount": 1,
        "description": "Ловушка для сложных поимок и вязких боёв.",
        "hero_level": 4,
        "alchemy_level": 3,
    },
    "crystal_focus": {
        "name": "Кристальный концентрат",
        "emoji": "💎",
        "ingredients": {"raw_ore": 1, "sky_crystal": 1},
        "result_item": "crystal_focus",
        "result_amount": 1,
        "description": "Редкий концентрат, усиливающий интеллект монстра.",
        "hero_level": 5,
        "alchemy_level": 4,
    },
    "swamp_antidote": {
        "name": "Болотный антидот",
        "emoji": "🪷",
        "ingredients": {"bog_flower": 1, "dark_resin": 1},
        "result_item": "swamp_antidote",
        "result_amount": 1,
        "description": "Защищает от болотных эффектов.",
        "hero_level": 6,
        "alchemy_level": 4,
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
        lines.append(f"{RESOURCE_LABELS.get(slug, slug.replace('_', ' ').title())} x{qty}")

    if not shown:
        lines.append("У тебя пока нет ресурсов.")

    return "\n".join(lines)


def make_recipe_button(recipe: dict) -> str:
    return f"{recipe['emoji']} Создать: {recipe['name']}"


def get_visible_recipe_ids(player):
    visible = []
    for recipe_id, recipe in RECIPES.items():
        if player.level >= recipe.get("hero_level", 1):
            visible.append(recipe_id)
    return visible


def get_visible_recipes(player):
    return [RECIPES[recipe_id] for recipe_id in get_visible_recipe_ids(player)]


def get_recipe_id_by_button_text(button_text: str):
    text = (button_text or "").strip()
    for recipe_id, recipe in RECIPES.items():
        if text == make_recipe_button(recipe):
            return recipe_id
    return None


def has_recipe_resources(resources: dict, recipe: dict) -> bool:
    for slug, need in recipe["ingredients"].items():
        if resources.get(slug, 0) < need:
            return False
    return True


def meets_alchemy_requirement(player, recipe: dict) -> bool:
    return player.alchemist_level >= recipe.get("alchemy_level", 1)


def can_craft_recipe_now(player, resources: dict, recipe: dict) -> bool:
    if player.level < recipe.get("hero_level", 1):
        return False
    if not meets_alchemy_requirement(player, recipe):
        return False
    if not has_recipe_resources(resources, recipe):
        return False
    return True


def get_craftable_recipe_ids(player, resources: dict):
    craftable = []
    for recipe_id in get_visible_recipe_ids(player):
        recipe = RECIPES[recipe_id]
        if can_craft_recipe_now(player, resources, recipe):
            craftable.append(recipe_id)
    return craftable


def render_craft_text(player, resources: dict):
    lines = ["🛠 Мастерская", ""]

    visible_ids = get_visible_recipe_ids(player)

    if not visible_ids:
        lines.append("Рецепты пока не открыты.")
        return "\n".join(lines)

    for recipe_id in visible_ids:
        recipe = RECIPES[recipe_id]

        lines.append(f"{recipe['emoji']} {recipe['name']}")
        lines.append(recipe["description"])
        lines.append(
            f"Требования: герой {recipe['hero_level']} ур. | алхимия {recipe['alchemy_level']} ур."
        )
        lines.append("Нужно:")

        enough_resources = True
        for slug, need in recipe["ingredients"].items():
            have = resources.get(slug, 0)
            if have < need:
                enough_resources = False
            lines.append(f"- {RESOURCE_LABELS.get(slug, slug)}: {have}/{need}")

        if not meets_alchemy_requirement(player, recipe):
            lines.append(
                f"Недостаточный уровень алхимии ❌ "
                f"(нужно {recipe['alchemy_level']}, сейчас {player.alchemist_level})"
            )
        elif enough_resources:
            lines.append("Готово к созданию ✅")
        else:
            lines.append("Недостаточно ресурсов ❌")

        lines.append("")

    lines.append("Новые рецепты открываются по уровню героя.")
    lines.append("Создание доступно только при нужном уровне алхимии и наличии ресурсов.")

    return "\n".join(lines)
