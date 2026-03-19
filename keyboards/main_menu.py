from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.gather_service import has_gathering_in_location
from game.location_rules import is_city
from keyboards.city_menu import city_menu


def main_menu(location_slug: str, district_slug: str | None = None):
    if is_city(location_slug):
        return city_menu(district_slug)

    buttons = [
        [KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="📈 Развитие")],
        [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="🌲 Исследовать"), KeyboardButton(text="🕳 Подземелье")],
    ]

    if has_gathering_in_location(location_slug):
        buttons.append([KeyboardButton(text="🧺 Собирать ресурсы")])

    buttons.extend([
        [KeyboardButton(text="📜 Квесты"), KeyboardButton(text="🧾 Сюжет")],
        [KeyboardButton(text="🩹 Лечить героя"), KeyboardButton(text="😴 Отдых героя")],
        [KeyboardButton(text="❤️ Лечить монстра"), KeyboardButton(text="⚡ Восстановить энергию")],
        [KeyboardButton(text="🧭 Навигация"), KeyboardButton(text="🗺 Карта")],
    ])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )
