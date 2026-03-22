from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.map_service import get_move_commands, get_connected_locations
from game.district_service import get_district_move_commands
from game.location_rules import is_city, check_location_access

# Локации доступные с самого начала без исследования
STARTER_LOCATIONS = {"silver_city", "dark_forest", "emerald_fields"}


def _is_location_discovered(telegram_id: int, location_slug: str) -> bool:
    """Локация открыта если она стартовая ИЛИ игрок уже посещал её."""
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
        return True  # Если ошибка - показываем


def _get_player_level(telegram_id: int) -> int:
    if not telegram_id:
        return 1
    try:
        from database.repositories import get_player
        p = get_player(telegram_id)
        return p.level if p else 1
    except Exception:
        return 1


def navigation_menu(location_slug: str, district_slug: str | None = None,
                    telegram_id: int = None):
    buttons = []

    if is_city(location_slug):
        for cmd in get_district_move_commands(location_slug):
            buttons.append([KeyboardButton(text=cmd)])

        if district_slug == "main_gate":
            buttons.append([KeyboardButton(text="🚶 Покинуть город")])

        buttons.append([KeyboardButton(text="🗺 Карта")])
    else:
        from game.map_service import LOCATION_LEVEL_REQUIREMENT
        player_level = _get_player_level(telegram_id)

        for location in get_connected_locations(location_slug):
            min_lvl = LOCATION_LEVEL_REQUIREMENT.get(location.slug, 1)

            # Проверяем уровень доступа
            if player_level < min_lvl:
                # Показываем заблокированную локацию только если она уже открыта
                if _is_location_discovered(telegram_id, location.slug):
                    cmd = f"🔒 {location.name} (ур.{min_lvl}+)"
                    buttons.append([KeyboardButton(text=cmd)])
                continue

            # Показываем только открытые или стартовые локации
            if not _is_location_discovered(telegram_id, location.slug):
                # Неоткрытая — показываем как ??? для интриги
                if location.slug not in STARTER_LOCATIONS:
                    buttons.append([KeyboardButton(text="❓ Неизведанная территория")])
                continue

            cmd = f"🚶 {location.name}"
            buttons.append([KeyboardButton(text=cmd)])

        for cmd in get_district_move_commands(location_slug):
            buttons.append([KeyboardButton(text=cmd)])

        buttons.append([KeyboardButton(text="🗺 Карта")])

    buttons.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
