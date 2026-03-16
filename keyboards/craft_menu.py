from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def craft_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧪 Создать: Большое зелье")],
            [KeyboardButton(text="🪤 Создать: Ядовитая ловушка")],
            [KeyboardButton(text="✨ Создать: Настой искры")],
            [KeyboardButton(text="📦 Ресурсы"), KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )
