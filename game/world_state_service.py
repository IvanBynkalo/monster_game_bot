import random

WEATHER_BY_LOCATION = {
    "dark_forest": [
        {"id": "mist", "name": "🌫 Лесной туман", "text": "Туман стелется между деревьями и скрывает следы.", "capture_bonus": 0.04, "danger_bonus": 1},
        {"id": "spore_rain", "name": "🍄 Споровый дождь", "text": "Мелкие споры оседают на листве. Редкие травы встречаются чаще.", "rare_resource_bonus": 0.06, "danger_bonus": 0},
    ],
    "emerald_fields": [
        {"id": "golden_wind", "name": "💨 Золотой ветер", "text": "Ветер помогает заметить движение в высокой траве.", "capture_bonus": 0.08, "danger_bonus": 0},
        {"id": "warm_sun", "name": "☀ Тёплое солнце", "text": "Солнечный день помогает дольше держаться в экспедиции.", "energy_relief": 1, "danger_bonus": 0},
    ],
    "stone_hills": [
        {"id": "crystal_echo", "name": "💎 Хрустальный резонанс", "text": "Кристаллы звенят под ветром, открывая скрытые жилы.", "rare_resource_bonus": 0.08, "danger_bonus": 1},
        {"id": "rock_dust", "name": "🪨 Каменная пыль", "text": "Пыль затрудняет обзор и делает поход опаснее.", "capture_bonus": -0.03, "danger_bonus": 2},
    ],
    "shadow_swamp": [
        {"id": "black_fog", "name": "🌫 Чёрный туман", "text": "Туман прячет не только угрозы, но и редкие находки.", "rare_resource_bonus": 0.05, "danger_bonus": 2},
    ],
    "shadow_marsh": [
        {"id": "marsh_lights", "name": "🕯 Болотные огни", "text": "Блуждающие огни ведут к редким тайникам и страшным хищникам.", "rare_resource_bonus": 0.07, "danger_bonus": 2},
    ],
    "volcano_wrath": [
        {"id": "ash_storm", "name": "🌋 Пепельная буря", "text": "Горячий пепел режет кожу и мешает охоте.", "capture_bonus": -0.05, "danger_bonus": 2},
    ],
}

ELITE_EXPEDITIONS = {
    "dark_forest": {
        "title": "🌲 Элитная экспедиция: Сердце чащи",
        "description": "Очень опасный маршрут. Здесь чаще появляются редкие хищники и тайники.",
        "cost_energy": 2,
        "encounter_bonus": "elite_forest",
    },
    "stone_hills": {
        "title": "⛰ Элитная экспедиция: Глубинная жила",
        "description": "Маршрут для геологов и охотников за реликвиями. Высокий риск.",
        "cost_energy": 2,
        "encounter_bonus": "elite_hills",
    },
    "shadow_marsh": {
        "title": "🕸 Элитная экспедиция: Мёртвый омут",
        "description": "Почти самоубийственный поход за редкими болотными материалами.",
        "cost_energy": 2,
        "encounter_bonus": "elite_marsh",
    },
}

def roll_weather(location_slug: str):
    pool = WEATHER_BY_LOCATION.get(location_slug, [])
    if not pool:
        return None
    return random.choice(pool).copy()

def get_elite_expedition(location_slug: str):
    item = ELITE_EXPEDITIONS.get(location_slug)
    return item.copy() if item else None
