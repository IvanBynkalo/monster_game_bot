import random

from aiogram.types import Message

from database.repositories import (
    add_item,
    add_player_experience,
    add_player_gold,
    get_player,
    get_resources,
    improve_profession_from_action,
    progress_crafting_quests,
    progress_guild_quests,
    spend_resource,
)
from game.craft_service import (
    can_craft_recipe,
    get_recipe_by_button,
    render_craft_text,
    render_resources_text,
)
from game.location_rules import is_city
from keyboards.craft_menu import craft_menu
from keyboards.main_menu import main_menu
from keyboards.city_menu import district_actions_menu


def _craft_markup(player_id: int):
    player = get_player(player_id)
    resources = get_resources(player_id)
    return craft_menu(player, resources)


async def craft_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not is_city(player.location_slug):
        await message.answer(
            "Мастерская и лаборатория работают только в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    resources = get_resources(message.from_user.id)
    await message.answer(
        render_craft_text(player, resources),
        reply_markup=craft_menu(player, resources),
    )


async def resources_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    await message.answer(
        render_resources_text(get_resources(message.from_user.id)),
        reply_markup=_craft_markup(message.from_user.id),
    )


async def craft_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not is_city(player.location_slug):
        await message.answer(
            "Создавать предметы можно только в городской лаборатории.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    recipe_id, recipe = get_recipe_by_button(message.text or "")
    if not recipe:
        await message.answer("Не удалось определить рецепт.", reply_markup=_craft_markup(message.from_user.id))
        return

    if player.alchemist_level < recipe["min_alchemist_level"]:
        await message.answer(
            f"⚗ Для этого рецепта нужен уровень алхимика {recipe['min_alchemist_level']}.",
            reply_markup=_craft_markup(message.from_user.id),
        )
        return

    resources = get_resources(message.from_user.id)
    if not can_craft_recipe(recipe, resources):
        await message.answer(
            "Недостаточно ресурсов для создания.",
            reply_markup=_craft_markup(message.from_user.id),
        )
        return

    for slug, need in recipe["ingredients"].items():
        spend_resource(message.from_user.id, slug, need)

    amount = recipe["result_amount"]
    bonus_text = ""

    craft_bonus = 0.05 * max(0, player.alchemist_level - 1) + 0.03 * max(0, player.intellect - 1)
    if random.random() < min(0.40, craft_bonus):
        amount += 1
        bonus_text = "\n⚗ Благодаря мастерству алхимика получилось создать дополнительный экземпляр."

    add_item(message.from_user.id, recipe["result_item"], amount)
    improve_profession_from_action(message.from_user.id, "alchemist", 1)

    updated_player = get_player(message.from_user.id)

    extras = []

    for quest in progress_crafting_quests(message.from_user.id, recipe_id):
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )

    guild_done = progress_guild_quests(message.from_user.id, "craft_any", 1)
    for quest in guild_done:
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )

    text = (
        f"{recipe['emoji']} Создан предмет: {recipe['name']} x{amount}"
        f"{bonus_text}\n"
        f"⚗ Алхимик: {updated_player.alchemist_level}"
    )

    if extras:
        text += "\n\n" + "\n\n".join(extras)

    await message.answer(
        text,
        reply_markup=_craft_markup(message.from_user.id),
    )


async def back_from_craft_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if player.location_slug == "silver_city" and player.current_district_slug == "craft_quarter":
        await message.answer(
            "Возвращаемся в ремесленный квартал.",
            reply_markup=district_actions_menu("craft_quarter"),
        )
        return

    await message.answer(
        "Главное меню",
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
    )
