"""
wildlife_loot.py — Лут с зверей.
Таблицы дропа ресурсов и трофеев для всех 28 видов зверей.
"""
import random

# Новые ресурсы-луты (добавляются в item_service)
WILDLIFE_LOOT_ITEMS = {
    # Тёмный лес
    "fox_fur":         {"name": "Рыжий мех",        "emoji": "🦊", "sell_price": 12},
    "wolf_fang":       {"name": "Волчий клык",       "emoji": "🦷", "sell_price": 18},
    "wolf_hide":       {"name": "Волчья шкура",      "emoji": "🐺", "sell_price": 25},
    "bear_hide":       {"name": "Медвежья шкура",    "emoji": "🐻", "sell_price": 45},
    "giant_bark":      {"name": "Великанская кора",  "emoji": "🌲", "sell_price": 80},
    # Изумрудные поля
    "rabbit_pelt":     {"name": "Кроличья шкурка",   "emoji": "🐰", "sell_price": 8},
    "deer_antler":     {"name": "Оленьи рога",        "emoji": "🦌", "sell_price": 30},
    "aurochs_horn":    {"name": "Рог тура",           "emoji": "🐂", "sell_price": 55},
    "eagle_feather":   {"name": "Золотое перо",       "emoji": "🪶", "sell_price": 70},
    "mouse_whisker":   {"name": "Мышиный ус",         "emoji": "🐭", "sell_price": 5},
    # Каменные холмы
    "goat_horn":       {"name": "Козлиный рог",       "emoji": "🐐", "sell_price": 15},
    "boar_tusk":       {"name": "Кабаний клык",       "emoji": "🐗", "sell_price": 22},
    "lynx_claw":       {"name": "Коготь рыси",        "emoji": "🐾", "sell_price": 50},
    "mountain_lion_pelt": {"name": "Шкура горного льва", "emoji": "🦁", "sell_price": 90},
    "stone_beetle":    {"name": "Каменный жук",       "emoji": "🪲", "sell_price": 10},
    # Болота
    "frog_slime":      {"name": "Лягушачья слизь",    "emoji": "🐸", "sell_price": 7},
    "snake_venom":     {"name": "Змеиный яд",         "emoji": "🐍", "sell_price": 35},
    "otter_pelt":      {"name": "Шкурка выдры",       "emoji": "🦦", "sell_price": 20},
    "croc_scale":      {"name": "Чешуя крокодила",    "emoji": "🐊", "sell_price": 65},
    "leech":           {"name": "Болотная пиявка",    "emoji": "🪱", "sell_price": 6},
    # Вулкан
    "fire_lizard_skin":{"name": "Кожа огненной ящерицы","emoji": "🦎", "sell_price": 40},
    "magma_boar_tusk": {"name": "Клык магматического кабана","emoji": "🔥", "sell_price": 85},
    "lava_wolf_fang":  {"name": "Клык лавового волка","emoji": "🌋", "sell_price": 60},
}

# Таблица дропа: зверь → [(item_slug, chance)]
# chance = вероятность от 0.0 до 1.0
WILDLIFE_DROP_TABLE: dict[str, list[tuple[str, float]]] = {
    # Тёмный лес
    "Лесная лисица":       [("fox_fur", 0.65)],
    "Волк":                [("wolf_fang", 0.50), ("wolf_hide", 0.20)],
    "Матёрый волк":        [("wolf_fang", 0.65), ("wolf_hide", 0.40)],
    "Медведь":             [("bear_hide", 0.40), ("wolf_hide", 0.20)],
    "Лесной великан":      [("giant_bark", 0.30), ("bear_hide", 0.25)],
    # Изумрудные поля
    "Полевая мышь":        [("mouse_whisker", 0.70)],
    "Дикий заяц":          [("rabbit_pelt", 0.60)],
    "Молодой олень":       [("deer_antler", 0.40)],
    "Степной тур":         [("aurochs_horn", 0.35), ("deer_antler", 0.30)],
    "Золотой орёл":        [("eagle_feather", 0.25)],
    # Каменные холмы
    "Горный козёл":        [("goat_horn", 0.55)],
    "Дикий кабан":         [("boar_tusk", 0.45)],
    "Горная рысь":         [("lynx_claw", 0.40)],
    "Горный лев":          [("mountain_lion_pelt", 0.25), ("lynx_claw", 0.35)],
    "Каменный жук":        [("stone_beetle", 0.70)],
    # Болота теней
    "Болотная жаба":       [("frog_slime", 0.75)],
    "Уж":                  [("snake_venom", 0.40)],
    "Выдра":               [("otter_pelt", 0.50)],
    "Болотный крокодил":   [("croc_scale", 0.30), ("snake_venom", 0.25)],
    "Болотная пиявка":     [("leech", 0.80)],
    # Болото теней (shadow_swamp)
    "Топяная гадюка":      [("snake_venom", 0.55)],
    "Речная выдра":        [("otter_pelt", 0.60)],
    "Серый крокодил":      [("croc_scale", 0.35)],
    "Трясинный краб":      [("leech", 0.65)],
    # Вулкан ярости
    "Огненная ящерица":    [("fire_lizard_skin", 0.50)],
    "Лавовый волк":        [("lava_wolf_fang", 0.40), ("wolf_fang", 0.30)],
    "Пепельный кабан":     [("boar_tusk", 0.35)],
    "Магматический кабан": [("magma_boar_tusk", 0.25), ("fire_lizard_skin", 0.30)],
    "Горный саламандр":    [("fire_lizard_skin", 0.60)],
}


def roll_wildlife_loot(animal_name: str) -> list[tuple[str, str, int]]:
    """
    Бросает дайс на лут с убитого зверя.
    Возвращает список (item_slug, item_name, amount).
    """
    drops = WILDLIFE_DROP_TABLE.get(animal_name, [])
    result = []
    for slug, chance in drops:
        if random.random() <= chance:
            item = WILDLIFE_LOOT_ITEMS.get(slug, {})
            name = item.get("name", slug)
            result.append((slug, name, 1))
    return result


def get_loot_sell_price(slug: str) -> int:
    return WILDLIFE_LOOT_ITEMS.get(slug, {}).get("sell_price", 5)
