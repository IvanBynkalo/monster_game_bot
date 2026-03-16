ITEMS = {
    "small_potion": {"name": "Малое зелье", "emoji": "🧪", "description": "Восстанавливает 12 HP активному монстру."},
    "energy_capsule": {"name": "Капсула энергии", "emoji": "⚡", "description": "Восстанавливает 3 энергии игроку."},
    "basic_trap": {"name": "Простая ловушка", "emoji": "🪤", "description": "В бою повышает шанс поимки цели на 15%."},
    "big_potion": {"name": "Большое зелье", "emoji": "🧪", "description": "Восстанавливает 25 HP активному монстру."},
    "poison_trap": {"name": "Ядовитая ловушка", "emoji": "🪤", "description": "Даёт +25% к шансу поимки и ослабляет врага."},
    "spark_tonic": {"name": "Настой искры", "emoji": "✨", "description": "Восстанавливает 5 энергии игроку."},
    "field_elixir": {"name": "Эликсир лугов", "emoji": "🌼", "description": "Даёт бонус к поимке на 3 исследования."},
    "crystal_focus": {"name": "Кристальный концентрат", "emoji": "💎", "description": "Даёт защиту от опасных скал и 4 энергии."},
    "swamp_antidote": {"name": "Болотный антидот", "emoji": "🪷", "description": "Защищает от болотных угроз на 3 исследования."},
}

def get_item(item_slug: str):
    return ITEMS.get(item_slug)

def render_inventory_text(inventory: dict):
    lines = ["🎒 Инвентарь", ""]
    has_items = False
    order = ["small_potion", "energy_capsule", "basic_trap", "big_potion", "poison_trap", "spark_tonic", "field_elixir", "crystal_focus", "swamp_antidote"]
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
    lines.append("Доступные действия:")
    lines.append("🧪 Малое зелье — использовать")
    lines.append("🧪 Большое зелье — использовать")
    lines.append("⚡ Капсула энергии — использовать")
    lines.append("✨ Настой искры — использовать")
    lines.append("🪤 Простая ловушка — использовать только в бою")
    lines.append("🪤 Ядовитая ловушка — использовать только в бою")
    lines.append("🌼 Эликсир лугов — использовать")
    lines.append("💎 Кристальный концентрат — использовать")
    lines.append("🪷 Болотный антидот — использовать")
    return "\n".join(lines)
