from aiogram.types import Message
from database.repositories import get_or_create_player
from game.player_service import ensure_starter_monster
from keyboards.main_menu import main_menu
from game.map_service import render_location_card
from utils.logger import log_event

async def start_handler(message: Message):
    player, created = get_or_create_player(message.from_user.id, message.from_user.first_name or "Игрок")
    starter_monster, starter_created = ensure_starter_monster(message.from_user.id)

    if created:
        log_event("player_created", message.from_user.id, f"name={player.name}")
        await message.answer("🐲 Добро пожаловать в Monster Emotions.\nТы вступаешь в мир, где монстры рождаются из эмоций.")
        await message.answer("🧾 Пролог\nПроводник Эйр просит начать с Тёмного леса. Прислушайся к шёпоту деревьев и найди источник искажения.")

    if starter_created:
        log_event("starter_monster_granted", message.from_user.id, starter_monster["name"])
        await message.answer(f"✨ Ты получаешь стартового монстра: {starter_monster['name']}\nРедкость: {starter_monster['rarity']}\nЭмоция: {starter_monster['mood']}")

    await message.answer(render_location_card(player.location_slug), reply_markup=main_menu(player.location_slug))
