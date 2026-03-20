"""
Подменю «Ещё» — второй уровень для полевого меню.
Содержит всё, что не нужно постоянно под рукой.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def more_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🧭 Профиль"),    KeyboardButton(text="📈 Развитие")],
        [KeyboardButton(text="📜 Квесты"),     KeyboardButton(text="🧾 Сюжет")],
        [KeyboardButton(text="❤️ Лечение"),    KeyboardButton(text="🧭 Навигация")],
        [KeyboardButton(text="🛠 Мастерская"), KeyboardButton(text="🔮 Реликвии")],
        [KeyboardButton(text="📖 Кодекс")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🛠 Админ-панель")])
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
