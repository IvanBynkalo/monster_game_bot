from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def inventory_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧪 Малое зелье"), KeyboardButton(text="⚡ Капсула энергии")],
            [KeyboardButton(text="🪤 Простая ловушка")],
            [KeyboardButton(text="⬅️ Назад в меню")],
        ],
        resize_keyboard=True,
    )
