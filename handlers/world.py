from aiogram.types import Message, FSInputFile

from database.repositories import get_player
from game.world_service import WORLD_OVERVIEW_MAP_PATH, build_world_map_caption
from keyboards.main_menu import main_menu

async def world_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    caption = build_world_map_caption(
        player_level=player.level,
        current_region_slug=player.current_region_slug,
    )

    if WORLD_OVERVIEW_MAP_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(str(WORLD_OVERVIEW_MAP_PATH)),
            caption=caption,
            reply_markup=main_menu(player.location_slug),
        )
        return

    await message.answer(
        caption,
        reply_markup=main_menu(player.location_slug),
    )
