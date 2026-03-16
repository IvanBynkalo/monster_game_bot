
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def gather_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧺 Собирать ресурсы")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
