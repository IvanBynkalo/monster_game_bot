"""
Замки прогрессии по локациям — теперь реально применяются (рекомендация #9).
"""

CITY_SLUG = "silver_city"

SHOP_LOCATIONS = {
    "silver_city": {"has_shop": True, "shop_name": "🏪 Торговые ряды Сереброграда"},
}

# Требования для входа в локацию
LOCATION_REQUIREMENTS: dict[str, dict] = {
    # slug → {min_level, min_monsters, story_quest}
    "dark_forest":    {"min_level": 1},
    "emerald_fields": {"min_level": 1},
    "stone_hills":    {"min_level": 2},
    "shadow_swamp":   {"min_level": 3},
    "shadow_marsh":   {"min_level": 3},
    "ancient_ruins":  {"min_level": 5},
    "bone_desert":    {"min_level": 6,  "min_monsters": 3},
    "volcano_wrath":  {"min_level": 8,  "story_quest": "swamp_sign"},
    "storm_ridge":    {"min_level": 10, "min_monsters": 5},
    "emotion_rift":   {"min_level": 12, "story_quest": "volcano_trial"},
}

# Описание локаций для сообщений об ошибке
LOCATION_LOCK_MESSAGES: dict[str, str] = {
    "stone_hills":   "Каменные холмы опасны — нужен хотя бы 2-й уровень.",
    "shadow_swamp":  "Болото теней требует опыта — нужен 3-й уровень.",
    "shadow_marsh":  "Болота теней — только для опытных охотников (уровень 3+).",
    "ancient_ruins": "Руины хранят тайны для исследователей 5-го уровня и выше.",
    "bone_desert":   "Пустыня костей — только для уровня 6+ с командой монстров.",
    "volcano_wrath": "Вулкан ярости закрыт. Сначала завершите квест «Тени у воды».",
    "storm_ridge":   "Хребет бурь — только для легендарных охотников (уровень 10+).",
    "emotion_rift":  "Разлом эмоций открывается лишь избранным (уровень 12+, квест завершён).",
}


def has_shop(location_slug: str) -> bool:
    return SHOP_LOCATIONS.get(location_slug, {}).get("has_shop", False)


def get_shop_name(location_slug: str) -> str:
    return SHOP_LOCATIONS.get(location_slug, {}).get("shop_name", "Лавка")


def is_city(location_slug: str) -> bool:
    return location_slug == CITY_SLUG


def check_location_access(player, location_slug: str, completed_story_ids: list[str] | None = None) -> tuple[bool, str]:
    """
    Проверяет, может ли игрок войти в локацию.
    Возвращает (allowed: bool, reason: str).
    """
    req = LOCATION_REQUIREMENTS.get(location_slug)
    if not req:
        return True, ""

    # Проверка уровня
    min_level = req.get("min_level", 1)
    if player.level < min_level:
        msg = LOCATION_LOCK_MESSAGES.get(location_slug,
              f"Нужен {min_level}-й уровень для входа в эту локацию.")
        return False, f"🔒 {msg}\nТвой уровень: {player.level} / нужно: {min_level}"

    # Проверка минимального количества монстров
    min_monsters = req.get("min_monsters", 0)
    if min_monsters > 0:
        from database.repositories import get_player_monsters
        count = len(get_player_monsters(player.telegram_id))
        if count < min_monsters:
            msg = LOCATION_LOCK_MESSAGES.get(location_slug,
                  f"Нужно иметь минимум {min_monsters} монстров.")
            return False, f"🔒 {msg}\nУ тебя монстров: {count} / нужно: {min_monsters}"

    # Проверка сюжетного квеста
    story_quest = req.get("story_quest")
    if story_quest and completed_story_ids is not None:
        if story_quest not in completed_story_ids:
            msg = LOCATION_LOCK_MESSAGES.get(location_slug,
                  "Сначала нужно завершить определённый квест.")
            return False, f"🔒 {msg}"

    return True, ""


def get_available_locations(player, completed_story_ids: list[str] | None = None) -> list[tuple[str, bool]]:
    """Возвращает список (slug, is_available) всех локаций."""
    from game.map_service import LOCATIONS
    result = []
    for slug in LOCATIONS:
        if slug == CITY_SLUG:
            result.append((slug, True))
            continue
        allowed, _ = check_location_access(player, slug, completed_story_ids)
        result.append((slug, allowed))
    return result
