from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def guilds_menu():
    keyboard = [
        [KeyboardButton(text="🎯 Гильдия ловцов"), KeyboardButton(text="🌿 Гильдия собирателей")],
        [KeyboardButton(text="⛏ Гильдия геологов"), KeyboardButton(text="⚗ Гильдия алхимиков")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
