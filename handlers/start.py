from aiogram.types import Message

from database.repositories import get_or_create_player
from game.player_service import ensure_starter_monster
from keyboards.main_menu import main_menu
from game.map_service import render_location_card

async def start_handler(message: Message):
    player, created = get_or_create_player(message.from_user.id, message.from_user.first_name or "Игрок")
    starter_monster, starter_created = ensure_starter_monster(message.from_user.id)

    if created:
        await message.answer(
            "🐲 Добро пожаловать в Monster Emotions.\n"
            "Ты вступаешь в мир, где монстры рождаются из эмоций."
        )

    if starter_created:
        await message.answer(
            f"✨ Ты получаешь стартового монстра: {starter_monster['name']}\n"
            f"Редкость: {starter_monster['rarity']}\n"
            f"Эмоция: {starter_monster['mood']}"
        )

    await message.answer(
        render_location_card(player.location_slug),
        reply_markup=main_menu(player.location_slug),
    )
