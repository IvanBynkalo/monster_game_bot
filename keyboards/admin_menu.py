from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Выдать золото"), KeyboardButton(text="⚡ Выдать энергию")],
            [KeyboardButton(text="❤️ Вылечить монстров"), KeyboardButton(text="🧹 Сбросить игрока")],
            [KeyboardButton(text="🗺 Телепорт по локации"), KeyboardButton(text="🧭 Телепорт по району")],
            [KeyboardButton(text="❌ Закрыть админ-панель")],
        ],
        resize_keyboard=True,
    )
