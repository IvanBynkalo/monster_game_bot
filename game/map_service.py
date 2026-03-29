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

# Оставлено для совместимости со старым кодом.
# Источником правды теперь считаем game.location_rules.LOCATION_REQUIREMENTS
LOCATION_LEVEL_REQUIREMENT = {
    "silver_city": 1,
    "dark_forest": 1,
    "emerald_fields": 1,
    "stone_hills": 2,
    "shadow_marsh": 3,
    "shadow_swamp": 3,
    "ancient_ruins": 5,
    "bone_desert": 6,
    "volcano_wrath": 8,
    "storm_ridge": 10,
    "emotion_rift": 12,
}

TRAVEL_GRAPH = {
    "silver_city": ["dark_forest"],
    "dark_forest": ["silver_city", "emerald_fields", "shadow_marsh"],
    "emerald_fields": ["dark_forest", "stone_hills"],
    "shadow_marsh": ["dark_forest", "shadow_swamp"],
    "stone_hills": ["emerald_fields", "ancient_ruins"],
    "shadow_swamp": ["shadow_marsh", "bone_desert"],
    "ancient_ruins": ["stone_hills", "bone_desert"],
    "bone_desert": ["shadow_swamp", "ancient_ruins", "volcano_wrath"],
    "volcano_wrath": ["bone_desert", "storm_ridge"],
    "storm_ridge": ["volcano_wrath", "emotion_rift"],
    "emotion_rift": ["storm_ridge"],
}

MOOD_LABELS = {
    "rage": "🔥 Ярость",
    "fear": "😱 Страх",
    "instinct": "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение",
}

STARTER_LOCATIONS = {"silver_city", "dark_forest", "emerald_fields"}

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
        lines.append(f"{marker} {location.name} — {MOOD_LABELS.get(location.mood, location.mood)}")
    return "\n".join(lines)


def _get_player(telegram_id: int | None):
    if not telegram_id:
        return None
    try:
        from database.repositories import get_player
        return get_player(telegram_id)
    except Exception:
        return None


def _get_completed_story_ids(telegram_id: int | None) -> list[str]:
    if not telegram_id:
        return []
    try:
        from database.repositories import get_player_story
        story = get_player_story(telegram_id)
        return story.get("completed_ids", []) if story else []
    except Exception:
        return []


def _is_location_discovered(telegram_id: int | None, location_slug: str) -> bool:
    """
    Локация известна если посещена или видна как сосед.
    Читает из player_location_visibility (отдельная таблица).
    """
    if location_slug in STARTER_LOCATIONS:
        return True
    if not telegram_id:
        return True

    try:
        from database.repositories import get_connection
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM player_location_visibility WHERE telegram_id=? AND location_slug=?",
                (telegram_id, location_slug),
            ).fetchone()

        if not row:
            return False

        if isinstance(row, tuple):
            return row[0] > 0

        return row["cnt"] > 0
    except Exception:
        return True


def _format_transition_line(location, player=None, completed_ids: list[str] | None = None, telegram_id: int | None = None) -> str:
    discovered = _is_location_discovered(telegram_id, location.slug)

    if not discovered and location.slug not in STARTER_LOCATIONS:
        return "— ❓ Неизведанная территория"

    if player is None:
        from game.location_rules import LOCATION_REQUIREMENTS
        req = LOCATION_REQUIREMENTS.get(location.slug, {})
        min_lvl = req.get("min_level", 1)
        if min_lvl > 1:
            return f"— {location.name} (ур.{min_lvl}+)"
        return f"— {location.name}"

    from game.location_rules import check_location_access, LOCATION_REQUIREMENTS

    allowed, _ = check_location_access(player, location.slug, completed_ids or [])
    req = LOCATION_REQUIREMENTS.get(location.slug, {})
    min_lvl = req.get("min_level", 1)

    if allowed:
        return f"— {location.name}"

    if min_lvl > 1:
        return f"— 🔒 {location.name} (ур.{min_lvl}+)"
    return f"— 🔒 {location.name}"


def _build_district_section(location_slug: str, current_district_slug: str | None = None, telegram_id: int | None = None) -> list[str]:
    try:
        from game.district_service import (
            get_district,
            get_districts_for_location,
            get_unlocked_districts,
            MOOD_LABELS as DISTRICT_MOOD_LABELS,
        )
    except Exception:
        return []

    all_districts = get_districts_for_location(location_slug)
    if not all_districts:
        return []

    current_district = get_district(location_slug, current_district_slug) if current_district_slug else None

    lines: list[str] = []

    if current_district:
        lines.extend([
            "",
            "Текущий район:",
            current_district["name"],
            f"Эмоция района: {DISTRICT_MOOD_LABELS.get(current_district['mood'], current_district['mood'])}",
            f"Опасность: {current_district['danger']}",
            "",
            current_district["description"],
        ])

    lines.extend([
        "",
        "Доступные районы этой локации:",
    ])

    if telegram_id:
        visible_districts = get_unlocked_districts(telegram_id, location_slug)
        visible_slugs = {d["slug"] for d in visible_districts}
    else:
        visible_districts = all_districts
        visible_slugs = {d["slug"] for d in all_districts}

    for district in all_districts:
        marker = "📍" if district["slug"] == current_district_slug else "▫️"

        if district["slug"] in visible_slugs:
            lines.append(f"{marker} {district['name']}")
        else:
            # Показываем % исследования ПРЕДЫДУЩЕГО района для разблокировки
            danger = district.get("danger", 1)
            PREV_UNLOCK = {2: 30, 3: 50, 4: 70}
            required_pct = PREV_UNLOCK.get(danger, 30)
            # Находим предыдущий район
            prev_pct = 0
            if telegram_id:
                try:
                    from game.district_service import get_district_explored_pct
                    district_idx = all_districts.index(district)
                    if district_idx > 0:
                        prev_district = all_districts[district_idx - 1]
                        prev_pct = get_district_explored_pct(
                            telegram_id, location_slug, prev_district["slug"]
                        )
                        prev_name = prev_district["name"]
                    else:
                        prev_name = "района"
                except Exception:
                    prev_name = "района"
            lines.append(
                f"{marker} 🔒 {district['name']} "
                f"(исследуй предыдущий район: {prev_pct}%/{required_pct}%)"
            )

    return lines


def render_location_card(
    location_slug: str,
    telegram_id: int | None = None,
    current_district_slug: str | None = None,
) -> str:
    location = get_location(location_slug)
    if not location:
        return "Локация не найдена."

    neighbors = get_connected_locations(location_slug)
    player = _get_player(telegram_id)
    completed_ids = _get_completed_story_ids(telegram_id)

    lines = [
        location.name,
        f"Тип местности: {location.biome}",
        f"Эмоция локации: {MOOD_LABELS.get(location.mood, location.mood)}",
        "",
        location.description,
        "",
        "Переходы:",
    ]

    if neighbors:
        for item in neighbors:
            lines.append(
                _format_transition_line(
                    item,
                    player=player,
                    completed_ids=completed_ids,
                    telegram_id=telegram_id,
                )
            )
    else:
        lines.append("— Нет доступных переходов")

    district_lines = _build_district_section(
        location_slug,
        current_district_slug=current_district_slug,
        telegram_id=telegram_id,
    )
    if district_lines:
        lines.extend(district_lines)

    return "\n".join(lines)


def build_map_caption(current_slug: str, telegram_id: int | None = None) -> str:
    location = get_location(current_slug)
    if not location:
        return "🗺 Визуальная карта мира"

    neighbors = get_connected_locations(current_slug)
    player = _get_player(telegram_id)
    completed_ids = _get_completed_story_ids(telegram_id)

    lines = [
        "🗺 Визуальная карта мира",
        "",
        f"Сейчас ты находишься: {location.name}",
        f"Доминирующая эмоция зоны: {MOOD_LABELS.get(location.mood, location.mood)}",
        "",
        "Доступные переходы:",
    ]

    if neighbors:
        for item in neighbors:
            discovered = _is_location_discovered(telegram_id, item.slug)
            if not discovered and item.slug not in STARTER_LOCATIONS:
                lines.append("• ❓ Неизведанная территория")
                continue

            if player:
                allowed, _ = check_location_access(player, item.slug, completed_ids)
            else:
                from game.location_rules import LOCATION_REQUIREMENTS
                req = LOCATION_REQUIREMENTS.get(item.slug, {})
                allowed = req.get("min_level", 1) <= 1

            if allowed:
                lines.append(f"• {item.name}")
            else:
                from game.location_rules import LOCATION_REQUIREMENTS
                req = LOCATION_REQUIREMENTS.get(item.slug, {})
                min_lvl = req.get("min_level", 1)
                lines.append(f"• 🔒 {item.name} (ур.{min_lvl}+)")
    else:
        lines.append("• Нет соседних локаций")

    return "\n".join(lines)


def get_move_commands(location_slug: str):
    return [f"🚶 {location.name}" for location in get_connected_locations(location_slug)]


def resolve_location_by_move_text(text: str):
    cleaned = (text or "").strip()
    prefixes = ("🚶 ", "🔒 ", "Перейти: ")
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned.replace(prefix, "", 1).strip()

    if " (ур." in cleaned:
        cleaned = cleaned.split(" (ур.", 1)[0].strip()

    for location in LOCATIONS.values():
        if location.name == cleaned:
            return location
    return None


def get_location_explore_text(location_slug: str):
    location = get_location(location_slug)
    if not location:
        return "Здесь пока нечего исследовать."
    return f"Ты осматриваешь зону: {location.name}. {location.description}"
