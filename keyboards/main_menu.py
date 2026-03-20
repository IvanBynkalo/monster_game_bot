"""
Главное меню — v3.1
Вне города: контекстное меню по данным локации.
В городе: city_menu.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.location_rules import is_city
from game.gather_service import has_gathering_in_location
from game.dungeon_service import DUNGEONS
from keyboards.city_menu import city_menu


def main_menu(location_slug: str, district_slug: str | None = None) -> ReplyKeyboardMarkup:
    if is_city(location_slug):
        return city_menu(district_slug)

    keyboard = [
        [KeyboardButton(text="🌲 Исследовать"),  KeyboardButton(text="🧭 Переместиться")],
        [KeyboardButton(text="🐲 Мои монстры"),  KeyboardButton(text="🎒 Инвентарь")],
    ]

    # Сбор ресурсов — только там где есть
    if has_gathering_in_location(location_slug):
        keyboard.append([KeyboardButton(text="🧺 Собирать ресурсы")])

    # Подземелье — только там где есть
    if location_slug in DUNGEONS:
        keyboard.append([KeyboardButton(text="🕳 Подземелье")])

    keyboard.append([KeyboardButton(text="👤 Персонаж"), KeyboardButton(text="📂 Ещё")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
