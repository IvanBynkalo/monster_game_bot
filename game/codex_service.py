
RARITY_LABELS = {
    "common": "Обычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
}

def render_codex_summary(discovered: set, all_monsters: set):
    total = len(all_monsters)
    found = len(discovered)
    lines = [
        "📖 Кодекс существ",
        "",
        f"Найдено: {found} / {total}",
        "",
    ]
    return "\n".join(lines)

def render_codex_list(discovered: set, all_monsters: dict):
    lines = ["📖 Кодекс существ", ""]
    for name, data in sorted(all_monsters.items()):
        if name in discovered:
            rarity = RARITY_LABELS.get(data.get("rarity"), data.get("rarity"))
            lines.append(f"✅ {name} — {rarity}")
        else:
            lines.append("❓ Неизвестное существо")
    return "\n".join(lines)
