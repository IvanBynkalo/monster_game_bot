from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def city_menu(district_slug: str | None = None):
    keyboard = [
        [KeyboardButton(text="🏪 Торговая лавка"), KeyboardButton(text="📜 Доска заказов")],
        [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="🧭 Профиль")],
        [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="📈 Развитие")],
    ]

    district_actions = {
        "market_square": [
            [KeyboardButton(text="💰 Скупщик ресурсов"), KeyboardButton(text="🧭 Район")],
        ],
        "craft_quarter": [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")],
        ],
        "guild_quarter": [
            [KeyboardButton(text="🎯 Гильдии"), KeyboardButton(text="🧭 Район")],
        ],
        "main_gate": [
            [KeyboardButton(text="🛡 Городская стража"), KeyboardButton(text="🚶 Покинуть город")],
        ],
    }

    if district_slug == "craft_quarter":
        keyboard.append([KeyboardButton(text="🧭 Район"), KeyboardButton(text="⬅️ Назад")])
    elif district_slug == "main_gate":
        keyboard.append([KeyboardButton(text="🧭 Район"), KeyboardButton(text="⬅️ Назад")])
    elif district_slug == "guild_quarter":
        keyboard.append([KeyboardButton(text="🧭 Район"), KeyboardButton(text="⬅️ Назад")])
    else:
        keyboard.append([KeyboardButton(text="💰 Скупщик ресурсов"), KeyboardButton(text="🧭 Район")])
        keyboard.append([KeyboardButton(text="⬅️ Назад")])

    if district_slug == "craft_quarter":
        keyboard.insert(3, [KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")])
    elif district_slug == "guild_quarter":
        keyboard.insert(3, [KeyboardButton(text="🎯 Гильдия ловцов"), KeyboardButton(text="🌿 Гильдия собирателей")])
        keyboard.insert(4, [KeyboardButton(text="⛏ Гильдия геологов"), KeyboardButton(text="⚗ Гильдия алхимиков")])
    elif district_slug == "main_gate":
        keyboard.insert(3, [KeyboardButton(text="🛡 Городская стража"), KeyboardButton(text="🚶 Покинуть город")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
