from pathlib import Path

from database.models import Location

LOCATIONS = {
    "silver_city": Location(
        slug="silver_city",
        name="🏙 Сереброград",
        mood="inspiration",
        biome="город",
        description="Каменный город-убежище. Здесь находятся лавки, мастерские и главные ворота, ведущие в дикие земли.",
    ),
    "dark_forest": Location(
        slug="dark_forest",
        name="🌲 Тёмный лес",
        mood="fear",
        biome="лес",
        description="Сырая чаща, где тревога и шёпот деревьев подпитывают страх.",
    ),
    "emerald_fields": Location(
        slug="emerald_fields",
        name="🌿 Изумрудные поля",
        mood="inspiration",
        biome="поля",
        description="Бескрайние зелёные равнины, где ветер приносит запах редких трав.",
    ),
    "stone_hills": Location(
        slug="stone_hills",
        name="⛰ Каменные холмы",
        mood="instinct",
        biome="горы",
        description="Холмы из серого камня. Здесь часто находят руду и кристаллы.",
    ),
    "shadow_marsh": Location(
        slug="shadow_marsh",
        name="🕸 Болота теней",
        mood="fear",
        biome="болото",
        description="Тёмная вода и густой туман скрывают странных существ.",
    ),
    "shadow_swamp": Location(
        slug="shadow_swamp",
        name="🌫 Болото теней",
        mood="fear",
        biome="болото",
        description="Туман скрывает движения, а тени будто наблюдают за каждым шагом.",
    ),
    "ancient_ruins": Location(
        slug="ancient_ruins",
        name="🏛 Древние руины",
        mood="inspiration",
        biome="руины",
        description="Старые символы и забытые залы наполняют разум вдохновением.",
    ),
    "bone_desert": Location(
        slug="bone_desert",
        name="🏜 Пустыня костей",
        mood="instinct",
        biome="пустыня",
        description="Суровая земля проверяет выживших. Здесь просыпается хищный инстинкт.",
    ),
    "volcano_wrath": Location(
        slug="volcano_wrath",
        name="🔥 Вулкан ярости",
        mood="rage",
        biome="вулкан",
        description="Трещины земли дышат жаром. Здесь эмоции легко превращаются в ярость.",
    ),
    "storm_ridge": Location(
        slug="storm_ridge",
        name="🏔 Хребет бурь",
        mood="rage",
        biome="горы",
        description="Штормы и удары молний закаляют волю и будят внутренний гнев.",
    ),
    "emotion_rift": Location(
        slug="emotion_rift",
        name="🌌 Разлом эмоций",
        mood="inspiration",
        biome="разлом",
        description="Нестабильная зона, где чувства обретают форму быстрее обычного.",
    ),
}

TRAVEL_GRAPH = {
    "silver_city": ["dark_forest"],
    "dark_forest": ["silver_city", "shadow_swamp", "ancient_ruins", "emerald_fields"],
    "emerald_fields": ["dark_forest", "stone_hills"],
    "stone_hills": ["emerald_fields", "bone_desert"],
    "shadow_marsh": ["shadow_swamp"],
    "shadow_swamp": ["dark_forest", "emotion_rift", "shadow_marsh"],
    "ancient_ruins": ["dark_forest", "bone_desert", "emotion_rift"],
    "bone_desert": ["ancient_ruins", "volcano_wrath", "storm_ridge", "stone_hills"],
    "volcano_wrath": ["bone_desert", "storm_ridge"],
    "storm_ridge": ["bone_desert", "volcano_wrath"],
    "emotion_rift": ["shadow_swamp", "ancient_ruins"],
}

MOOD_LABELS = {
    "rage": "🔥 Ярость",
    "fear": "😱 Страх",
    "instinct": "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение",
}

BASE_DIR = Path(__file__).resolve().parent.parent
WORLD_MAP_PATH = BASE_DIR / "assets" / "world_map.png"


def get_location(location_slug: str):
    return LOCATIONS.get(location_slug)


def get_location_name(location_slug: str) -> str:
    location = get_location(location_slug)
    return location.name if location else location_slug


def get_connected_locations(location_slug: str):
    return [LOCATIONS[slug] for slug in TRAVEL_GRAPH.get(location_slug, []) if slug in LOCATIONS]


def render_map_overview(current_slug: str) -> str:
    lines = ["🗺 Карта мира", ""]
    for slug, location in LOCATIONS.items():
        marker = "📍" if slug == current_slug else "▫️"
        lines.append(f"{marker} {location.name} — {MOOD_LABELS[location.mood]}")
    return "\n".join(lines)


def render_location_card(location_slug: str) -> str:
    location = get_location(location_slug)
    if not location:
        return "Локация не найдена."
    neighbors = get_connected_locations(location_slug)
    lines = [
        location.name,
        f"Тип местности: {location.biome}",
        f"Эмоция локации: {MOOD_LABELS[location.mood]}",
        "",
        location.description,
        "",
        "Переходы:",
    ]
    from game.location_rules import LOCATION_REQUIREMENTS
    for item in neighbors:
        req = LOCATION_REQUIREMENTS.get(item.slug, {})
        min_lvl = req.get("min_level", 1)
        if min_lvl > 1:
            lines.append(f"— {item.name} (ур.{min_lvl}+)")
        else:
            lines.append(f"— {item.name}")
    return "\n".join(lines)


def build_map_caption(current_slug: str) -> str:
    location = get_location(current_slug)
    if not location:
        return "🗺 Визуальная карта мира"
    neighbors = get_connected_locations(current_slug)
    lines = [
        "🗺 Визуальная карта мира",
        "",
        f"Сейчас ты находишься: {location.name}",
        f"Доминирующая эмоция зоны: {MOOD_LABELS[location.mood]}",
        "",
        "Доступные переходы:",
    ]
    for item in neighbors:
        lines.append(f"• {item.name}")
    return "\n".join(lines)


def get_move_commands(location_slug: str):
    return [f"🚶 {location.name}" for location in get_connected_locations(location_slug)]


def resolve_location_by_move_text(text: str):
    target_name = text.replace("🚶 ", "", 1).strip()
    for location in LOCATIONS.values():
        if location.name == target_name:
            return location
    return None


def get_location_explore_text(location_slug: str):
    location = get_location(location_slug)
    if not location:
        return "Здесь пока нечего исследовать."
    return f"Ты осматриваешь зону: {location.name}. {location.description}"
