from pathlib import Path

from aiogram.types import Message, FSInputFile

from database.repositories import (
    get_player,
    set_ui_screen,
    update_player_district,
    update_player_location,
)
from game.city_service import GUILD_QUESTS, render_guild_text
from game.location_rules import is_city
from keyboards.city_menu import city_menu, district_actions_menu
from keyboards.main_menu import main_menu

async def guild_alchemists_handler(message: Message):
    await _guild_handler(
        message,
        "⚗ Гильдия алхимиков",
        "Здесь раскрывают секреты настоев, эссенций и устойчивых смесей.",
        "alchemist",
        "guild_hall.png",
    )


async def _guild_handler(message: Message, title: str, description: str, profession: str, image_name: str):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Гильдии доступны только в городе.")
        return

    quests = [q for q in GUILD_QUESTS if q["profession"] == profession]

    await _answer_with_city_image(
        message,
        image_name,
        render_guild_text(title, description, quests),
        city_menu(player.current_district_slug),
    )


async def city_guard_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Стража доступна только в городе.")
        return

    text = (
        "🛡 Городская стража\n\n"
        "Стражник напоминает: за воротами опасно.\n"
        "Подготовь сумку, купи расходники и выходи только через главные ворота."
    )

    set_ui_screen(message.from_user.id, "city")
    await _answer_with_city_image(
        message,
        "city_square.png",
        text,
        city_menu(player.current_district_slug),
    )


async def leave_city_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Ты и так не в городе.")
        return

    if player.current_district_slug != "main_gate":
        await message.answer(
            "Покинуть город можно только через 🚪 Главные ворота.",
            reply_markup=city_menu(player.current_district_slug),
        )
        return

    update_player_location(message.from_user.id, "dark_forest")
    set_ui_screen(message.from_user.id, "main")

    await message.answer(
        "🚶 Ты покидаешь Сереброград через главные ворота и выходишь в Тёмный лес.",
        reply_markup=main_menu("dark_forest", None),
    )


async def city_market_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Торговый квартал доступен только в городе.")
        return

    update_player_district(message.from_user.id, "market_square")
    set_ui_screen(message.from_user.id, "district")

    text = (
        "🏬 Торговый квартал\n\n"
        "Ты входишь в торговый квартал.\n"
        "Здесь можно купить сумки, найти рынок монстров и продать ресурсы."
    )

    await _answer_with_city_image(
        message,
        "city_square.png",
        text,
        district_actions_menu("market_square"),
    )
