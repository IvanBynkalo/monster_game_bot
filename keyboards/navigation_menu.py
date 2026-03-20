from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.map_service import get_move_commands, get_connected_locations
from game.district_service import get_district_move_commands
from game.location_rules import is_city, check_location_access


def navigation_menu(location_slug: str, district_slug: str | None = None):
    buttons = []

    if is_city(location_slug):
        for cmd in get_district_move_commands(location_slug):
            buttons.append([KeyboardButton(text=cmd)])

        if district_slug == "main_gate":
            buttons.append([KeyboardButton(text="🚶 Покинуть город")])

        buttons.append([KeyboardButton(text="🗺 Карта")])
    else:
        # Показываем соседние локации с пометкой уровня
        from game.location_rules import LOCATION_REQUIREMENTS, check_location_access
        for location in get_connected_locations(location_slug):
            req = LOCATION_REQUIREMENTS.get(location.slug, {})
            min_lvl = req.get("min_level", 1)
            # Только доступные локации — заблокированные показываем серым текстом
            if min_lvl <= 1:
                cmd = f"🚶 {location.name}"
            else:
                cmd = f"🚶 {location.name} (ур.{min_lvl}+)"
            buttons.append([KeyboardButton(text=cmd)])

        for cmd in get_district_move_commands(location_slug):
            buttons.append([KeyboardButton(text=cmd)])

        buttons.append([KeyboardButton(text="🗺 Карта")])

    buttons.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
