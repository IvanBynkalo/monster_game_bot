"""
wildlife_service.py — обычные звери локаций.

Философия:
- Монстры редки и уникальны (эмоциональные сущности).
- Звери — обычные обитатели мира, встречаются часто.
- За победу над зверями: золото, ресурсы, малый опыт.
- Баланс встреч: 60% звери, 35% события, 5% монстры.
"""
import random

# ── Пулы зверей по локациям ───────────────────────────────────────────────────
# weight: чем меньше — тем реже. Сильные звери редкие.

WILDLIFE_BY_LOCATION: dict[str, list[dict]] = {
    "dark_forest": [
        {"name": "Лесная лисица",    "hp": 10, "attack": 3, "weight": 40, "gold": 4,  "exp": 2, "loot": None},
        {"name": "Лесной волк",      "hp": 16, "attack": 5, "weight": 30, "gold": 7,  "exp": 3, "loot": "forest_herb"},
        {"name": "Матёрый волк",     "hp": 24, "attack": 7, "weight": 15, "gold": 12, "exp": 5, "loot": "forest_herb"},
        {"name": "Бурый медведь",    "hp": 36, "attack": 10,"weight": 10, "gold": 20, "exp": 8, "loot": "mushroom_cap"},
        {"name": "Лесной великан",   "hp": 50, "attack": 14,"weight": 5,  "gold": 35, "exp": 12,"loot": "silver_moss"},
    ],
    "emerald_fields": [
        {"name": "Полевая мышь",     "hp": 6,  "attack": 2, "weight": 45, "gold": 2,  "exp": 1, "loot": "field_grass"},
        {"name": "Луговой заяц",     "hp": 10, "attack": 3, "weight": 35, "gold": 4,  "exp": 2, "loot": "field_grass"},
        {"name": "Рогатый олень",    "hp": 22, "attack": 6, "weight": 15, "gold": 10, "exp": 4, "loot": "sun_blossom"},
        {"name": "Степной тур",      "hp": 38, "attack": 11,"weight": 4,  "gold": 22, "exp": 8, "loot": "dew_crystal"},
        {"name": "Золотой орёл",     "hp": 28, "attack": 9, "weight": 1,  "gold": 30, "exp": 10,"loot": "dew_crystal"},
    ],
    "stone_hills": [
        {"name": "Горный суслик",    "hp": 8,  "attack": 2, "weight": 40, "gold": 3,  "exp": 1, "loot": "granite_shard"},
        {"name": "Каменная ящерица", "hp": 14, "attack": 4, "weight": 30, "gold": 6,  "exp": 3, "loot": "granite_shard"},
        {"name": "Горный козёл",     "hp": 20, "attack": 6, "weight": 18, "gold": 10, "exp": 4, "loot": "raw_ore"},
        {"name": "Скальный кабан",   "hp": 32, "attack": 9, "weight": 10, "gold": 18, "exp": 7, "loot": "raw_ore"},
        {"name": "Горный лев",       "hp": 48, "attack": 13,"weight": 2,  "gold": 32, "exp": 11,"loot": "sky_crystal"},
    ],
    "shadow_marsh": [
        {"name": "Болотная жаба",    "hp": 8,  "attack": 3, "weight": 40, "gold": 3,  "exp": 2, "loot": "bog_flower"},
        {"name": "Топяная крыса",    "hp": 12, "attack": 4, "weight": 30, "gold": 5,  "exp": 3, "loot": "bog_flower"},
        {"name": "Болотная змея",    "hp": 20, "attack": 7, "weight": 18, "gold": 10, "exp": 5, "loot": "dark_resin"},
        {"name": "Топяной кабан",    "hp": 30, "attack": 10,"weight": 10, "gold": 16, "exp": 7, "loot": "dark_resin"},
        {"name": "Болотный крокодил","hp": 52, "attack": 15,"weight": 2,  "gold": 38, "exp": 13,"loot": "ghost_reed"},
    ],
    "shadow_swamp": [
        {"name": "Иловый уж",        "hp": 10, "attack": 3, "weight": 40, "gold": 4,  "exp": 2, "loot": "swamp_moss"},
        {"name": "Тёмная выдра",     "hp": 16, "attack": 5, "weight": 30, "gold": 7,  "exp": 3, "loot": "swamp_moss"},
        {"name": "Болотный варан",   "hp": 26, "attack": 8, "weight": 18, "gold": 12, "exp": 5, "loot": "toxic_spore"},
        {"name": "Топяной кабан",    "hp": 34, "attack": 11,"weight": 10, "gold": 18, "exp": 7, "loot": "toxic_spore"},
        {"name": "Болотный крокодил","hp": 54, "attack": 15,"weight": 2,  "gold": 40, "exp": 13,"loot": "black_pearl"},
    ],
    "volcano_wrath": [
        {"name": "Пепельная ящерица","hp": 12, "attack": 4, "weight": 40, "gold": 5,  "exp": 2, "loot": "ash_leaf"},
        {"name": "Лавовый краб",     "hp": 20, "attack": 7, "weight": 28, "gold": 9,  "exp": 4, "loot": "ember_stone"},
        {"name": "Огненная саламандра","hp":30,"attack": 10,"weight": 18, "gold": 15, "exp": 6, "loot": "ember_stone"},
        {"name": "Вулканический волк","hp": 42,"attack": 13,"weight": 12, "gold": 24, "exp": 9, "loot": "magma_core"},
        {"name": "Магматический кабан","hp":60,"attack": 17,"weight": 2,  "gold": 42, "exp": 14,"loot": "magma_core"},
    ],
}

# Локации без зверей (город, руины и т.д.)
_NO_WILDLIFE = {"silver_city", "ancient_ruins", "emotion_rift", "bone_desert", "storm_ridge"}

RARITY_BY_WEIGHT = [
    (40, "Обычный"),
    (25, "Редкий"),
    (5,  "Редкий"),
]


def has_wildlife(location_slug: str) -> bool:
    return location_slug not in _NO_WILDLIFE and location_slug in WILDLIFE_BY_LOCATION


def roll_wildlife(location_slug: str) -> dict | None:
    """
    Бросает кубик — встречается ли зверь.
    Возвращает словарь с параметрами зверя или None.
    """
    pool = WILDLIFE_BY_LOCATION.get(location_slug)
    if not pool:
        return None

    total = sum(a["weight"] for a in pool)
    roll  = random.uniform(0, total)
    cur   = 0
    chosen = None
    for animal in pool:
        cur += animal["weight"]
        if roll <= cur:
            chosen = animal
            break
    if not chosen:
        chosen = pool[0]

    # Вариация HP и ATK ±10%
    hp  = max(1, chosen["hp"]  + random.randint(-2, 2))
    atk = max(1, chosen["attack"] + random.randint(-1, 1))
    gold = chosen["gold"] + random.randint(0, chosen["gold"] // 3)

    # Определяем тип зверя по локации для правильного фолбэка картинки
    _LOCATION_BIOME_TYPE = {
        "dark_forest":    "nature", "shadow_marsh":   "shadow",
        "shadow_swamp":   "void",   "emerald_fields":  "nature",
        "stone_hills":    "bone",   "volcano_wrath":   "flame",
        "ancient_ruins":  "echo",   "storm_ridge":     "storm",
        "bone_desert":    "bone",   "emotion_rift":    "spirit",
    }
    _ANIMAL_TYPE = {
        "Лесная лисица": "nature",  "Лесной волк": "nature",
        "Матёрый волк": "shadow",   "Бурый медведь": "nature",
        "Лесной великан": "nature", "Полевая мышь": "nature",
        "Луговой заяц": "nature",   "Рогатый олень": "spirit",
        "Степной тур": "nature",    "Золотой орёл": "storm",
        "Горный суслик": "bone",    "Каменная ящерица": "bone",
        "Горный козёл": "bone",     "Скальный кабан": "bone",
        "Горный лев": "storm",      "Болотная жаба": "shadow",
        "Топяная крыса": "shadow",  "Болотная змея": "void",
        "Топяной кабан": "shadow",  "Болотный крокодил": "void",
        "Иловый уж": "shadow",      "Тёмная выдра": "shadow",
        "Болотный варан": "void",   "Пепельная ящерица": "flame",
        "Лавовый краб": "flame",    "Огненная саламандра": "flame",
        "Вулканический волк": "flame", "Магматический кабан": "bone",
        "Ветряной заяц": "storm",   "Лепестковый лис": "nature",
        "Златорогий олень": "spirit", "Гранитный зверь": "bone",
        "Чащобный альфа": "nature", "Топный ловчий": "shadow",
    }
    animal_type = _ANIMAL_TYPE.get(chosen["name"],
                  _LOCATION_BIOME_TYPE.get(location_slug, "nature"))

    return {
        "type":          "wildlife",
        "name":          chosen["name"],
        "monster_name":  chosen["name"],
        "monster_type":  animal_type,
        "hp":            hp,
        "max_hp":        hp,
        "attack":        atk,
        "reward_gold":   gold,
        "reward_exp":    chosen["exp"],
        "loot_slug":     chosen.get("loot"),
        "capture_chance":0.0,
        "counter_multiplier": 1.0,
        "bonus_capture": 0.0,
    }


def render_wildlife_encounter(animal: dict) -> str:
    return (
        f"🐾 Ты встречаешь: {animal['name']}\n"
        f"HP: {animal['hp']}/{animal['max_hp']} | ATK: {animal['attack']}\n"
        f"Награда: ~{animal['reward_gold']} золота, {animal['reward_exp']} опыта\n\n"
        f"Выбери действие:"
    )
