from aiogram.types import Message

from config import ADMIN_IDS
from database.repositories import get_player, get_ui_screen, set_ui_screen
from game.location_rules import is_city
from keyboards.city_menu import city_menu
from keyboards.main_menu import main_menu
from keyboards.more_menu import more_menu
from keyboards.shop_menu import shop_menu


def _is_admin(user_id: int) -> bool:
    return user_id in set(ADMIN_IDS or [])


async def more_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "more")
    await message.answer("Выбери дополнительное действие.", reply_markup=more_menu(is_admin=_is_admin(message.from_user.id)))


async def back_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    screen = get_ui_screen(message.from_user.id)

    if screen in {"item_shop", "monster_shop", "bag_shop", "sell_shop"}:
        set_ui_screen(message.from_user.id, "shop")
        await message.answer("Возврат в магазин.", reply_markup=shop_menu())
        return

    if screen in {"board", "district", "shop", "craft", "progression", "inventory", "more", "navigation", "city"}:
        set_ui_screen(message.from_user.id, "main")
        if is_city(player.location_slug):
            await message.answer("Главное меню города", reply_markup=city_menu(player.current_district_slug))
        else:
            await message.answer("Главное меню", reply_markup=main_menu(player.location_slug, player.current_district_slug))
        return

    set_ui_screen(message.from_user.id, "main")
    await message.answer("Главное меню", reply_markup=main_menu(player.location_slug, player.current_district_slug))
