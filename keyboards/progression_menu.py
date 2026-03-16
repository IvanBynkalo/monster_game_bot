from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def progression_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💪 +Сила"), KeyboardButton(text="🤸 +Ловкость"), KeyboardButton(text="🧠 +Интеллект")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )
