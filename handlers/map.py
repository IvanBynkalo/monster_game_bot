from aiogram.types import Message, FSInputFile

from database.repositories import get_player, update_player_location
from game.map_service import (
    WORLD_MAP_PATH,
    build_map_caption,
    render_map_overview,
    render_location_card,
    get_move_commands,
    resolve_location_by_move_text,
)
from keyboards.main_menu import main_menu

async def map_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    caption = build_map_caption(player.location_slug)

    if WORLD_MAP_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(str(WORLD_MAP_PATH)),
            caption=caption,
            reply_markup=main_menu(player.location_slug),
        )
        return

    await message.answer(
        render_map_overview(player.location_slug),
        reply_markup=main_menu(player.location_slug),
    )

async def location_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    await message.answer(
        render_location_card(player.location_slug),
        reply_markup=main_menu(player.location_slug),
    )

async def move_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    target = resolve_location_by_move_text(message.text)
    if not target:
        await message.answer("Не удалось определить локацию для перехода.")
        return

    available_names = set(get_move_commands(player.location_slug))
    if f"🚶 {target.name}" not in available_names:
        await message.answer("Из текущей локации туда пройти нельзя.")
        return

    update_player_location(message.from_user.id, target.slug)
    await message.answer(
        f"🚶 Ты переместился в новую область.\n\n{render_location_card(target.slug)}",
        reply_markup=main_menu(target.slug),
    )
