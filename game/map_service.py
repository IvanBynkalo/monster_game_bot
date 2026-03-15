from pathlib import Path
from database.models import Location

LOCATIONS = {
    "dark_forest": Location(
        slug="dark_forest",
        name="🌲 Тёмный лес",
        mood="fear",
        biome="forest",
        description="Сырая чаща, где тревога и шёпот деревьев подпитывают страх."
    ),
    "volcano_wrath": Location(
        slug="volcano_wrath",
        name="🔥 Вулкан ярости",
        mood="rage",
        biome="volcano",
        description="Трещины земли дышат жаром. Здесь эмоции легко превращаются в ярость."
    ),
    "shadow_swamp": Location(
        slug="shadow_swamp",
        name="🌫 Болото теней",
        mood="fear",
        biome="swamp",
        description="Туман скрывает движения, а тени будто наблюдают за каждым шагом."
    ),
    "bone_desert": Location(
        slug="bone_desert",
        name="🏜 Пустыня костей",
        mood="instinct",
        biome="desert",
        description="Суровая земля проверяет выживших. Здесь просыпается хищный инстинкт."
    ),
    "ancient_ruins": Location(
        slug="ancient_ruins",
        name="🏛 Древние руины",
        mood="inspiration",
        biome="ruins",
        description="Старые символы и забытые залы наполняют разум вдохновением."
    ),
    "emotion_rift": Location(
        slug="emotion_rift",
        name="🌌 Разлом эмоций",
        mood="inspiration",
        biome="rift",
        description="Нестабильная зона, где чувства обретают форму быстрее обычного."
    ),
    "storm_ridge": Location(
        slug="storm_ridge",
        name="🏔 Хребет бурь",
        mood="rage",
        biome="mountains",
        description="Штормы и удары молний закаляют волю и будят внутренний гнев."
    ),
}

TRAVEL_GRAPH = {
    "dark_forest": ["shadow_swamp", "ancient_ruins"],
    "shadow_swamp": ["dark_forest", "emotion_rift"],
    "ancient_ruins": ["dark_forest", "bone_desert", "emotion_rift"],
    "bone_desert": ["ancient_ruins", "volcano_wrath", "storm_ridge"],
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

def get_connected_locations(location_slug: str):
    return [LOCATIONS[slug] for slug in TRAVEL_GRAPH.get(location_slug, [])]

def render_map_overview(current_slug: str) -> str:
    lines = ["🗺 Карта мира:", ""]
    for slug, location in LOCATIONS.items():
        marker = "📍" if slug == current_slug else "▫️"
        lines.append(f"{marker} {location.name} — {MOOD_LABELS[location.mood]}")
    return "\n".join(lines)

def render_location_card(location_slug: str) -> str:
    location = get_location(location_slug)
    neighbors = get_connected_locations(location_slug)

    lines = [
        f"{location.name}",
        f"Биом: {location.biome}",
        f"Эмоция локации: {MOOD_LABELS[location.mood]}",
        "",
        location.description,
        "",
        "Переходы:"
    ]
    for item in neighbors:
        lines.append(f"— {item.name}")
    return "\n".join(lines)

def build_map_caption(current_slug: str) -> str:
    location = get_location(current_slug)
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
    neighbors = get_connected_locations(location_slug)
    return [f"🚶 {location.name}" for location in neighbors]

def resolve_location_by_move_text(text: str):
    target_name = text.replace("🚶 ", "", 1).strip()
    for location in LOCATIONS.values():
        if location.name == target_name:
            return location
    return None

def get_location_explore_text(location_slug: str) -> str:
    location = get_location(location_slug)
    biome_messages = {
        "forest": "Под ногами хрустит листва. Вдалеке слышится рык неизвестного существа.",
        "volcano": "Воздух обжигает лёгкие. Магма пульсирует, будто отвечает на твой гнев.",
        "swamp": "Туман стелется по воде. Кажется, кто-то движется рядом, но не показывается.",
        "desert": "Горячий ветер несёт песок. Здесь выживают только те, у кого сильный инстинкт.",
        "ruins": "Каменные арки покрыты знаками. Здесь легко найти следы древней силы.",
        "rift": "Воздух дрожит. Эмоции словно материализуются прямо в пространстве.",
        "mountains": "Гром гремит над вершинами. Шторм делает каждый шаг испытанием."
    }
    return f"{location.name}\n\n{biome_messages.get(location.biome, 'Ты исследуешь окрестности.')}"
