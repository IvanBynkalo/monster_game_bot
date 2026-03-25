from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.map_service import get_connected_locations
from game.district_service import get_district_move_commands
from game.location_rules import is_city, check_location_access


STARTER_LOCATIONS = {"silver_city", "dark_forest", "emerald_fields"}


def _is_location_discovered(telegram_id: int, location_slug: str) -> bool:
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
    buttons = []

    if is_city(location_slug):
        for cmd in get_district_move_commands(location_slug, telegram_id=telegram_id):
            buttons.append([KeyboardButton(text=cmd)])

        if district_slug == "main_gate":
            buttons.append([KeyboardButton(text="🚶 Покинуть город")])

        buttons.append([KeyboardButton(text="🗺 Карта")])
    else:
        player = _get_player(telegram_id)

        for location in get_connected_locations(location_slug):
            # Не показываем неоткрытые зоны, кроме стартовых
            if not _is_location_discovered(telegram_id, location.slug):
                if location.slug not in STARTER_LOCATIONS:
                    buttons.append([KeyboardButton(text="❓ Неизведанная территория")])
                continue

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

            from game.location_rules import LOCATION_REQUIREMENTS
            req = LOCATION_REQUIREMENTS.get(location.slug, {})
            min_level = req.get("min_level", 1)

            if allowed:
                cmd = f"🚶 {location.name}"
            else:
                cmd = f"🔒 {location.name} (ур.{min_level}+)"
            buttons.append([KeyboardButton(text=cmd)])

        for cmd in get_district_move_commands(location_slug, telegram_id=telegram_id):
            buttons.append([KeyboardButton(text=cmd)])

        buttons.append([KeyboardButton(text="🗺 Карта")])

    buttons.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
