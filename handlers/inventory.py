from aiogram.types import Message

from database.repositories import (
    get_inventory,
    get_item_count,
    get_player,
    restore_player_energy,
    spend_item,
)
from database.repositories import heal_active_monster
from game.item_service import render_inventory_text
from keyboards.inventory_menu import inventory_menu
from keyboards.main_menu import main_menu

async def inventory_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    inventory = get_inventory(message.from_user.id)
    await message.answer(render_inventory_text(inventory), reply_markup=inventory_menu())

async def use_small_potion_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if get_item_count(message.from_user.id, "small_potion") <= 0:
        await message.answer("🧪 У тебя нет малого зелья.", reply_markup=inventory_menu())
        return
    monster_before = heal_active_monster(message.from_user.id, 0)
    if not monster_before:
        await message.answer("У тебя нет активного монстра.", reply_markup=inventory_menu())
        return
    before_hp = monster_before["current_hp"]
    max_hp = monster_before["max_hp"]
    if before_hp >= max_hp:
        await message.answer("🧪 Активный монстр уже полностью здоров.", reply_markup=inventory_menu())
        return
    spend_item(message.from_user.id, "small_potion", 1)
    monster = heal_active_monster(message.from_user.id, 12)
    healed = monster["current_hp"] - before_hp
    await message.answer(
        f"🧪 Использовано малое зелье.\n"
        f"{monster['name']} восстанавливает {healed} HP.\n"
        f"Текущее HP: {monster['current_hp']}/{monster['max_hp']}",
        reply_markup=inventory_menu(),
    )

async def use_energy_capsule_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if get_item_count(message.from_user.id, "energy_capsule") <= 0:
        await message.answer("⚡ У тебя нет капсулы энергии.", reply_markup=inventory_menu())
        return
    if player.energy >= 12:
        await message.answer("⚡ Энергия уже полная.", reply_markup=inventory_menu())
        return
    spend_item(message.from_user.id, "energy_capsule", 1)
    restore_player_energy(message.from_user.id, 3, max_energy=12)
    await message.answer(
        f"⚡ Использована капсула энергии.\n"
        f"Энергия: {player.energy}/12",
        reply_markup=inventory_menu(),
    )

async def back_to_menu_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer("Главное меню", reply_markup=main_menu(player.location_slug))
