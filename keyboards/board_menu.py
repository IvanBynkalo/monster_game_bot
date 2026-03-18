from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def board_menu(has_active_order: bool = False):
    keyboard = []

    if not has_active_order:
        keyboard.append([KeyboardButton(text="📌 Взять заказ: Травник")])
        keyboard.append([KeyboardButton(text="📌 Взять заказ: Руда")])

    keyboard.append([KeyboardButton(text="📒 Мои заказы")])
    keyboard.append([KeyboardButton(text="⬅️ Назад в город")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
