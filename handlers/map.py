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
from game.travel_service import start_travel, get_travel, get_travel_seconds, format_travel_time, is_traveling, check_arrival, render_travel_status, LOCATION_NAMES
from keyboards.main_menu import main_menu
from keyboards.location_menu import location_actions_inline
from keyboards.navigation_menu import navigation_menu
# ── Error tracking shim ──────────────────────────────────────────────────────
try:
    from game.error_tracker import log_logic_error as _log_logic, log_exception as _log_exc
except Exception:
    def _log_logic(*a, **k): pass
    def _log_exc(*a, **k): pass
# ─────────────────────────────────────────────────────────────────────────────




def _normalize_move_text(text: str) -> str:
    import re
    text = (text or "").strip()
    if text.startswith("Перейти: "):
        text = "🚶 " + text.replace("Перейти: ", "", 1)
    # Убираем суффикс уровня "(ур.X+)" если есть
    text = re.sub(r"\s*\(ур\.\d+\+\)\s*$", "", text).strip()
    return text


async def navigation_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "navigation")
    await message.answer(
        "🧭 Навигация\n\nЗдесь собраны все доступные переходы: районы, соседние области и карта.",
        reply_markup=navigation_menu(player.location_slug, player.current_district_slug, telegram_id=message.from_user.id),
    )


async def map_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "main")
    caption = build_map_caption(player.location_slug)

    from game.location_rules import is_city
    from game.dungeon_service import DUNGEONS
    from game.grid_exploration_service import is_dungeon_available

    if WORLD_MAP_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(str(WORLD_MAP_PATH)),
            caption=caption,
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
    else:
        await message.answer(
            render_map_overview(player.location_slug),
            reply_markup=main_menu(player.location_slug, player.current_district_slug)
        )

    # Inline-меню действий — только вне города
    if not is_city(player.location_slug):
        try:
            has_dungeon = player.location_slug in DUNGEONS and is_dungeon_available(
                message.from_user.id, player.location_slug
            )
        except Exception:
            has_dungeon = False
        await message.answer(
            "Что делать:",
            reply_markup=location_actions_inline(player.location_slug, has_dungeon=has_dungeon)
        )


async def location_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "main")
    loc_text = render_location_card(player.location_slug)
    # Добавляем панель рождения если в нужном месте
    from game.emotion_birth_service import get_birth_panel, BIRTH_LOCATIONS
    if player.location_slug in BIRTH_LOCATIONS:
        birth_p = get_birth_panel(message.from_user.id, player.location_slug)
        if birth_p:
            loc_text += f"\n\n{birth_p}"
    await message.answer(
        loc_text,
        reply_markup=main_menu(player.location_slug, player.current_district_slug)
    )
    # Inline-меню действий локации отдельным сообщением
    from game.dungeon_service import DUNGEONS
    from game.grid_exploration_service import is_dungeon_available
    has_dungeon = player.location_slug in DUNGEONS and is_dungeon_available(message.from_user.id, player.location_slug)
    inline_kb = location_actions_inline(player.location_slug, has_dungeon=has_dungeon)
    await message.answer("Действия:", reply_markup=inline_kb)


async def move_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    # Проверяем не в пути ли уже герой
    if (message.text or "").strip() == "🚫 Отменить перемещение":
        from database.repositories import get_connection as _gc_cancel
        with _gc_cancel() as _conn:
            _conn.execute("DELETE FROM player_travel WHERE telegram_id=?",
                          (message.from_user.id,))
            _conn.commit()
        await message.answer(
            "✅ Перемещение отменено. Ты остался на месте.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug)
        )
        return

    if is_traveling(message.from_user.id):
        travel_data = get_travel(message.from_user.id)
        if travel_data:
            await message.answer(render_travel_status(travel_data))
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

    # Проверка уровня и требований локации
    from database.repositories import get_player_story
    story = get_player_story(message.from_user.id)
    completed_ids = story.get("completed_ids", []) if story else []
    allowed, reason = check_location_access(player, target.slug, completed_ids)
    if not allowed:
        await message.answer(reason)
        return

    # Начинаем путешествие с учётом ловкости
    travel = start_travel(
        message.from_user.id,
        player.location_slug,
        target.slug,
        agility=player.agility
    )

    from_name = LOCATION_NAMES.get(player.location_slug, player.location_slug)
    to_name   = LOCATION_NAMES.get(target.slug, target.slug)

    if travel["seconds"] <= 30:
        # Короткий переход — мгновенно
        update_player_location(message.from_user.id, target.slug)
        story_done = update_story_progress(message.from_user.id, "move", target.slug)
        set_ui_screen(message.from_user.id, "main")
        # Отмечаем локацию как посещённую (для навигации)
        try:
            from database.repositories import get_connection as _gc_disc
            with _gc_disc() as _conn:
                _conn.execute("""
                    INSERT OR IGNORE INTO player_grid_exploration
                    (telegram_id, location_slug, col, row, cell_type)
                    VALUES (?, ?, 5, 0, 'normal')
                """, (message.from_user.id, target.slug))
                _conn.commit()
        except Exception:
            pass
    else:
        # Длинный переход — герой в пути
        await message.answer(
            f"🚶 Ты отправляешься в путь.\n"
            f"{from_name} → {to_name}\n"
            f"⏱ Время в пути: {travel['time_text']}\n\n"
            f"Во время перехода нельзя исследовать и сражаться.\n"
            f"Нажми 🚫 Отменить перемещение если хочешь остаться.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug,
                                   is_traveling=True)
        )
        return

    story_done = update_story_progress(message.from_user.id, "move", target.slug)
    set_ui_screen(message.from_user.id, "main")

    try:
        from game.grid_exploration_service import render_exploration_panel as _grid_panel
        _expl_panel = _grid_panel(message.from_user.id, target.slug)
    except Exception as _e:
        import logging
        logging.getLogger(__name__).warning(f"grid panel failed: {_e}")
        _expl_panel = ""
    # Проверяем недельный квест при входе в регион
    try:
        _new_wq = check_and_assign_weekly_quest(message.from_user.id, target.slug)
        _active_wq = get_active_weekly_quest(message.from_user.id, target.slug)
    except Exception as _we:
        import logging
        logging.getLogger(__name__).warning(f"weekly quest failed: {_we}")
        _new_wq = None
        _active_wq = None
    _wq_text = ""
    if _new_wq:
        _wq_text = f"\n\n🎉 Новый недельный квест!\n{render_weekly_quest(_new_wq)}"
    elif _active_wq and not _active_wq["completed"]:
        _wq_text = f"\n\n{render_weekly_quest(_active_wq)}"
    text = f"🚶 Ты переместился в новую область.\n\n{render_location_card(target.slug)}\n\n{_expl_panel}{_wq_text}"
    if story_done:
        text += "\n\n" + apply_story_reward(message.from_user.id, story_done)

    await send_location_image(message, target.slug, text,
                               reply_markup=main_menu(target.slug, None))
    # Inline-меню действий при прибытии
    from game.dungeon_service import DUNGEONS
    from game.emotion_birth_service import get_birth_panel, BIRTH_LOCATIONS
    from game.grid_exploration_service import is_dungeon_available
    from game.location_rules import is_city as _is_city
    if not _is_city(target.slug):
        try:
            has_dungeon = target.slug in DUNGEONS and is_dungeon_available(message.from_user.id, target.slug)
        except Exception:
            has_dungeon = False
        inline_kb = location_actions_inline(target.slug, has_dungeon=has_dungeon)
        await message.answer("Что делать:", reply_markup=inline_kb)
    # Панель рождения если это место ритуала
    if target.slug in BIRTH_LOCATIONS:
        birth_p = get_birth_panel(message.from_user.id, target.slug)
        if birth_p:
            await message.answer(birth_p)
