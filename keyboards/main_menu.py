from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.map_service import get_move_commands
from game.district_service import get_district_move_commands

def main_menu(location_slug: str):
    buttons = [
        [KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="📜 Квесты"), KeyboardButton(text="🌍 Мир")],
        [KeyboardButton(text="🗺 Карта"), KeyboardButton(text="📍 Локация")],
        [KeyboardButton(text="🧭 Район"), KeyboardButton(text="🌲 Исследовать")],
        [KeyboardButton(text="❤️ Лечить монстра"), KeyboardButton(text="⚡ Восстановить энергию")],
    ]

    move_buttons = [KeyboardButton(text=command) for command in get_move_commands(location_slug)]
    for button in move_buttons:
        buttons.append([button])

    district_buttons = [KeyboardButton(text=command) for command in get_district_move_commands(location_slug)]
    for button in district_buttons:
        buttons.append([button])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
