from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def encounter_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ Атаковать"), KeyboardButton(text="✨ Навык")],
            [KeyboardButton(text="🎯 Поймать"), KeyboardButton(text="🪤 Ловушка")],
            [KeyboardButton(text="🏃 Убежать")],
        ],
        resize_keyboard=True,
    )
