from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def city_menu(district_slug: str | None = None):
    keyboard = [
        [KeyboardButton(text="🏪 Торговая лавка"), KeyboardButton(text="📜 Доска заказов")],
        [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="🧭 Профиль")],
        [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="📈 Развитие")],
    ]

    district_actions = {
        "market_square": [
            [KeyboardButton(text="🎒 Лавка сумок"), KeyboardButton(text="🐲 Рынок монстров")],
            [KeyboardButton(text="💰 Скупщик ресурсов")],
        ],
        "craft_quarter": [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")],
        ],
        "guild_quarter": [
            [KeyboardButton(text="🎯 Гильдия ловцов"), KeyboardButton(text="🌿 Гильдия собирателей")],
            [KeyboardButton(text="⛏ Гильдия геологов"), KeyboardButton(text="⚗ Гильдия алхимиков")],
        ],
        "main_gate": [
            [KeyboardButton(text="🛡 Городская стража"), KeyboardButton(text="🚶 Покинуть город")],
        ],
    }

    keyboard.extend(district_actions.get(district_slug, []))

    if district_slug != "main_gate":
        keyboard.append([KeyboardButton(text="🛡 Городская стража")])

    keyboard.append([KeyboardButton(text="🧭 Район"), KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
