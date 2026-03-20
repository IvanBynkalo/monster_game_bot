"""
Главное меню — v3.1
Вне города: контекстное меню по данным локации.
В городе: city_menu.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.location_rules import is_city
from keyboards.city_menu import city_menu


def main_menu(location_slug: str, district_slug: str | None = None) -> ReplyKeyboardMarkup:
    if is_city(location_slug):
        return city_menu(district_slug)

    # Чистое меню — Собирать и Подземелье теперь в inline под сообщением локации
    keyboard = [
        [KeyboardButton(text="🌲 Исследовать"),  KeyboardButton(text="🧭 Переместиться")],
        [KeyboardButton(text="🐲 Мои монстры"),  KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="👤 Персонаж"),     KeyboardButton(text="📂 Ещё")],
    ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
