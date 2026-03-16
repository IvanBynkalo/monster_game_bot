from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu(location_slug: str):
    buttons = [
        [KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="🌲 Исследовать"), KeyboardButton(text="🔥 Элитная экспедиция")],
        [KeyboardButton(text="🕳 Подземелье"), KeyboardButton(text="📜 Квесты")],
        [KeyboardButton(text="🧾 Сюжет"), KeyboardButton(text="📂 Ещё")],
        [KeyboardButton(text="🩹 Лечить героя"), KeyboardButton(text="😴 Отдых героя")],
        [KeyboardButton(text="🧭 Перемещение")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
