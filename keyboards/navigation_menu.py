from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from game.map_service import get_move_commands
from game.district_service import get_district_move_commands

def navigation_menu(location_slug: str):
    buttons = [
        [KeyboardButton(text="🌲 Исследовать"), KeyboardButton(text="🧭 Профиль")],
        [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="🗺 Карта")],
        [KeyboardButton(text="📍 Локация"), KeyboardButton(text="🧭 Район")],
    ]
    for cmd in get_move_commands(location_slug):
        buttons.append([KeyboardButton(text=cmd)])
    for cmd in get_district_move_commands(location_slug):
        buttons.append([KeyboardButton(text=cmd)])
    buttons.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
