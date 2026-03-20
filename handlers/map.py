from aiogram.types import Message, FSInputFile
from utils.images import send_location_image
from game.exploration_service import render_exploration_panel
from game.weekly_quest_service import check_and_assign_weekly_quest, get_active_weekly_quest, render_weekly_quest

from database.repositories import get_player, set_ui_screen, update_player_location, update_story_progress
from game.location_rules import check_location_access
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
from keyboards.navigation_menu import navigation_menu


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
    set_ui_screen(message.from_user.id, "navigation")
    await message.answer(
        "🧭 Навигация\n\nЗдесь собраны все доступные переходы: районы, соседние области и карта.",
        reply_markup=navigation_menu(player.location_slug, player.current_district_slug),
    )


async def map_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "main")
    caption = build_map_caption(player.location_slug)
    if WORLD_MAP_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(str(WORLD_MAP_PATH)),
            caption=caption,
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return
    await message.answer(render_map_overview(player.location_slug), reply_markup=main_menu(player.location_slug, player.current_district_slug))


async def location_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "main")
    await send_location_image(message, player.location_slug,
                               render_location_card(player.location_slug),
                               reply_markup=main_menu(player.location_slug, player.current_district_slug))


async def move_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if (message.text or "").strip() == "⬅️ Назад":
        set_ui_screen(message.from_user.id, "main")
        await message.answer("Главное меню", reply_markup=main_menu(player.location_slug, player.current_district_slug))
        return

    normalized = _normalize_move_text(message.text)
    target = resolve_location_by_move_text(normalized)
    if not target:
        await message.answer("Не удалось определить локацию для перехода.")
        return

    available_names = set(get_move_commands(player.location_slug))
    if f"🚶 {target.name}" not in available_names:
        await message.answer("Из текущей локации туда пройти нельзя.")
        return

    update_player_location(message.from_user.id, target.slug)
    story_done = update_story_progress(message.from_user.id, "move", target.slug)
    set_ui_screen(message.from_user.id, "main")

    _expl_panel = render_exploration_panel(message.from_user.id, target.slug)
    # Проверяем недельный квест при входе в регион
    _new_wq = check_and_assign_weekly_quest(message.from_user.id, target.slug)
    _active_wq = get_active_weekly_quest(message.from_user.id, target.slug)
    _wq_text = ""
    if _new_wq:
        _wq_text = f"\n\n🎉 Новый недельный квест!\n{render_weekly_quest(_new_wq)}"
    elif _active_wq and not _active_wq["completed"]:
        _wq_text = f"\n\n{render_weekly_quest(_active_wq)}"
    text = f"🚶 Ты переместился в новую область.\n\n{render_location_card(target.slug)}\n\n{_expl_panel}{_wq_text}"
    if story_done:
        text += "\n\n" + apply_story_reward(message.from_user.id, story_done)

    # Показываем картинку локации при прибытии
    await send_location_image(message, target.slug, text,
                               reply_markup=main_menu(target.slug, None))
