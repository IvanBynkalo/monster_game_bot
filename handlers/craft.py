import random

from aiogram.types import Message

from database.repositories import (
    add_item,
    add_player_experience,
    add_player_gold,
    get_player,
    get_resources,
    progress_crafting_quests,
    progress_guild_quests,
    set_ui_screen,
    spend_resource,
improve_profession_from_action,
)
from game.craft_service import (
    RECIPES,
    can_craft_recipe_now,
    get_recipe_id_by_button_text,
    has_recipe_resources,
    meets_alchemy_requirement,
    render_craft_text,
    render_resources_text,
)
from game.location_rules import is_city
from keyboards.craft_menu import craft_menu
from keyboards.main_menu import main_menu


async def craft_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not is_city(player.location_slug):
        await message.answer(
            "Мастерская и здания работают только в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "craft")

    await message.answer(
        render_craft_text(player, resources),
        reply_markup=craft_menu(player, resources),
    )


async def resources_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "craft")

    await message.answer(
        render_resources_text(resources),
        reply_markup=craft_menu(player, resources),
    )


async def craft_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not is_city(player.location_slug):
        await message.answer(
            "Создавать предметы можно только в городской мастерской.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    recipe_id = get_recipe_id_by_button_text(message.text)
    if not recipe_id:
        resources = get_resources(message.from_user.id)
        await message.answer(
            "Не удалось определить рецепт.",
            reply_markup=craft_menu(player, resources),
        )
        return

    recipe = RECIPES[recipe_id]

    if player.level < recipe.get("hero_level", 1):
        resources = get_resources(message.from_user.id)
        await message.answer(
            "Этот рецепт ещё не открыт для твоего уровня героя.",
            reply_markup=craft_menu(player, resources),
        )
        return

    if not meets_alchemy_requirement(player, recipe):
        resources = get_resources(message.from_user.id)
        await message.answer(
            f"⚗ Недостаточный уровень алхимии.\n"
            f"Нужно: {recipe['alchemy_level']}\n"
            f"Сейчас: {player.alchemist_level}",
            reply_markup=craft_menu(player, resources),
        )
        return

    resources = get_resources(message.from_user.id)
    if not has_recipe_resources(resources, recipe):
        await message.answer(
            "Недостаточно ресурсов для создания.",
            reply_markup=craft_menu(player, resources),
        )
        return

    if not can_craft_recipe_now(player, resources, recipe):
        await message.answer(
            "Сейчас этот предмет создать нельзя.",
            reply_markup=craft_menu(player, resources),
        )
        return

    for slug, need in recipe["ingredients"].items():
        spend_resource(message.from_user.id, slug, need)

    amount = recipe["result_amount"]
    bonus_text = ""

    craft_bonus = 0.05 * max(0, player.alchemist_level - 1) + 0.03 * max(0, player.intellect - 1)
    if random.random() < min(0.35, craft_bonus):
        amount += 1
        bonus_text = "\n⚗ Благодаря навыкам алхимика удалось создать дополнительный экземпляр."

        add_item(message.from_user.id, recipe["result_item"], amount)
    profession_gain = improve_profession_from_action(message.from_user.id, "alchemist", 2)

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

    updated_resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "craft")

        profession_text = ""
    if profession_gain:
        if profession_gain.get("is_max_level"):
            profession_text = "\n⚗ Алхимик: максимальный уровень."
        elif profession_gain.get("leveled_up"):
            profession_text = f"\n🎉 ⚗ Алхимик повышен до {profession_gain['level_after']} уровня!"
        else:
            profession_text = f"\n⚗ Алхимик: +{profession_gain['gained_exp']} опыта ({profession_gain['exp_after']}/{profession_gain['exp_to_next']})"

    text = f"{recipe['emoji']} Создан предмет: {recipe['name']} x{amount}" + bonus_text + profession_text

    if extras:
        text += "\n\n" + "\n\n".join(extras)

    await message.answer(
        text,
        reply_markup=craft_menu(player, updated_resources),
    )


async def back_from_craft_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    set_ui_screen(message.from_user.id, "main")
    await message.answer(
        "Главное меню",
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
    )
