from aiogram.types import Message
from database.repositories import (
    get_inventory,
    get_item_count,
    get_player,
    restore_player_energy,
    set_temp_effect,
    set_ui_screen,
    spend_item,
    heal_active_monster,
)
from game.item_service import render_inventory_text
from keyboards.inventory_menu import inventory_menu
from keyboards.main_menu import main_menu

async def inventory_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "inventory")
    await message.answer(render_inventory_text(get_inventory(message.from_user.id)), reply_markup=inventory_menu())

async def use_small_potion_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if get_item_count(message.from_user.id, "small_potion") <= 0:
        await message.answer("🧪 У тебя нет малого зелья.", reply_markup=inventory_menu())
        return
    if player.hp >= player.max_hp:
        await message.answer("❤️ Здоровье уже полное.", reply_markup=inventory_menu())
        return
    spend_item(message.from_user.id, "small_potion", 1)
    heal_active_monster(message.from_user.id, 8)
    await message.answer(f"🧪 Использовано малое зелье.\n❤️ HP: {player.hp}/{player.max_hp}", reply_markup=inventory_menu())

async def use_big_potion_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if get_item_count(message.from_user.id, "big_potion") <= 0:
        await message.answer("🧪 У тебя нет большого зелья.", reply_markup=inventory_menu())
        return
    if player.hp >= player.max_hp:
        await message.answer("❤️ Здоровье уже полное.", reply_markup=inventory_menu())
        return
    spend_item(message.from_user.id, "big_potion", 1)
    heal_active_monster(message.from_user.id, 16)
    await message.answer(f"🧪 Использовано большое зелье.\n❤️ HP: {player.hp}/{player.max_hp}", reply_markup=inventory_menu())

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
    restore_player_energy(message.from_user.id, 6, max_energy=12)
    await message.answer(f"⚡ Использована капсула энергии.\nЭнергия: {player.energy}/12", reply_markup=inventory_menu())

async def use_spark_tonic_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if get_item_count(message.from_user.id, "spark_tonic") <= 0:
        await message.answer("✨ У тебя нет настоя искры.", reply_markup=inventory_menu())
        return
    if player.energy >= 12:
        await message.answer("✨ Энергия уже полная.", reply_markup=inventory_menu())
        return
    spend_item(message.from_user.id, "spark_tonic", 1)
    restore_player_energy(message.from_user.id, 5, max_energy=12)
    await message.answer(f"✨ Использован настой искры.\nЭнергия: {player.energy}/12", reply_markup=inventory_menu())

async def use_field_elixir_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if get_item_count(message.from_user.id, "field_elixir") <= 0:
        await message.answer("🌼 У тебя нет эликсира лугов.", reply_markup=inventory_menu())
        return
    spend_item(message.from_user.id, "field_elixir", 1)
    set_temp_effect(message.from_user.id, "field_capture", 3)
    await message.answer(
        "🌼 Эликсир лугов использован.\n"
        "Следующие 3 исследования дадут бонус к поимке и помогут в полях.",
        reply_markup=inventory_menu(),
    )

async def use_crystal_focus_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if get_item_count(message.from_user.id, "crystal_focus") <= 0:
        await message.answer("💎 У тебя нет кристального концентрата.", reply_markup=inventory_menu())
        return
    spend_item(message.from_user.id, "crystal_focus", 1)
    restore_player_energy(message.from_user.id, 4, max_energy=12)
    set_temp_effect(message.from_user.id, "crystal_skin", 3)
    await message.answer(
        f"💎 Концентрат использован.\nЭнергия: {player.energy}/12\n"
        "Следующие 3 исследования будут безопаснее в каменных и жарких зонах.",
        reply_markup=inventory_menu(),
    )

async def use_swamp_antidote_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if get_item_count(message.from_user.id, "swamp_antidote") <= 0:
        await message.answer("🪷 У тебя нет болотного антидота.", reply_markup=inventory_menu())
        return
    spend_item(message.from_user.id, "swamp_antidote", 1)
    set_temp_effect(message.from_user.id, "swamp_guard", 3)
    await message.answer(
        "🪷 Ты используешь болотный антидот.\n"
        "Следующие 3 исследования в болотах будут безопаснее.",
        reply_markup=inventory_menu(),
    )

async def back_to_menu_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "main")
    await message.answer("Главное меню", reply_markup=main_menu(player.location_slug, player.current_district_slug))
