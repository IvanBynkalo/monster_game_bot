from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.location_rules import is_city


def inventory_menu(inventory: dict | None = None, location_slug: str | None = None):
    inventory = inventory or {}
    keyboard = []

    usable_buttons = []

    if inventory.get("small_potion", 0) > 0:
        usable_buttons.append(KeyboardButton(text="🧪 Малое зелье"))
    if inventory.get("big_potion", 0) > 0:
        usable_buttons.append(KeyboardButton(text="🧪 Большое зелье"))
    if inventory.get("energy_capsule", 0) > 0:
        usable_buttons.append(KeyboardButton(text="⚡ Капсула энергии"))
    if inventory.get("spark_tonic", 0) > 0:
        usable_buttons.append(KeyboardButton(text="✨ Настой искры"))
    if inventory.get("field_elixir", 0) > 0:
        usable_buttons.append(KeyboardButton(text="🌼 Эликсир лугов"))
    if inventory.get("crystal_focus", 0) > 0:
        usable_buttons.append(KeyboardButton(text="💎 Кристальный концентрат"))
    if inventory.get("swamp_antidote", 0) > 0:
        usable_buttons.append(KeyboardButton(text="🪷 Болотный антидот"))

    for i in range(0, len(usable_buttons), 2):
        keyboard.append(usable_buttons[i:i + 2])

    utility_buttons = []

    has_resources = False
    for resource_slug, qty in inventory.items():
        if resource_slug not in {
            "small_potion",
            "big_potion",
            "energy_capsule",
            "spark_tonic",
            "field_elixir",
            "crystal_focus",
            "swamp_antidote",
            "basic_trap",
            "poison_trap",
        } and qty > 0:
            has_resources = True
            break

    if has_resources:
        utility_buttons.append(KeyboardButton(text="📦 Ресурсы"))

    if location_slug and is_city(location_slug):
        utility_buttons.append(KeyboardButton(text="🛠 Мастерская"))

    if utility_buttons:
        keyboard.append(utility_buttons)

    keyboard.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
