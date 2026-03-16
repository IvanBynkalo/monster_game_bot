from aiogram.types import Message

from config import ADMIN_IDS
from database.repositories import get_player
from keyboards.main_menu import main_menu
from keyboards.more_menu import more_menu

def _is_admin(user_id: int) -> bool:
    return user_id in set(ADMIN_IDS or [])

async def more_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer("Выбери дополнительное действие.", reply_markup=more_menu(is_admin=_is_admin(message.from_user.id)))

async def back_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer("Главное меню", reply_markup=main_menu(player.location_slug))
