ITEMS = {
    "small_potion": {
        "name": "Малое зелье",
        "emoji": "🧪",
        "description": "Восстанавливает 12 HP активному монстру.",
        "usable_in_menu": True,
    },
    "energy_capsule": {
        "name": "Капсула энергии",
        "emoji": "⚡",
        "description": "Восстанавливает 3 энергии игроку.",
        "usable_in_menu": True,
    },
    "basic_trap": {
        "name": "Простая ловушка",
        "emoji": "🪤",
        "description": "В бою повышает шанс поимки цели на 15%.",
        "usable_in_menu": False,
    },
    "big_potion": {
        "name": "Большое зелье",
        "emoji": "🧪",
        "description": "Восстанавливает 25 HP активному монстру.",
        "usable_in_menu": True,
    },
    "poison_trap": {
        "name": "Ядовитая ловушка",
        "emoji": "🪤",
        "description": "Даёт +25% к шансу поимки и ослабляет врага.",
        "usable_in_menu": False,
    },
    "spark_tonic": {
        "name": "Настой искры",
        "emoji": "✨",
        "description": "Восстанавливает 5 энергии игроку.",
        "usable_in_menu": True,
    },
    "field_elixir": {
        "name": "Эликсир лугов",
        "emoji": "🌼",
        "description": "Даёт бонус к поимке на 3 исследования.",
        "usable_in_menu": True,
    },
    "crystal_focus": {
        "name": "Кристальный концентрат",
        "emoji": "💎",
        "description": "Даёт защиту от опасных скал и 4 энергии.",
        "usable_in_menu": True,
    },
    "swamp_antidote": {
        "name": "Болотный антидот",
        "emoji": "🪷",
        "description": "Защищает от болотных угроз на 3 исследования.",
        "usable_in_menu": True,
    },
}

ITEM_ORDER = [
    "small_potion",
    "big_potion",
    "energy_capsule",
    "spark_tonic",
    "basic_trap",
    "poison_trap",
    "field_elixir",
    "crystal_focus",
    "swamp_antidote",
]

RESOURCE_LABELS = {
    "forest_herb": "🌿 Лесная трава",
    "mushroom_cap": "🍄 Шляпка гриба",
    "silver_moss": "✨ Серебряный мох",
    "swamp_moss": "🪴 Болотный мох",
    "toxic_spore": "🧫 Токсичная спора",
    "black_pearl": "⚫ Чёрная жемчужина тины",
    "ember_stone": "🔥 Угольный камень",
    "ash_leaf": "🍂 Пепельный лист",
    "magma_core": "💠 Ядро магмы",
    "field_grass": "🌾 Полевая трава",
    "sun_blossom": "🌼 Солнечный цветок",
    "dew_crystal": "💧 Кристалл росы",
    "raw_ore": "⛏ Сырая руда",
    "granite_shard": "🪨 Осколок гранита",
    "sky_crystal": "💎 Небесный кристалл",
    "bog_flower": "🪷 Болотный цветок",
    "dark_resin": "🕯 Тёмная смола",
    "ghost_reed": "🎐 Призрачный камыш",
}

RESOURCE_SOURCES = {
    "dark_forest": "🌲 Тёмный лес: травы, грибы, серебряный мох",
    "emerald_fields": "🌾 Изумрудные поля: полевая трава, солнечный цветок, кристалл росы",
    "stone_hills": "⛰ Каменные холмы: руда, гранит, небесный кристалл",
    "shadow_swamp": "🪷 Теневое болото: болотный мох, споры, чёрная жемчужина тины",
    "shadow_marsh": "🌫 Мрачные топи: болотный цветок, тёмная смола, призрачный камыш",
    "volcano_wrath": "🌋 Гнев вулкана: угольный камень, пепельный лист, ядро магмы",
}


def get_item(item_slug: str):
    return ITEMS.get(item_slug)


def get_present_item_slugs(inventory: dict) -> list[str]:
    return [slug for slug in ITEM_ORDER if inventory.get(slug, 0) > 0]


def get_usable_item_slugs(inventory: dict) -> list[str]:
    result = []
    for slug in ITEM_ORDER:
        item = ITEMS[slug]
        if inventory.get(slug, 0) > 0 and item.get("usable_in_menu"):
            result.append(slug)
    return result


def render_inventory_text(inventory: dict):
    lines = ["🎒 Инвентарь", ""]
    present_items = get_present_item_slugs(inventory)

    if not present_items:
        lines.append("Рюкзак пуст.")
        lines.append("")
        lines.append("Как наполнить рюкзак:")
        lines.append("— выходи из города")
        lines.append("— исследуй локации")
        lines.append("— собирай ресурсы и лут")
        return "\n".join(lines)

    for slug in present_items:
        item = ITEMS[slug]
        qty = inventory.get(slug, 0)
        lines.append(f"{item['emoji']} {item['name']} x{qty}")
        lines.append(item["description"])
        if not item["usable_in_menu"]:
            lines.append("Используется в бою, а не из меню.")
        lines.append("")

    usable_items = get_usable_item_slugs(inventory)
    if usable_items:
        lines.append("Доступно из этого меню:")
        for slug in usable_items:
            item = ITEMS[slug]
            lines.append(f"{item['emoji']} {item['name']} — использовать")
        lines.append("")

    combat_only = [
        slug for slug in present_items
        if not ITEMS[slug].get("usable_in_menu")
    ]
    if combat_only:
        lines.append("Только для боя:")
        for slug in combat_only:
            item = ITEMS[slug]
            lines.append(f"{item['emoji']} {item['name']}")
        lines.append("")

    lines.append("📦 Ресурсы смотри отдельной кнопкой.")
    return "\n".join(lines)


def render_resources_text(resources: dict):
    lines = ["📦 Ресурсы", ""]
    has_resources = False

    for slug, label in RESOURCE_LABELS.items():
        qty = resources.get(slug, 0)
        if qty > 0:
            has_resources = True
            lines.append(f"{label} x{qty}")

    if not has_resources:
        lines.append("Сейчас у тебя нет ресурсов.")

    lines.append("")
    lines.append("Где добывать ресурсы:")
    for _, text in RESOURCE_SOURCES.items():
        lines.append(f"— {text}")

    lines.append("")
    lines.append("Как добывать:")
    lines.append("— выйди из города")
    lines.append("— исследуй внешние локации")
    lines.append("— используй кнопку «🧺 Собирать ресурсы», если она доступна")
    return "\n".join(lines)
