RELICS = {
    "forest_heart": {
        "name": "🌿 Сердце леса",
        "description": "+10% шанс поимки природных монстров",
        "effects": {"nature_capture_bonus": 0.10},
    },
    "ancient_crystal": {
        "name": "💎 Древний кристалл",
        "description": "+15% шанс редкого ресурса",
        "effects": {"rare_resource_bonus": 0.15},
    },
    "hunter_talisman": {
        "name": "🎯 Талисман охотника",
        "description": "+8% шанс поимки любого монстра",
        "effects": {"capture_bonus": 0.08},
    },
}

MAX_RELICS = 3

def get_relic(relic_slug: str):
    return RELICS.get(relic_slug)

def render_relics(relics):
    lines = ["🔮 Реликвии героя", ""]
    if not relics:
        lines.append("У тебя нет активных реликвий.")
        return "\n".join(lines)
    lines.append(f"Активно: {len(relics)} / {MAX_RELICS}")
    lines.append("")
    for r in relics:
        relic = RELICS.get(r)
        if relic:
            lines.append(f"{relic['name']}")
            lines.append(relic["description"])
            lines.append("")
    return "\n".join(lines)
