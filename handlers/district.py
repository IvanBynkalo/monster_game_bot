from aiogram.types import Message

from database.repositories import get_player, update_player_district
from game.district_service import (
    get_district_move_commands,
    render_district_card,
    resolve_district_by_move_text,
)
from keyboards.main_menu import main_menu

async def district_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    text = render_district_card(player.location_slug, player.current_district_slug)
    await message.answer(
        text,
        reply_markup=main_menu(player.location_slug),
    )

async def district_move_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    district = resolve_district_by_move_text(player.location_slug, message.text)
    if not district:
        await message.answer("Для этой локации такой район не найден.")
        return

    update_player_district(message.from_user.id, district["slug"])
    await message.answer(
        f"🧭 Ты переместился в район.\n\n{render_district_card(player.location_slug, district['slug'])}",
        reply_markup=main_menu(player.location_slug),
    )
