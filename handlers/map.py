from aiogram.types import Message, FSInputFile

from database.repositories import (
    get_player,
    set_ui_screen,
    update_player_location,
    update_story_progress,
)
from game.location_rules import check_location_access, is_city
from game.map_service import (
    WORLD_MAP_PATH,
    build_map_caption,
    get_move_commands,
    render_location_card,
    render_map_overview,
    resolve_location_by_move_text,
)
from game.story_service import apply_story_reward
from game.travel_service import (
    LOCATION_NAMES,
    check_arrival,
    get_travel,
    is_traveling,
    render_travel_status,
    start_travel,
)
from game.weekly_quest_service import (
    check_and_assign_weekly_quest,
    get_active_weekly_quest,
    render_weekly_quest,
)
from keyboards.location_menu import location_actions_inline
from keyboards.main_menu import main_menu
from keyboards.navigation_menu import navigation_menu
from services.ui_service import show_location_screen
from utils.images import send_location_image


# ── Error tracking shim ──────────────────────────────────────────────────────
try:
    from game.error_tracker import log_logic_error as _log_logic, log_exception as _log_exc
except Exception:  # pragma: no cover
    def _log_logic(*a, **k):
        pass

    def _log_exc(*a, **k):
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_move_text(text: str) -> str:
    import re

    text = (text or "").strip()
    if text.startswith("Перейти: "):
        text = "🚶 " + text.replace("Перейти: ", "", 1)
    text = re.sub(r"\s*\(ур\.\d+\+\)\s*$", "", text).strip()
    return text


def _root_menu_for_player(player, user_id: int, *, traveling: bool = False):
    return main_menu(
        player.location_slug,
        getattr(player, "current_district_slug", None),
        is_traveling=traveling,
        telegram_id=user_id,
    )


async def _show_travel_status(message: Message, player) -> bool:
    """Показывает статус путешествия. Возвращает True, если игрок сейчас в пути."""
    arrival = check_arrival(message.from_user.id)
    if arrival and arrival.get("arrived"):
        return False

    if not is_traveling(message.from_user.id):
        return False

    travel_data = get_travel(message.from_user.id)
    if travel_data:
        await message.answer(
            render_travel_status(travel_data),
            reply_markup=_root_menu_for_player(player, message.from_user.id, traveling=True),
        )
    return True


async def _show_world_map(message: Message, player):
    caption = build_map_caption(player.location_slug)
    set_ui_screen(message.from_user.id, "main")

    if WORLD_MAP_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(str(WORLD_MAP_PATH)),
            caption=caption,
            reply_markup=_root_menu_for_player(player, message.from_user.id),
        )
    else:
        await message.answer(
            render_map_overview(player.location_slug),
            reply_markup=_root_menu_for_player(player, message.from_user.id),
        )


async def _show_location_actions(message: Message, location_slug: str):
    if is_city(location_slug):
        return

    try:
        from game.dungeon_service import DUNGEONS
        from game.grid_exploration_service import is_dungeon_available

        has_dungeon = location_slug in DUNGEONS and is_dungeon_available(
            message.from_user.id,
            location_slug,
        )
    except Exception:
        has_dungeon = False

    await message.answer(
        "Что будешь делать в этой локации?",
        reply_markup=location_actions_inline(location_slug, has_dungeon=has_dungeon),
    )


async def _show_arrival_screen(message: Message, target_slug: str, story_done):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    try:
        from game.grid_exploration_service import render_exploration_panel

        exploration_panel = render_exploration_panel(message.from_user.id, target_slug)
    except Exception as exc:
        _log_exc("grid panel failed", exc=exc, extra={"target_slug": target_slug})
        exploration_panel = ""

    try:
        new_weekly = check_and_assign_weekly_quest(message.from_user.id, target_slug)
        active_weekly = get_active_weekly_quest(message.from_user.id, target_slug)
    except Exception as exc:
        _log_exc("weekly quest failed", exc=exc, extra={"target_slug": target_slug})
        new_weekly = None
        active_weekly = None

    weekly_text = ""
    if new_weekly:
        weekly_text = f"\n\n🎉 Новый недельный квест!\n{render_weekly_quest(new_weekly)}"
    elif active_weekly and not active_weekly.get("completed"):
        weekly_text = f"\n\n{render_weekly_quest(active_weekly)}"

    text = (
        "🚶 Ты переместился в новую область.\n\n"
        f"{render_location_card(target_slug, telegram_id=message.from_user.id, current_district_slug=getattr(player, 'current_district_slug', None))}\n\n"
        f"{exploration_panel}{weekly_text}"
    ).strip()

    if story_done:
        text += "\n\n" + apply_story_reward(message.from_user.id, story_done)

    await send_location_image(
        message,
        target_slug,
        text,
        reply_markup=_root_menu_for_player(player, message.from_user.id),
    )
    await _show_location_actions(message, target_slug)

    try:
        from game.emotion_birth_service import BIRTH_LOCATIONS, get_birth_panel

        if target_slug in BIRTH_LOCATIONS:
            birth_panel = get_birth_panel(message.from_user.id, target_slug)
            if birth_panel:
                await message.answer(birth_panel)
    except Exception:
        pass


def _mark_location_discovered(user_id: int, location_slug: str):
    try:
        from database.repositories import get_connection

        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO player_grid_exploration
                (telegram_id, location_slug, col, row, cell_type)
                VALUES (?, ?, 5, 0, 'normal')
                """,
                (user_id, location_slug),
            )
            conn.commit()
    except Exception as exc:
        _log_exc("mark discovered failed", exc=exc, extra={"location_slug": location_slug})


# ─────────────────────────────────────────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────────────────────────────────────────

async def map_handler(message: Message):
    """Экран обзора мира / карты, отдельно от экрана текущей локации."""
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if await _show_travel_status(message, player):
        return

    player = get_player(message.from_user.id) or player
    await _show_world_map(message, player)


async def location_handler(message: Message):
    """Экран текущей локации: где игрок находится и что тут можно делать."""
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if await _show_travel_status(message, player):
        return

    set_ui_screen(message.from_user.id, "location")
    await show_location_screen(message, message.from_user.id)


async def navigation_handler(message: Message):
    """Экран только для переходов: соседние зоны и районы текущей локации."""
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    arrival = check_arrival(message.from_user.id)
    if arrival and arrival.get("arrived"):
        player = get_player(message.from_user.id) or player

    if is_traveling(message.from_user.id):
        travel_data = get_travel(message.from_user.id)
        if travel_data:
            await message.answer(
                render_travel_status(travel_data),
                reply_markup=_root_menu_for_player(player, message.from_user.id, traveling=True),
            )
        return

    set_ui_screen(message.from_user.id, "navigation")

    district_slug = getattr(player, "current_district_slug", None)
    current_location_name = LOCATION_NAMES.get(player.location_slug, player.location_slug)
    lines = [
        "🗺 Переходы",
        "",
        f"Сейчас ты находишься: {current_location_name}",
    ]

    if district_slug:
        lines.append(f"Текущий район: {district_slug}")

    if is_city(player.location_slug):
        lines += [
            "",
            "Здесь можно переходить между городскими районами или выйти через главные ворота.",
        ]
    else:
        lines += [
            "",
            "Здесь показаны соседние локации и доступные районы текущей зоны.",
            "Чтобы посмотреть описание места и действия в нём, нажми «🧭 Локация».",
        ]

    await message.answer(
        "\n".join(lines),
        reply_markup=navigation_menu(
            player.location_slug,
            district_slug,
            telegram_id=message.from_user.id,
        ),
    )


async def move_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    text = (message.text or "").strip()

    if text == "🚫 Отменить перемещение":
        from database.repositories import get_connection

        with get_connection() as conn:
            conn.execute(
                "DELETE FROM player_travel WHERE telegram_id=?",
                (message.from_user.id,),
            )
            conn.commit()

        await message.answer(
            "✅ Перемещение отменено. Ты остался на месте.",
            reply_markup=_root_menu_for_player(player, message.from_user.id),
        )
        return

    arrival = check_arrival(message.from_user.id)
    if arrival and arrival.get("arrived"):
        player = get_player(message.from_user.id) or player
        await message.answer(
            f"✅ Ты прибыл в {LOCATION_NAMES.get(player.location_slug, player.location_slug)}!",
            reply_markup=_root_menu_for_player(player, message.from_user.id),
        )
        return

    if is_traveling(message.from_user.id):
        travel_data = get_travel(message.from_user.id)
        if travel_data:
            await message.answer(
                render_travel_status(travel_data),
                reply_markup=_root_menu_for_player(player, message.from_user.id, traveling=True),
            )
        return

    if text == "⬅️ Назад":
        set_ui_screen(message.from_user.id, "main")
        await message.answer(
            "Главное меню",
            reply_markup=_root_menu_for_player(player, message.from_user.id),
        )
        return

    if text in {"🗺 Карта", "Карта"}:
        await map_handler(message)
        return

    normalized = _normalize_move_text(text)
    target = resolve_location_by_move_text(normalized)
    if not target:
        await message.answer("Не удалось определить локацию для перехода.")
        return

    available_names = set(get_move_commands(player.location_slug))
    if f"🚶 {target.name}" not in available_names:
        await message.answer("Из текущей локации туда пройти нельзя.")
        return

    from database.repositories import get_player_story

    story = get_player_story(message.from_user.id)
    completed_ids = story.get("completed_ids", []) if story else []
    allowed, reason = check_location_access(player, target.slug, completed_ids)
    if not allowed:
        await message.answer(reason)
        return

    travel = start_travel(
        message.from_user.id,
        player.location_slug,
        target.slug,
        agility=player.agility,
    )

    from_name = LOCATION_NAMES.get(player.location_slug, player.location_slug)
    to_name = LOCATION_NAMES.get(target.slug, target.slug)

    if travel["seconds"] > 10:
        await message.answer(
            f"🚶 Ты отправляешься в путь.\n"
            f"{from_name} → {to_name}\n"
            f"⏱ Время в пути: {travel['time_text']}\n\n"
            "Во время перехода нельзя исследовать и сражаться.\n"
            "Нажми 🚫 Отменить перемещение, если хочешь остаться.",
            reply_markup=_root_menu_for_player(player, message.from_user.id, traveling=True),
        )
        return

    update_player_location(message.from_user.id, target.slug)
    _mark_location_discovered(message.from_user.id, target.slug)
    story_done = update_story_progress(message.from_user.id, "move", target.slug)
    set_ui_screen(message.from_user.id, "location")
    await _show_arrival_screen(message, target.slug, story_done)
