import random
from aiogram.types import Message
from database.repositories import add_item, add_player_experience, add_player_gold, get_player, get_resources, progress_crafting_quests, progress_guild_quests, spend_resource
from game.craft_service import RECIPES, render_craft_text, render_resources_text
from game.location_rules import is_city
from keyboards.craft_menu import craft_menu
from keyboards.main_menu import main_menu

BUTTON_TO_RECIPE = {
    "🧪 Создать: Большое зелье": "big_potion",
    "🪤 Создать: Ядовитая ловушка": "poison_trap",
    "✨ Создать: Настой искры": "spark_tonic",
}

async def craft_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if not is_city(player.location_slug):
        await message.answer("Мастерская и здания работают только в городе.", reply_markup=main_menu(player.location_slug))
        return
    await message.answer(render_craft_text(get_resources(message.from_user.id)), reply_markup=craft_menu())

async def resources_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer(render_resources_text(get_resources(message.from_user.id)), reply_markup=craft_menu())

async def craft_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if not is_city(player.location_slug):
        await message.answer("Создавать предметы можно только в городской мастерской.", reply_markup=main_menu(player.location_slug))
        return
    recipe_id = BUTTON_TO_RECIPE.get((message.text or "").strip())
    if not recipe_id:
        await message.answer("Не удалось определить рецепт.", reply_markup=craft_menu())
        return
    recipe = RECIPES[recipe_id]
    resources = get_resources(message.from_user.id)
    for slug, need in recipe["ingredients"].items():
        if resources.get(slug, 0) < need:
            await message.answer("Недостаточно ресурсов для создания.", reply_markup=craft_menu())
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
    if player.alchemist_level < 5:
        player.alchemist_level += 1

    extras = []
    for quest in progress_crafting_quests(message.from_user.id, recipe_id):
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта")

    guild_done = progress_guild_quests(message.from_user.id, 'craft_any', 1)
    for quest in guild_done:
        add_player_gold(message.from_user.id, quest['reward_gold'])
        add_player_experience(message.from_user.id, quest['reward_exp'])
        extras.append(f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта")
    text = f"{recipe['emoji']} Создан предмет: {recipe['name']} x{amount}" + bonus_text + f"\n⚗ Алхимик: {player.alchemist_level}"
    if extras:
        text += "\n\n" + "\n\n".join(extras)
    await message.answer(text, reply_markup=craft_menu())

async def back_from_craft_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer("Главное меню", reply_markup=main_menu(player.location_slug))
