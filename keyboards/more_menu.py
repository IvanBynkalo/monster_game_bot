"""
keyboards/more_menu.py

Подменю «🐲 Герой» — всё что касается персонажа и его характеристик.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def more_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Меню раздела «Герой» — монстры, инвентарь, экипировка, персонаж и сервис.
    """
    keyboard = [
        [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="💎 Кристаллы")],
        [KeyboardButton(text="🎒 Инвентарь"),   KeyboardButton(text="⚔️ Экипировка")],
        [KeyboardButton(text="👤 Персонаж"),     KeyboardButton(text="❤️ Лечение")],
        [KeyboardButton(text="🔮 Реликвии"),     KeyboardButton(text="🔔 Уведомления")],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="🛠 Админ-панель")])

    keyboard.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def quests_nav_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Меню раздела «Задания» — все квесты и активности.
    """
    keyboard = [
        [KeyboardButton(text="📜 Квесты"),       KeyboardButton(text="🧾 Сюжет")],
        [KeyboardButton(text="📅 Сегодня"),      KeyboardButton(text="🎯 Охота недели")],
        [KeyboardButton(text="📋 Доска заказов")],
    ]
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
