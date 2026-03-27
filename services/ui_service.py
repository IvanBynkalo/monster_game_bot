from aiogram.types import Message

from database.repositories import get_player
from game.map_service import render_location_card
from game.location_rules import is_city
from game.grid_exploration_service import is_dungeon_available
from keyboards.main_menu import main_menu
from keyboards.location_menu import location_actions_inline
from utils.images import send_location_image


async def show_location_screen(message: Message, user_id: int):
    player = get_player(user_id)
    if not player:
        await message.answer("Ошибка: игрок не найден")
        return

    loc_text = render_location_card(
        player.location_slug,
        telegram_id=user_id,
        current_district_slug=getattr(player, "current_district_slug", None),
    )

    reply_kb = main_menu(
        player.location_slug,
        getattr(player, "current_district_slug", None),
        telegram_id=user_id,
    )

    await send_location_image(
        message,
        player.location_slug,
        loc_text,
        reply_markup=reply_kb,
        district_slug=getattr(player, "current_district_slug", None),
    )

    if not is_city(player.location_slug):
        try:
            from game.dungeon_service import DUNGEONS
            has_dungeon = (
                player.location_slug in DUNGEONS
                and is_dungeon_available(user_id, player.location_slug)
            )
        except Exception:
            has_dungeon = False

        await message.answer(
            "Что будешь делать в этой локации?",
            reply_markup=location_actions_inline(
                player.location_slug,
                has_dungeon=has_dungeon,
            ),
        )
