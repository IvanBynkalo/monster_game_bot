from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def inventory_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧪 Малое зелье"), KeyboardButton(text="🧪 Большое зелье")],
            [KeyboardButton(text="⚡ Капсула энергии"), KeyboardButton(text="✨ Настой искры")],
            [KeyboardButton(text="🪤 Простая ловушка"), KeyboardButton(text="🪤 Ядовитая ловушка")],
            [KeyboardButton(text="🌼 Эликсир лугов"), KeyboardButton(text="💎 Кристальный концентрат")],
            [KeyboardButton(text="🪷 Болотный антидот")],
            [KeyboardButton(text="📦 Ресурсы"), KeyboardButton(text="🛠 Мастерская")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )
