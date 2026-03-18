from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.craft_service import RECIPES, get_craftable_recipe_ids, make_recipe_button


def craft_menu(player, resources: dict):
    keyboard = []

    for recipe_id in get_craftable_recipe_ids(player, resources):
        recipe = RECIPES[recipe_id]
        keyboard.append([KeyboardButton(text=make_recipe_button(recipe))])

    keyboard.append([KeyboardButton(text="📦 Ресурсы"), KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
