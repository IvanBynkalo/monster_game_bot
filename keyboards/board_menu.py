from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def board_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📌 Взять заказ: Травник")],
            [KeyboardButton(text="📌 Взять заказ: Руда")],
            [KeyboardButton(text="⬅️ Назад в город")],
        ],
        resize_keyboard=True,
    )
