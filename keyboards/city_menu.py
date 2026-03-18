from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def city_menu(district_slug: str | None = None):
    keyboard = [
        [KeyboardButton(text="🏪 Торговая лавка"), KeyboardButton(text="📜 Доска заказов")],
        [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="🧭 Профиль")],
        [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="📈 Развитие")],
    ]

    if district_slug == "market_square":
        keyboard.append([KeyboardButton(text="🎒 Лавка сумок"), KeyboardButton(text="🐲 Рынок монстров")])
        keyboard.append([KeyboardButton(text="💰 Скупщик ресурсов")])

    elif district_slug == "craft_quarter":
        keyboard.append([KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")])

    elif district_slug == "guild_quarter":
        keyboard.append([KeyboardButton(text="🎯 Гильдия ловцов"), KeyboardButton(text="🌿 Гильдия собирателей")])
        keyboard.append([KeyboardButton(text="⛏ Гильдия геологов"), KeyboardButton(text="⚗ Гильдия алхимиков")])

    elif district_slug == "main_gate":
        keyboard.append([KeyboardButton(text="🛡 Городская стража"), KeyboardButton(text="🚶 Покинуть город")])

    keyboard.append([KeyboardButton(text="🧭 Район"), KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
