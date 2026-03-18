ITEMS = {
    "small_potion": {
        "name": "Малое зелье",
        "emoji": "🧪",
        "description": "Восстанавливает 12 HP активному монстру.",
    },
    "energy_capsule": {
        "name": "Капсула энергии",
        "emoji": "⚡",
        "description": "Восстанавливает 3 энергии игроку.",
    },
    "basic_trap": {
        "name": "Простая ловушка",
        "emoji": "🪤",
        "description": "Используется только в бою. Повышает шанс поимки цели на 15%.",
    },
    "big_potion": {
        "name": "Большое зелье",
        "emoji": "🧪",
        "description": "Восстанавливает 25 HP активному монстру.",
    },
    "poison_trap": {
        "name": "Ядовитая ловушка",
        "emoji": "🪤",
        "description": "Используется только в бою. Даёт +25% к шансу поимки и ослабляет врага.",
    },
    "spark_tonic": {
        "name": "Настой искры",
        "emoji": "✨",
        "description": "Восстанавливает 5 энергии игроку.",
    },
    "field_elixir": {
        "name": "Эликсир лугов",
        "emoji": "🌼",
        "description": "Даёт бонус к поимке на 3 исследования.",
    },
    "crystal_focus": {
        "name": "Кристальный концентрат",
        "emoji": "💎",
        "description": "Даёт защиту от опасных скал и 4 энергии.",
    },
    "swamp_antidote": {
        "name": "Болотный антидот",
        "emoji": "🪷",
        "description": "Защищает от болотных угроз на 3 исследования.",
    },
}


def get_item(item_slug: str):
    return ITEMS.get(item_slug)


def render_inventory_text(inventory: dict):
    lines = ["🎒 Инвентарь", ""]
    has_items = False

    order = [
        "small_potion",
        "energy_capsule",
        "basic_trap",
        "big_potion",
        "poison_trap",
        "spark_tonic",
        "field_elixir",
        "crystal_focus",
        "swamp_antidote",
    ]

    for slug in order:
        qty = inventory.get(slug, 0)
        if qty <= 0:
            continue

        item = ITEMS[slug]
        has_items = True
        lines.append(f"{item['emoji']} {item['name']} x{qty}")
        lines.append(item["description"])
        lines.append("")

    if not has_items:
        lines.append("Инвентарь пуст.")
        return "\n".join(lines)

    usable_now = []
    battle_only = []

    if inventory.get("small_potion", 0) > 0:
        usable_now.append("🧪 Малое зелье")
    if inventory.get("big_potion", 0) > 0:
        usable_now.append("🧪 Большое зелье")
    if inventory.get("energy_capsule", 0) > 0:
        usable_now.append("⚡ Капсула энергии")
    if inventory.get("spark_tonic", 0) > 0:
        usable_now.append("✨ Настой искры")
    if inventory.get("field_elixir", 0) > 0:
        usable_now.append("🌼 Эликсир лугов")
    if inventory.get("crystal_focus", 0) > 0:
        usable_now.append("💎 Кристальный концентрат")
    if inventory.get("swamp_antidote", 0) > 0:
        usable_now.append("🪷 Болотный антидот")

    if inventory.get("basic_trap", 0) > 0:
        battle_only.append("🪤 Простая ловушка")
    if inventory.get("poison_trap", 0) > 0:
        battle_only.append("🪤 Ядовитая ловушка")

    if usable_now:
        lines.append("Можно использовать сейчас:")
        lines.extend(usable_now)
        lines.append("")

    if battle_only:
        lines.append("Используются только в бою:")
        lines.extend(battle_only)

    return "\n".join(lines)
