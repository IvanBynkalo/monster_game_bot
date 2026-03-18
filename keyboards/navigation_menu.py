from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.district_service import get_district_move_commands
from game.location_rules import is_city
from game.map_service import get_move_commands


EXIT_CITY_BUTTON = "🚶 Покинуть город"


def navigation_menu(location_slug: str, district_slug: str | None = None):
    rows: list[list[KeyboardButton]] = []

    if is_city(location_slug):
        for cmd in get_district_move_commands(location_slug):
            rows.append([KeyboardButton(text=cmd)])

        if district_slug == "main_gate":
            rows.append([KeyboardButton(text=EXIT_CITY_BUTTON)])
    else:
        for cmd in get_move_commands(location_slug):
            rows.append([KeyboardButton(text=cmd)])

        for cmd in get_district_move_commands(location_slug):
            rows.append([KeyboardButton(text=cmd)])

    if not rows:
        rows.append([KeyboardButton(text="🗺 Карта")])

    rows.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
