from aiogram.types import Message

from database.repositories import get_player
from keyboards.main_menu import main_menu
from keyboards.more_menu import more_menu

async def more_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer("Выбери дополнительное действие.", reply_markup=more_menu())

async def back_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer("Главное меню", reply_markup=main_menu(player.location_slug))
