from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def more_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌍 Мир"), KeyboardButton(text="🗺 Карта")],
            [KeyboardButton(text="📍 Локация"), KeyboardButton(text="🧭 Район")],
            [KeyboardButton(text="❤️ Лечить монстра"), KeyboardButton(text="⚡ Восстановить энергию")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )
