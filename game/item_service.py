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
        "description": "В бою повышает шанс поимки цели на 15%.",
    },
}

def get_item(item_slug: str):
    return ITEMS.get(item_slug)

def render_inventory_text(inventory: dict):
    lines = ["🎒 Инвентарь", ""]
    has_items = False
    for slug in ["small_potion", "energy_capsule", "basic_trap"]:
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
    lines.append("⚡ Капсула энергии — использовать")
    lines.append("🪤 Простая ловушка — использовать только в бою")
    return "\n".join(lines)
