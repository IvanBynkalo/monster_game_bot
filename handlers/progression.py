from aiogram.types import Message
from database.repositories import get_player, spend_stat_point
from game.progression_service import render_attributes, render_professions
from keyboards.progression_menu import progression_menu
from keyboards.main_menu import main_menu

async def progression_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    text = (
        "📈 Развитие героя\n\n"
        + render_attributes(player) + "\n\n"
        + render_professions(player) + "\n\n"
        + "🎒 Сумки больше не улучшаются напрямую. Новую сумку можно купить только в городе у продавца.\n"
        + f"Текущая вместимость сумки: {player.bag_capacity}"
    )
    await message.answer(text, reply_markup=progression_menu())

async def add_strength_handler(message: Message):
    await _spend_stat(message, "strength", "💪 Сила повышена")

async def add_agility_handler(message: Message):
    await _spend_stat(message, "agility", "🤸 Ловкость повышена")

async def add_intellect_handler(message: Message):
    await _spend_stat(message, "intellect", "🧠 Интеллект повышен")

async def _spend_stat(message: Message, stat_name: str, title: str):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if not spend_stat_point(message.from_user.id, stat_name):
        await message.answer("Нет свободных очков характеристик.", reply_markup=progression_menu())
        return
    await message.answer(title + "\n\n" + render_attributes(player), reply_markup=progression_menu())

async def upgrade_bag_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer("🎒 Сумки больше не улучшаются напрямую. Покупай новые сумки только в городе, в лавке.", reply_markup=progression_menu())

async def back_from_progression_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer("Главное меню", reply_markup=main_menu(player.location_slug, player.current_district_slug))
