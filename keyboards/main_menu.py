from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu(location_slug: str):
    buttons = [
        [KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="🌲 Исследовать"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="🧾 Сюжет"), KeyboardButton(text="📜 Квесты")],
        [KeyboardButton(text="🧭 Перемещение"), KeyboardButton(text="📂 Ещё")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
