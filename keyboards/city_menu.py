from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def city_menu(district_slug: str | None = None):
    keyboard = [
        [KeyboardButton(text="🏬 Торговый квартал"), KeyboardButton(text="📜 Доска заказов")],
        [KeyboardButton(text="🏛 Гильдии"),           KeyboardButton(text="⚒ Ремесленный квартал")],
        [KeyboardButton(text="🐲 Мои монстры"),        KeyboardButton(text="💎 Кристаллы")],
        [KeyboardButton(text="🎒 Инвентарь"),          KeyboardButton(text="👤 Персонаж")],
        [KeyboardButton(text="⚔️ Экипировка"),         KeyboardButton(text="📂 Ещё")],
        [KeyboardButton(text="🧭 Перемещение"),        KeyboardButton(text="🚶 Покинуть город")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def district_actions_menu(district_slug: str):
    keyboard = [
        [KeyboardButton(text="⬅️ Назад")],
    ]

    if district_slug == "market_square":
        keyboard = [
            [KeyboardButton(text="🎒 Лавка сумок"), KeyboardButton(text="🐲 Рынок монстров")],
            [KeyboardButton(text="🧪 Лавка зелий"),  KeyboardButton(text="💰 Скупщик ресурсов")],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "craft_quarter":
        keyboard = [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "guild_quarter":
        keyboard = [
            [KeyboardButton(text="🎯 Гильдия ловцов"), KeyboardButton(text="🌿 Гильдия собирателей")],
            [KeyboardButton(text="⛏ Гильдия геологов"), KeyboardButton(text="⚗ Гильдия алхимиков")],
            [KeyboardButton(text="🌌 Алтарь рождения")],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "main_gate":
        keyboard = [
            [KeyboardButton(text="🛡 Городская стража"), KeyboardButton(text="🚶 Покинуть город")],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
