from aiogram.types import Message
from database.repositories import get_or_create_player, set_ui_screen
from game.player_service import ensure_starter_monster
from game.daily_service import handle_login_streak
from game.daily_service import get_daily_panel
from utils.analytics import track_new_player, track_session_start
from game.map_service import render_location_card

RARITY_LABELS = {
    "common": "Обычный", "rare": "Редкий",
    "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический",
}
MOOD_LABELS = {
    "rage": "🔥 Ярость", "fear": "😱 Страх",
    "instinct": "🎯 Инстинкт", "inspiration": "✨ Вдохновение",
    "sadness": "💧 Грусть", "joy": "🌟 Радость",
    "disgust": "🤢 Отвращение", "surprise": "⚡ Удивление",
}


async def start_handler(message: Message):
    from keyboards.main_menu import main_menu

    player, created = get_or_create_player(
        message.from_user.id,
        message.from_user.first_name or "Игрок"
    )
    starter_monster, starter_created = ensure_starter_monster(message.from_user.id)

    if created:
        track_new_player(message.from_user.id, player.name)
        await message.answer(
            "Добро пожаловать в Monster Emotions.\n"
            "Ты вступаешь в мир, где монстры рождаются из эмоций."
        )
        await message.answer(
            "Пролог\n"
            "Проводник Эйр просит начать с Тёмного леса. "
            "Прислушайся к шёпоту деревьев и найди источник искажения."
        )

    if starter_created and starter_monster:
        await message.answer(
            f"Ты получаешь стартового монстра: {starter_monster['name']}\n"
            f"Редкость: {RARITY_LABELS.get(starter_monster['rarity'], starter_monster['rarity'])}\n"
            f"Эмоция: {MOOD_LABELS.get(starter_monster['mood'], starter_monster['mood'])}"
        )

    # Ежедневный вход: streak + награда (рек. #12)
    streak_text = handle_login_streak(message.from_user.id)
    if streak_text:
        await message.answer(streak_text)

    # Аналитика сессии (рек. #20)
    track_session_start(message.from_user.id)

    set_ui_screen(message.from_user.id, "main")
    await message.answer(
        render_location_card(player.location_slug),
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
    )
