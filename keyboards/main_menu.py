from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.location_rules import is_city
from keyboards.city_menu import city_menu


def main_menu(location_slug: str, district_slug: str | None = None):
    if is_city(location_slug):
        return city_menu(district_slug)

    buttons = [
        [KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="🌲 Исследовать"), KeyboardButton(text="🕳 Подземелье")],
        [KeyboardButton(text="📜 Квесты"), KeyboardButton(text="🧾 Сюжет")],
        [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="📂 Ещё")],
        [KeyboardButton(text="🩹 Лечить героя"), KeyboardButton(text="😴 Отдых героя")],
        [KeyboardButton(text="🧭 Перемещение")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
