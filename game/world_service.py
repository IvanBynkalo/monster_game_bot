from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORLD_OVERVIEW_MAP_PATH = BASE_DIR / "assets" / "world_overview_map.png"

REGIONS = [
    {
        "slug": "valley_of_emotions",
        "name": "Долина Эмоций",
        "theme": "Стартовый регион. Базовые эмоции, первые заражения и первые эволюции.",
        "unlock_level": 1,
    },
    {
        "slug": "ashen_belt",
        "name": "Пепельный Пояс",
        "theme": "Регион ярости, войны и огненных мутаций.",
        "unlock_level": 6,
    },
    {
        "slug": "silent_marshes",
        "name": "Безмолвные Топи",
        "theme": "Туман, страх, теневые существа и скрытые угрозы.",
        "unlock_level": 10,
    },
    {
        "slug": "instinct_steppes",
        "name": "Степи Инстинкта",
        "theme": "Охота, стаи, альфа-формы и выживание.",
        "unlock_level": 14,
    },
    {
        "slug": "dreamer_ruins",
        "name": "Руины Сновидцев",
        "theme": "Вдохновение, древние знания и редкие эфирные эволюции.",
        "unlock_level": 18,
    },
    {
        "slug": "fracture_ridge",
        "name": "Хребет Раскола",
        "theme": "Стихийные разломы и опасные смешанные заражения.",
        "unlock_level": 22,
    },
    {
        "slug": "mirror_void",
        "name": "Зеркальная Пустота",
        "theme": "Отражения, копии монстров и искажённые формы.",
        "unlock_level": 26,
    },
    {
        "slug": "heart_of_world",
        "name": "Сердце Мира",
        "theme": "Поздний эндгейм и источник эмоциональной катастрофы.",
        "unlock_level": 30,
    },
]

def get_region(region_slug: str):
    for region in REGIONS:
        if region["slug"] == region_slug:
            return region
    return None

def get_unlocked_regions(player_level: int):
    return [region for region in REGIONS if player_level >= region["unlock_level"]]

def build_world_map_caption(player_level: int, current_region_slug: str) -> str:
    lines = [
        "🌍 Эхо-Мир",
        "",
        "Глобальная карта мира. Сейчас открыт не весь континент — новые регионы открываются постепенно.",
        "",
        f"Текущий уровень игрока: {player_level}",
        "",
        "Регионы:",
    ]

    for region in REGIONS:
        is_current = region["slug"] == current_region_slug
        unlocked = player_level >= region["unlock_level"]

        if is_current:
            prefix = "📍"
        elif unlocked:
            prefix = "🟢"
        else:
            prefix = "🔒"

        level_note = f"(ур. {region['unlock_level']}+)"
        lines.append(f"{prefix} {region['name']} {level_note}")
        if unlocked or is_current:
            lines.append(f"   {region['theme']}")

    return "\n".join(lines)
