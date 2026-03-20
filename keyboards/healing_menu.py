"""
Подменю лечения — третий уровень.
Все действия по восстановлению героя и монстра в одном месте.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def healing_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🩹 Лечить героя"),          KeyboardButton(text="❤️ Лечить монстра")],
        [KeyboardButton(text="😴 Отдых героя"),            KeyboardButton(text="⚡ Восстановить энергию")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
