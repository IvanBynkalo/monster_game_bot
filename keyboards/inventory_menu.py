from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


ITEM_BUTTONS = {
    "small_potion": "🧪 Малое зелье",
    "big_potion": "🧪 Большое зелье",
    "energy_capsule": "⚡ Капсула энергии",
    "spark_tonic": "✨ Настой искры",
    "field_elixir": "🌼 Эликсир лугов",
    "crystal_focus": "💎 Кристальный концентрат",
    "swamp_antidote": "🪷 Болотный антидот",
}


def inventory_menu(inventory: dict):
    keyboard: list[list[KeyboardButton]] = []
    current_row: list[KeyboardButton] = []

    for slug in [
        "small_potion",
        "big_potion",
        "energy_capsule",
        "spark_tonic",
        "field_elixir",
        "crystal_focus",
        "swamp_antidote",
    ]:
        if inventory.get(slug, 0) <= 0:
            continue

        current_row.append(KeyboardButton(text=ITEM_BUTTONS[slug]))
        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    keyboard.append([KeyboardButton(text="📦 Ресурсы")])
    keyboard.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
