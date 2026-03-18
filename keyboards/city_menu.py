from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def city_menu():
    keyboard = [
        [KeyboardButton(text="🏬 Торговый квартал"), KeyboardButton(text="📜 Доска заказов")],
        [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="🧭 Профиль")],
        [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="📈 Развитие")],
        [KeyboardButton(text="🧭 Район"), KeyboardButton(text="🧭 Перемещение")],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def district_actions_menu(district_slug: str):
    if district_slug == "market_square":
        keyboard = [
            [KeyboardButton(text="🧪 Магазин предметов"), KeyboardButton(text="🎒 Лавка сумок")],
            [KeyboardButton(text="🐲 Рынок монстров"), KeyboardButton(text="💰 Скупщик ресурсов")],
            [KeyboardButton(text="🧭 Район"), KeyboardButton(text="🧭 Перемещение")],
            [KeyboardButton(text="⬅️ Назад в город")],
        ]
    elif district_slug == "craft_quarter":
        keyboard = [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")],
            [KeyboardButton(text="🧭 Район"), KeyboardButton(text="🧭 Перемещение")],
            [KeyboardButton(text="⬅️ Назад в город")],
        ]
    elif district_slug == "guild_quarter":
        keyboard = [
            [KeyboardButton(text="🎯 Гильдия ловцов"), KeyboardButton(text="🌿 Гильдия собирателей")],
            [KeyboardButton(text="⛏ Гильдия геологов"), KeyboardButton(text="⚗ Гильдия алхимиков")],
            [KeyboardButton(text="🧭 Район"), KeyboardButton(text="🧭 Перемещение")],
            [KeyboardButton(text="⬅️ Назад в город")],
        ]
    elif district_slug == "main_gate":
        keyboard = [
            [KeyboardButton(text="🛡 Городская стража"), KeyboardButton(text="🚶 Покинуть город")],
            [KeyboardButton(text="🧭 Район"), KeyboardButton(text="🧭 Перемещение")],
            [KeyboardButton(text="⬅️ Назад в город")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="🧭 Район"), KeyboardButton(text="🧭 Перемещение")],
            [KeyboardButton(text="⬅️ Назад в город")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
