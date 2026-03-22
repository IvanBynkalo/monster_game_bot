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


async def revive_monster_handler(message):
    """Возрождает павшего монстра за золото (только в городе)."""
    from aiogram.types import Message
    from database.repositories import get_player, get_active_monster, revive_monster
    from game.location_rules import is_city
    from keyboards.main_menu import main_menu

    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет монстра для возрождения.")
        return

    if active.get("current_hp", 1) > 0 and not active.get("is_dead"):
        await message.answer("Твой монстр жив — возрождение не нужно.")
        return

    # Стоимость возрождения = 30% от базовой цены монстра (по редкости)
    rarity_costs = {"common": 40, "rare": 100, "epic": 250, "legendary": 600, "mythic": 1500}
    cost = rarity_costs.get(active.get("rarity", "common"), 80)

    if player.gold < cost:
        await message.answer(
            f"💔 Возрождение {active['name']} стоит {cost} золота.\n"
            f"У тебя: {player.gold} золота — недостаточно.\n\n"
            f"Собери ресурсы и продай их у торговца."
        )
        return

    # Возрождаем
    revive_hp = max(1, active["max_hp"] * 30 // 100)
    revive_monster(message.from_user.id, active["id"], revive_hp)
    from database.repositories import _update_player_field
    _update_player_field(message.from_user.id, gold=player.gold - cost)

    await message.answer(
        f"✨ {active['name']} возрождён!\n"
        f"HP: {revive_hp}/{active['max_hp']}\n"
        f"Потрачено: {cost} золота\n\n"
        f"Монстр снова готов к бою!",
        reply_markup=main_menu(player.location_slug, player.current_district_slug)
    )
