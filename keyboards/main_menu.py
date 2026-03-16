from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu(location_slug: str):
    buttons = [
        [KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="🧾 Сюжет"), KeyboardButton(text="📜 Квесты")],
        [KeyboardButton(text="🌲 Исследовать"), KeyboardButton(text="🧭 Перемещение")],
        [KeyboardButton(text="🌍 Мир"), KeyboardButton(text="🗺 Карта")],
        [KeyboardButton(text="📍 Локация"), KeyboardButton(text="🧭 Район")],
        [KeyboardButton(text="❤️ Лечить монстра"), KeyboardButton(text="⚡ Восстановить энергию")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
