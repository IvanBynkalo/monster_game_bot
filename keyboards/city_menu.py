from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def city_menu(district_slug: str):
    rows = []
    mapping = {
        "market_square": [
            [KeyboardButton(text="🏪 Торговая лавка"), KeyboardButton(text="🎒 Лавка сумок")],
            [KeyboardButton(text="🐲 Рынок монстров"), KeyboardButton(text="💰 Скупщик ресурсов")],
            [KeyboardButton(text="📜 Доска заказов")],
        ],
        "craft_quarter": [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")],
        ],
        "guild_quarter": [
            [KeyboardButton(text="🎯 Гильдия ловцов"), KeyboardButton(text="🌿 Гильдия собирателей")],
            [KeyboardButton(text="⛏ Гильдия геологов"), KeyboardButton(text="⚗ Гильдия алхимиков")],
        ],
        "main_gate": [
            [KeyboardButton(text="🚶 Покинуть город"), KeyboardButton(text="🛡 Городская стража")],
        ],
    }
    rows.extend(mapping.get(district_slug, []))
    rows.append([KeyboardButton(text="🧭 Район"), KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
