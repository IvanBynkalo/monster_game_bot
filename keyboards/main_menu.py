"""
Главное меню — v3.1
Вне города: 4 кнопки максимум (исследовать, монстры, инвентарь, ещё).
В городе: без изменений (city_menu).
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.location_rules import is_city
from keyboards.city_menu import city_menu


def main_menu(location_slug: str, district_slug: str | None = None) -> ReplyKeyboardMarkup:
    if is_city(location_slug):
        return city_menu(district_slug)

    # Вне города — минимальное меню, всё вторичное через "Ещё"
    keyboard = [
        [KeyboardButton(text="🌲 Исследовать"), KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="🎒 Инвентарь"),   KeyboardButton(text="📂 Ещё")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
