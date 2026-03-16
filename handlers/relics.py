from aiogram.types import Message
from database.repositories import get_player, get_player_relics
from game.relic_service import render_relics
from keyboards.main_menu import main_menu

async def relics_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    relics = get_player_relics(message.from_user.id)
    await message.answer(render_relics(relics), reply_markup=main_menu(player.location_slug))
