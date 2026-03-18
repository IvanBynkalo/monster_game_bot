from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def board_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Взять: Заказ травника")],
            [KeyboardButton(text="✅ Взять: Нужна руда для печей")],
            [KeyboardButton(text="⬅️ Назад в город")],
        ],
        resize_keyboard=True,
    )
