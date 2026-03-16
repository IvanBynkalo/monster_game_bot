from aiogram.types import Message
from database.repositories import clear_player_injuries, get_player, heal_player_hp, tick_player_injuries
from keyboards.main_menu import main_menu

async def heal_hero_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.location_slug != "silver_city":
        await message.answer("🩹 Лечиться можно только в Сереброграде.", reply_markup=main_menu(player.location_slug))
        return
    price = 12
    if player.gold < price:
        await message.answer(f"Недостаточно золота. Лечение стоит {price}.", reply_markup=main_menu(player.location_slug))
        return
    if player.hp >= player.max_hp and not player.is_defeated and getattr(player, "injury_turns", 0) <= 0:
        await message.answer("Герой уже полностью здоров.", reply_markup=main_menu(player.location_slug))
        return
    player.gold -= price
    heal_player_hp(message.from_user.id, player.max_hp)
    clear_player_injuries(message.from_user.id)
    await message.answer(
        f"🩹 Герой полностью вылечен.\n❤️ HP героя: {player.hp}/{player.max_hp}\nПотрачено: {price} золота",
        reply_markup=main_menu(player.location_slug),
    )

async def rest_hero_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.location_slug != "silver_city":
        await message.answer("😴 Отдыхать можно только в Сереброграде.", reply_markup=main_menu(player.location_slug))
        return
    tick_player_injuries(message.from_user.id, 2)
    heal_player_hp(message.from_user.id, 6)
    await message.answer(
        f"😴 Герой отдыхает и постепенно восстанавливается.\n"
        f"❤️ HP героя: {player.hp}/{player.max_hp}\n"
        f"🩹 Осталось травм: {player.injury_turns}",
        reply_markup=main_menu(player.location_slug),
    )
