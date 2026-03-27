from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.map_service import get_connected_locations
from game.district_service import get_district_move_commands
from game.location_rules import is_city, check_location_access, LOCATION_REQUIREMENTS


STARTER_LOCATIONS = {"silver_city", "dark_forest", "emerald_fields"}


def _is_location_discovered(telegram_id: int, location_slug: str) -> bool:
    """
    Локация считается «известной» если игрок её посетил (cell_type='normal')
    или видел как сосед (cell_type='visible').
    Только полностью неизвестные локации показываются как ❓.
    """
    if location_slug in STARTER_LOCATIONS:
        return True
    if not telegram_id:
        return False
    try:
        from database.repositories import get_connection
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM player_grid_exploration WHERE telegram_id=? AND location_slug=?",
                (telegram_id, location_slug)
            ).fetchone()
        return (row[0] > 0) if row else False
    except Exception:
        return True


def _get_player(telegram_id: int):
    if not telegram_id:
        return None
    try:
        from database.repositories import get_player
        return get_player(telegram_id)
    except Exception:
        return None


def navigation_menu(location_slug: str, district_slug: str | None = None, telegram_id: int = None):
    """
    Меню переходов между локациями.

    Для города: переходы между районами (это городской аналог локаций).
    Для поля: ТОЛЬКО переходы в соседние локации — без кнопок районов.
    Районы полевой локации переключаются через карточку локации (🧭 Локация),
    чтобы не смешивать два разных действия в одном меню.
    """
    buttons = []

    if is_city(location_slug):
        # Город: кнопки переходов между районами
        for cmd in get_district_move_commands(location_slug, telegram_id=telegram_id):
            buttons.append([KeyboardButton(text=cmd)])

        if district_slug == "main_gate":
            buttons.append([KeyboardButton(text="🚶 Покинуть город")])

        buttons.append([KeyboardButton(text="🗺 Карта")])

    else:
        # Поле: только переходы в соседние локации
        player = _get_player(telegram_id)
        seen_unknown = False  # только одна кнопка ❓ на все неизвестные

        for location in get_connected_locations(location_slug):
            discovered = _is_location_discovered(telegram_id, location.slug)

            if not discovered and location.slug not in STARTER_LOCATIONS:
                # Полностью неизвестная локация — игрок никогда не был рядом
                if not seen_unknown:
                    buttons.append([KeyboardButton(text="❓ Неизведанная территория")])
                    seen_unknown = True
                continue

            # Локация известна (visited или visible) — показываем с замком или без
            allowed = True
            min_level = 1

            if player:
                try:
                    from database.repositories import get_player_story
                    story = get_player_story(telegram_id)
                    completed_ids = story.get("completed_ids", []) if story else []
                    allowed, _ = check_location_access(player, location.slug, completed_ids)
                except Exception:
                    allowed = True

            req = LOCATION_REQUIREMENTS.get(location.slug, {})
            min_level = req.get("min_level", 1)

            if allowed:
                cmd = f"🚶 {location.name}"
            else:
                # Заблокирована — показываем с замком и уровнем
                # Кнопка начинается с "🚶" — нормализатор в move_handler уберёт суффикс
                cmd = f"🚶 🔒 {location.name} (ур.{min_level}+)"

            buttons.append([KeyboardButton(text=cmd)])

        buttons.append([KeyboardButton(text="🗺 Карта")])

    buttons.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
