import random

HAZARDS_BY_LOCATION = {
    "shadow_swamp": [
        {"id": "poison_fog", "text": "🧪 Ядовитый туман обжигает лёгкие и жалит кожу монстра.", "damage": 3, "effect_counter": "swamp_guard"},
        {"id": "sink_mud", "text": "🪵 Топкая грязь замедляет продвижение и ранит активного монстра.", "damage": 2, "effect_counter": "swamp_guard"},
    ],
    "shadow_marsh": [
        {"id": "marsh_poison", "text": "🌫 Болотные испарения оказываются токсичными.", "damage": 4, "effect_counter": "swamp_guard"},
        {"id": "ghost_reeds", "text": "🎐 Призрачный камыш режет словно лезвие.", "damage": 3, "effect_counter": "swamp_guard"},
    ],
    "stone_hills": [
        {"id": "rockfall", "text": "🪨 Сверху срывается каменный дождь.", "damage": 4, "effect_counter": "crystal_skin"},
        {"id": "crystal_burst", "text": "💎 Осколки кристаллов вспыхивают и ранят твою команду.", "damage": 3, "effect_counter": "crystal_skin"},
    ],
    "volcano_wrath": [
        {"id": "heat_wave", "text": "🔥 Волна жара обжигает всё вокруг.", "damage": 5, "effect_counter": "crystal_skin"},
    ],
    "emerald_fields": [
        {"id": "wind_surge", "text": "💨 Ветер меняет следы и открывает лучший маршрут.", "damage": 0, "effect_counter": "field_capture"},
    ],
}

def roll_hazard(location_slug: str):
    pool = HAZARDS_BY_LOCATION.get(location_slug, [])
    if not pool:
        return None
    if random.random() <= 0.28:
        return random.choice(pool).copy()
    return None

def render_effects_text(effects: dict):
    if not effects:
        return "Активные эффекты: нет"
    labels = {
        "field_capture": "🌼 Чутьё полей",
        "crystal_skin": "💎 Кристальная защита",
        "swamp_guard": "🪷 Болотная защита",
        "elite_forest": "🌲 Элитная лесная экспедиция",
        "elite_hills": "⛰ Элитная горная экспедиция",
        "elite_marsh": "🕸 Элитная болотная экспедиция",
    }
    parts = []
    for key, turns in effects.items():
        if turns > 0:
            parts.append(f"{labels.get(key, key)} ({turns})")
    return "Активные эффекты: " + (", ".join(parts) if parts else "нет")
