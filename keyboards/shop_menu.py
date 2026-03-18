from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧪 Магазин предметов"), KeyboardButton(text="🐲 Магазин монстров")],
            [KeyboardButton(text="🎒 Сумки"), KeyboardButton(text="💰 Продать ресурсы")],
            [KeyboardButton(text="⬅️ Назад в район")],
        ],
        resize_keyboard=True,
    )


def item_shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить: Малое зелье"), KeyboardButton(text="🛒 Купить: Капсула энергии")],
            [KeyboardButton(text="🛒 Купить: Простая ловушка")],
            [KeyboardButton(text="⬅️ Назад в район")],
        ],
        resize_keyboard=True,
    )


def monster_shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить монстра: Лесной спрайт")],
            [KeyboardButton(text="🛒 Купить монстра: Болотный охотник")],
            [KeyboardButton(text="🛒 Купить монстра: Угольный клык")],
            [KeyboardButton(text="⬅️ Назад в район")],
        ],
        resize_keyboard=True,
    )


def bag_shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить сумку: Поясная сумка")],
            [KeyboardButton(text="🛒 Купить сумку: Полевой ранец")],
            [KeyboardButton(text="🛒 Купить сумку: Экспедиционный рюкзак")],
            [KeyboardButton(text="⬅️ Назад в район")],
        ],
        resize_keyboard=True,
    )


def sell_menu(resources: dict):
    keyboard = []
    labels = {
        "forest_herb": "🌿 Лесная трава",
        "mushroom_cap": "🍄 Шляпка гриба",
        "silver_moss": "✨ Серебряный мох",
        "swamp_moss": "🪴 Болотный мох",
        "toxic_spore": "🧫 Токсичная спора",
        "black_pearl": "⚫ Чёрная жемчужина тины",
        "ember_stone": "🔥 Угольный камень",
        "ash_leaf": "🍂 Пепельный лист",
        "magma_core": "💠 Ядро магмы",
        "field_grass": "🌾 Полевая трава",
        "sun_blossom": "🌼 Солнечный цветок",
        "dew_crystal": "💧 Кристалл росы",
        "raw_ore": "⛏ Сырая руда",
        "granite_shard": "🪨 Осколок гранита",
        "sky_crystal": "💎 Небесный кристалл",
        "bog_flower": "🪷 Болотный цветок",
        "dark_resin": "🕯 Тёмная смола",
        "ghost_reed": "🎐 Призрачный камыш",
    }

    for slug, qty in resources.items():
        if qty > 0:
            keyboard.append([KeyboardButton(text=f"💰 Продать: {labels.get(slug, slug)}")])

    keyboard.append([KeyboardButton(text="⬅️ Назад в район")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
