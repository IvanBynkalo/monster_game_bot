from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.craft_service import can_craft_recipe, get_unlocked_recipes, recipe_button_text


def craft_menu(player, resources: dict):
    keyboard = []

    ready_buttons = []
    not_ready_buttons = []

    for _, recipe in get_unlocked_recipes(player.alchemist_level):
        button = KeyboardButton(text=recipe_button_text(recipe))
        if can_craft_recipe(recipe, resources):
            ready_buttons.append(button)
        else:
            not_ready_buttons.append(button)

    for button in ready_buttons:
        keyboard.append([button])

    for button in not_ready_buttons:
        keyboard.append([button])

    keyboard.append([KeyboardButton(text="📦 Ресурсы"), KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
