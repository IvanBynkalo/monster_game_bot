from aiogram.types import Message, FSInputFile

from database.repositories import get_player, update_player_location, update_story_progress
from game.map_service import (
    WORLD_MAP_PATH,
    build_map_caption,
    render_map_overview,
    render_location_card,
    get_move_commands,
    resolve_location_by_move_text,
)
from game.story_service import apply_story_reward
from keyboards.main_menu import main_menu
from keyboards.navigation_menu import navigation_menu, EXIT_CITY_BUTTON


CITY_EXIT_TARGET = "dark_forest"


def _normalize_move_text(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("Перейти: "):
        return "🚶 " + text.replace("Перейти: ", "", 1)
    return text


async def navigation_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer(
        "Выбери переход по области или району.",
        reply_markup=navigation_menu(player.location_slug, player.current_district_slug),
    )


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
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return
    await message.answer(
        render_map_overview(player.location_slug),
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
    )


async def location_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer(
        render_location_card(player.location_slug),
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
    )


async def move_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    text = (message.text or "").strip()

    if text == "⬅️ Назад":
        await message.answer(
            "Главное меню",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    if text == EXIT_CITY_BUTTON:
        if player.location_slug != "silver_city":
            await message.answer(
                "Эта кнопка работает только в городе.",
                reply_markup=main_menu(player.location_slug, player.current_district_slug),
            )
            return

        if player.current_district_slug != "main_gate":
            await message.answer(
                "Покинуть город можно только через район 🚪 Главные ворота.",
                reply_markup=main_menu(player.location_slug, player.current_district_slug),
            )
            return

        update_player_location(message.from_user.id, CITY_EXIT_TARGET)
        story_done = update_story_progress(message.from_user.id, "move", CITY_EXIT_TARGET)

        response_text = (
            "🚶 Ты покинул Сереброград через главные ворота.\n\n"
            f"{render_location_card(CITY_EXIT_TARGET)}"
        )
        if story_done:
            response_text += "\n\n" + apply_story_reward(message.from_user.id, story_done)

        await message.answer(response_text, reply_markup=main_menu(CITY_EXIT_TARGET, None))
        return

    normalized = _normalize_move_text(message.text)
    target = resolve_location_by_move_text(normalized)
    if not target:
        await message.answer(
            "Не удалось определить локацию для перехода.",
            reply_markup=navigation_menu(player.location_slug, player.current_district_slug),
        )
        return

    available_names = set(get_move_commands(player.location_slug))
    if f"🚶 {target.name}" not in available_names:
        await message.answer(
            "Из текущей локации туда пройти нельзя.",
            reply_markup=navigation_menu(player.location_slug, player.current_district_slug),
        )
        return

    if (
        player.location_slug == "silver_city"
        and player.current_district_slug != "main_gate"
        and target.slug != "silver_city"
    ):
        await message.answer(
            "Покинуть город можно только через район 🚪 Главные ворота.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    update_player_location(message.from_user.id, target.slug)
    story_done = update_story_progress(message.from_user.id, "move", target.slug)

    response_text = f"🚶 Ты переместился в новую область.\n\n{render_location_card(target.slug)}"
    if story_done:
        response_text += "\n\n" + apply_story_reward(message.from_user.id, story_done)

    await message.answer(response_text, reply_markup=main_menu(target.slug, None))
