from aiogram.types import Message
from database.repositories import get_player
from game.story_service import render_story_screen
from keyboards.main_menu import main_menu

async def story_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer(render_story_screen(message.from_user.id), reply_markup=main_menu(player.location_slug))
