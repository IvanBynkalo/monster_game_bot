DISTRICTS = {

"emerald_fields": [
    {"slug":"green_meadow","name":"🌾 Зелёный луг","mood":"inspiration","danger":1,"description":"Место обилия трав и редких растений."},
    {"slug":"flower_valley","name":"🌸 Цветочная долина","mood":"inspiration","danger":1,"description":"Цветы притягивают редких существ."},
],
"stone_hills": [
    {"slug":"old_mine","name":"⛏ Старая шахта","mood":"instinct","danger":2,"description":"Здесь находят уголь и кристаллы."},
    {"slug":"rock_pass","name":"🪨 Каменный перевал","mood":"instinct","danger":2,"description":"Скалы образуют узкий проход."},
],
"shadow_marsh": [
    {"slug":"fog_pool","name":"🌫 Туманный омут","mood":"fear","danger":2,"description":"Туман скрывает опасных существ."},
    {"slug":"sunken_ruins","name":"🪦 Утопшие руины","mood":"fear","danger":3,"description":"Разрушенные строения древней цивилизации."},
],
    "silver_city": [
        {
            "slug": "market_square",
            "name": "🛒 Рыночная площадь",
            "mood": "inspiration",
            "danger": 0,
            "description": "Центр торговли Сереброграда. Здесь расположены продавцы, сумки, обмен и городские заказы.",
        },
        {
            "slug": "craft_quarter",
            "name": "⚒ Ремесленный квартал",
            "mood": "inspiration",
            "danger": 0,
            "description": "Улицы мастерских и алхимических лавок. Здесь кипит работа над предметами и снаряжением.",
        },
        {
            "slug": "guild_quarter",
            "name": "🏛 Квартал гильдий",
            "mood": "inspiration",
            "danger": 0,
            "description": "Здесь расположены залы городских объединений: ловцов, собирателей, геологов и алхимиков.",
        },
        {
            "slug": "main_gate",
            "name": "🚪 Главные ворота",
            "mood": "instinct",
            "danger": 1,
            "description": "Главный выход из города в дикие земли. Только отсюда стража выпускает путников наружу.",
        },
    ],
    "dark_forest": [
        {"slug": "mushroom_path", "name": "🍄 Тропа грибов", "mood": "fear", "danger": 1, "description": "Узкая тропа среди грибных колец. Здесь легко почувствовать чужое присутствие."},
        {"slug": "wet_thicket", "name": "🌿 Сырая чаща", "mood": "fear", "danger": 2, "description": "Густая зелень и влажный воздух. Тени в чащобе двигаются слишком осмысленно."},
        {"slug": "whisper_den", "name": "👁 Логово шепчущих", "mood": "fear", "danger": 3, "description": "Старые корни образуют круг, из которого доносятся голоса. Здесь часто рождается тревога."},
    ],
    "shadow_swamp": [
        {"slug": "black_water", "name": "🖤 Чёрная вода", "mood": "fear", "danger": 2, "description": "Тёмная гладь воды отражает не тебя, а чужие силуэты."},
        {"slug": "fog_trail", "name": "🌫 Туманная тропа", "mood": "fear", "danger": 2, "description": "Видимость почти нулевая. Каждый шаг звучит громче, чем должен."},
        {"slug": "grave_of_voices", "name": "🪦 Кладбище голосов", "mood": "fear", "danger": 3, "description": "Из ила поднимаются обрывки шёпота. Иногда они зовут монстров по имени."},
    ],
    "volcano_wrath": [
        {"slug": "ash_slope", "name": "🌋 Пепельный склон", "mood": "rage", "danger": 2, "description": "Склон покрыт горячим пеплом, а воздух будто провоцирует на атаку."},
        {"slug": "lava_bridge", "name": "🔥 Лавовый мост", "mood": "rage", "danger": 3, "description": "Под тобой течёт магма. Здесь выживают только те, кто действует без колебаний."},
        {"slug": "heart_of_magma", "name": "❤️ Сердце магмы", "mood": "rage", "danger": 4, "description": "Раскалённое ядро вулкана. Чистая ярость и редкие агрессивные формы."},
    ],
}

MOOD_LABELS = {"rage": "🔥 Ярость", "fear": "😱 Страх", "instinct": "🎯 Инстинкт", "inspiration": "✨ Вдохновение"}

# Порог исследования (%) для открытия района по уровню опасности
DISTRICT_UNLOCK_PCT = {
    0: 0,   # город — всегда открыт
    1: 0,   # начальный район — открыт сразу
    2: 30,  # открывается после 30% исследования
    3: 60,  # открывается после 60% исследования
    4: 85,  # открывается после 85% исследования
}

def get_districts_for_location(location_slug: str):
    return DISTRICTS.get(location_slug, [])


def get_explored_pct(telegram_id: int, location_slug: str) -> int:
    """Возвращает % исследования локации для данного игрока."""
    try:
        from database.repositories import get_connection
        with get_connection() as conn:
            row = conn.execute(
                "SELECT grid_data FROM player_grid_exploration WHERE telegram_id=? AND location_slug=?",
                (telegram_id, location_slug)
            ).fetchone()
        if not row:
            return 0
        import json
        grid = json.loads(row["grid_data"])
        visited = grid.get("visited_count", 0)
        return min(100, int(visited))
    except Exception:
        return 0


def get_district_explored_pct(telegram_id: int, location_slug: str, district_slug: str) -> int:
    """% исследования конкретного района (по его собственному гриду)."""
    try:
        from database.repositories import get_connection
        import json
        key = f"{location_slug}:{district_slug}"
        with get_connection() as conn:
            row = conn.execute(
                "SELECT grid_data FROM player_grid_exploration WHERE telegram_id=? AND location_slug=?",
                (telegram_id, key)
            ).fetchone()
        if not row:
            return 0
        grid = json.loads(row["grid_data"])
        return min(100, int(grid.get("visited_count", 0)))
    except Exception:
        return 0


def get_unlocked_districts(telegram_id: int, location_slug: str) -> list:
    """
    Районы открываются последовательно:
    - danger=1 → всегда открыт (первый район)
    - danger=2 → открывается когда предыдущий район исследован на 30%
    - danger=3 → открывается когда предыдущий район исследован на 50%
    - danger=4 → открывается когда предыдущий район исследован на 70%
    Прогресс считается по гриду ПРЕДЫДУЩЕГО района.
    """
    from game.location_rules import is_city
    if is_city(location_slug):
        return get_districts_for_location(location_slug)

    all_districts = get_districts_for_location(location_slug)
    if not all_districts:
        return []

    # Порог исследования предыдущего района для разблокировки следующего
    PREV_DISTRICT_UNLOCK = {2: 30, 3: 50, 4: 70}

    result = []
    prev_slug = None
    for district in all_districts:
        danger = district.get("danger", 1)
        if danger <= 1:
            # Первый район — всегда открыт
            result.append(district)
            prev_slug = district["slug"]
        else:
            # Следующий район — нужно исследовать предыдущий
            required_pct = PREV_DISTRICT_UNLOCK.get(danger, 30)
            if prev_slug:
                prev_pct = get_district_explored_pct(telegram_id, location_slug, prev_slug)
            else:
                prev_pct = 100
            if prev_pct >= required_pct:
                result.append(district)
                prev_slug = district["slug"]
            else:
                break  # последующие тоже закрыты
    return result

def get_district(location_slug: str, district_slug: str):
    for district in get_districts_for_location(location_slug):
        if district["slug"] == district_slug:
            return district
    return None

def get_default_district_slug(location_slug: str):
    districts = get_districts_for_location(location_slug)
    return districts[0]["slug"] if districts else ""

def get_district_name(location_slug: str, district_slug: str) -> str:
    district = get_district(location_slug, district_slug)
    return district["name"] if district else (district_slug or "не выбран")

def get_district_move_commands(location_slug: str, telegram_id: int = None):
    """Возвращает команды перехода в районы. Если передан telegram_id — только открытые."""
    if telegram_id:
        districts = get_unlocked_districts(telegram_id, location_slug)
    else:
        districts = get_districts_for_location(location_slug)
    return [f"🧭→ {district['name']}" for district in districts]

def resolve_district_by_move_text(location_slug: str, text: str):
    target_name = text.replace("🧭→ ", "", 1).strip()
    for district in get_districts_for_location(location_slug):
        if district["name"] == target_name:
            return district
    return None

def render_district_card(location_slug: str, district_slug: str):
    district = get_district(location_slug, district_slug)
    if not district:
        return "В этой локации районы пока не настроены."
    lines = [
        district["name"],
        f"Эмоция района: {MOOD_LABELS.get(district['mood'], district['mood'])}",
        f"Опасность: {district['danger']}",
        "",
        district["description"],
        "",
        "Доступные районы этой локации:",
    ]
    for item in get_districts_for_location(location_slug):
        marker = "📍" if item["slug"] == district_slug else "▫️"
        lines.append(f"{marker} {item['name']}")
    return "\n".join(lines)

def get_district_explore_text(location_slug: str, district_slug: str):
    district = get_district(location_slug, district_slug)
    if not district:
        return "Ты осматриваешь местность."
    return f"Ты исследуешь район {district['name']}. {district['description']}"
