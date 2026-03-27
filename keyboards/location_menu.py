"""
Inline-меню действий в локации.
Показывается в карточке локации — не засоряет reply-keyboard.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from game.gather_service import has_gathering_in_location


BIRTH_LOCATION_SLUGS = {"silver_city", "emotion_rift"}

def location_actions_inline(location_slug: str, has_dungeon: bool = False) -> InlineKeyboardMarkup:
    """
    Компактное inline-меню действий в текущей локации.
    Только для полевых локаций — в городе не показывается.
    """
    from game.location_rules import is_city
    if is_city(location_slug):
        # В городе это меню не нужно
        return InlineKeyboardMarkup(inline_keyboard=[])

    rows = []

    # Исследовать + Собирать в одном ряду
    explore_row = [InlineKeyboardButton(text="🌲 Исследовать", callback_data="loc:explore")]
    if has_gathering_in_location(location_slug):
        explore_row.append(InlineKeyboardButton(text="🧺 Собирать", callback_data="loc:gather"))
    rows.append(explore_row)

    # Подземелье
    if has_dungeon:
        rows.append([InlineKeyboardButton(text="🕳 Подземелье", callback_data="loc:dungeon")])

    # Смена района — если в локации есть несколько районов
    try:
        from game.district_service import get_districts_for_location
        districts = get_districts_for_location(location_slug)
        if len(districts) > 1:
            rows.append([InlineKeyboardButton(text="🧭 Сменить район", callback_data="loc:district")])
    except Exception:
        pass

    # Карта / Перемещение
    rows.append([InlineKeyboardButton(text="🗺 Карта / Перемещение", callback_data="loc:navigate")])

    # Ритуал рождения — только в Разломе эмоций (не в городе)
    if location_slug == "emotion_rift":
        rows.append([InlineKeyboardButton(text="🌌 Ритуал рождения", callback_data="loc:birth")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def district_inline_menu(district_slug: str) -> InlineKeyboardMarkup | None:
    """
    Inline-кнопки для активностей внутри района локации.
    Возвращает None если для района нет особых действий.
    """
    district_actions = {
        "mushroom_path":  [("🍄 Исследовать тропу", "loc:explore"), ("🧺 Собирать", "loc:gather")],
        "black_water":    [("🌊 Исследовать", "loc:explore"),        ("🧺 Собирать", "loc:gather")],
        "ash_slope":      [("🔥 Исследовать", "loc:explore")],
        "wind_garden":    [("💨 Исследовать", "loc:explore"),        ("🧺 Собирать", "loc:gather")],
        "crystal_shelf":  [("💎 Исследовать", "loc:explore"),        ("🧺 Собирать", "loc:gather")],
        "reed_maze":      [("🌾 Исследовать", "loc:explore"),        ("🧺 Собирать", "loc:gather")],
        "green_meadow":   [("🌿 Исследовать", "loc:explore"),        ("🧺 Собирать", "loc:gather")],
        "stone_quarry":   [("⛏ Исследовать", "loc:explore"),        ("🧺 Добывать", "loc:gather")],
    }
    actions = district_actions.get(district_slug)
    if not actions:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d)] for t, d in actions]
    )
