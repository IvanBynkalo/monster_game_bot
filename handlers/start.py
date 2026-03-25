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
    from game.player_service import ensure_player_crystal_state
    from keyboards.main_menu import main_menu

    migration = ensure_player_crystal_state(message.from_user.id)

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
    from database.repositories import get_player as _get_fresh
    _player = _get_fresh(message.from_user.id)

    from utils.images import send_location_image
    from keyboards.location_menu import location_actions_inline
    from game.dungeon_service import DUNGEONS
    from game.location_rules import is_city

    loc_text = render_location_card(_player.location_slug)

    if is_city(_player.location_slug):
        # В городе — показываем городское меню
        await message.answer(loc_text, reply_markup=main_menu(_player.location_slug, _player.current_district_slug))
    else:
        # Вне города — показываем локацию с картинкой + inline-меню
        await send_location_image(
            message, _player.location_slug, loc_text,
            reply_markup=main_menu(_player.location_slug, _player.current_district_slug)
        )
        try:
            from game.grid_exploration_service import is_dungeon_available
            has_dungeon = _player.location_slug in DUNGEONS and is_dungeon_available(message.from_user.id, _player.location_slug)
        except Exception:
            has_dungeon = False
        await message.answer(
            "Что делать:",
            reply_markup=location_actions_inline(_player.location_slug, has_dungeon=has_dungeon)
        )
