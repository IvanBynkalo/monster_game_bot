from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def more_menu(is_admin: bool = False):
    keyboard = [
        [KeyboardButton(text="🏙 Город"), KeyboardButton(text="🏪 Магазин")],
        [KeyboardButton(text="🛠 Мастерская"), KeyboardButton(text="📈 Развитие")],
        [KeyboardButton(text="🌍 Мир")],
        [KeyboardButton(text="🗺 Карта"), KeyboardButton(text="📍 Локация")],
        [KeyboardButton(text="🧭 Район"), KeyboardButton(text="❤️ Лечить монстра")],
        [KeyboardButton(text="⚡ Восстановить энергию")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🛠 Админ-панель")])
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
