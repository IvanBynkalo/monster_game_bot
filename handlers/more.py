"""
handlers/more.py

Вторичный UI-слой:
- открытие раздела «Ещё»
- открытие подменю лечения
- единая логика кнопки «⬅️ Назад»

Цель:
- убрать ручную и нелогичную навигацию;
- сделать возвраты иерархическими;
- сохранить совместимость с текущими обработчиками bot.py.
"""

from aiogram.types import Message

from config import ADMIN_IDS
from database.repositories import get_player, get_ui_screen, set_ui_screen
from game.location_rules import is_city
from keyboards.healing_menu import healing_menu
from keyboards.main_menu import main_menu
from keyboards.more_menu import more_menu


# ──────────────────────────────────────────────────────────────────────────────
# Конфигурация экранов
# ──────────────────────────────────────────────────────────────────────────────

# Из этих экранов возвращаемся в меню «Ещё»
_BACK_TO_MORE = {
    "healing",
}

# Из этих экранов возвращаемся в текущий район города
_BACK_TO_DISTRICT = {
    "shop",
    "item_shop",
    "monster_shop",
    "bag_shop",
    "sell_shop",
    "buy_resources",
    "craft",
    "traps",
}

# Из этих экранов возвращаемся в городской хаб
_BACK_TO_CITY = {
    "district",
    "board",
    "guilds",
}

# Из этих экранов возвращаемся в корневое меню мира/города
_BACK_TO_ROOT = {
    "main",
    "more",
    "inventory",
    "navigation",
    "progression",
    "city",
    "dungeon",
}


# ──────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────────────────────────────────────

def _is_admin(user_id: int) -> bool:
    return user_id in set(ADMIN_IDS or [])


def _is_traveling_now(user_id: int) -> bool:
    try:
        from game.travel_service import is_traveling as _is_traveling
        return _is_traveling(user_id)
    except Exception:
        return False


def _root_markup(player, user_id: int):
    return main_menu(
        player.location_slug,
        getattr(player, "current_district_slug", None),
        is_traveling=_is_traveling_now(user_id),
        telegram_id=user_id,
    )


async def _show_root_menu(message: Message, player, text: str = "Главное меню"):
    set_ui_screen(message.from_user.id, "main")
    await message.answer(
        text,
        reply_markup=_root_markup(player, message.from_user.id),
    )


async def _show_more_menu(message: Message):
    set_ui_screen(message.from_user.id, "more")
    await message.answer(
        "📂 Меню:",
        reply_markup=more_menu(is_admin=_is_admin(message.from_user.id)),
    )


async def _show_healing_menu(message: Message):
    set_ui_screen(message.from_user.id, "healing")
    await message.answer(
        "❤️ Лечение и восстановление:",
        reply_markup=healing_menu(),
    )


async def _show_city_hub(message: Message, player):
    """
    Возврат в корневой городской экран.
    Используем уже существующий city_handler, чтобы:
    - не дублировать текст и картинки,
    - сохранить текущую логику проекта.
    """
    if not is_city(player.location_slug):
        await _show_root_menu(message, player, "Ты сейчас не в городе.")
        return

    from handlers.city import city_handler
    await city_handler(message)


async def _show_current_district(message: Message, player):
    """
    Возврат в текущий район города.
    Если район неизвестен — возвращаем в городской хаб.
    """
    if not is_city(player.location_slug):
        await _show_root_menu(message, player)
        return

    district_slug = getattr(player, "current_district_slug", None)

    try:
        if district_slug == "market_square":
            from handlers.city import city_market_handler
            await city_market_handler(message)
            return

        if district_slug == "guild_quarter":
            from handlers.city import city_guilds_handler
            await city_guilds_handler(message)
            return

        if district_slug == "craft_quarter":
            from handlers.city import city_craft_quarter_handler
            await city_craft_quarter_handler(message)
            return

        if district_slug == "main_gate":
            from handlers.city import city_guard_handler
            await city_guard_handler(message)
            return
    except Exception:
        # Если какой-то специализированный экран не открылся,
        # безопасно возвращаем игрока в городское меню.
        pass

    await _show_city_hub(message, player)


# ──────────────────────────────────────────────────────────────────────────────
# Хендлеры
# ──────────────────────────────────────────────────────────────────────────────

async def more_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    await _show_more_menu(message)


async def healing_menu_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    await _show_healing_menu(message)


async def back_handler(message: Message):
    """
    Универсальная кнопка «⬅️ Назад».

    Правило:
    - подэкран -> родительский экран
    - неизвестный экран -> безопасный возврат в корневое меню
    """
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    screen = get_ui_screen(message.from_user.id) or "main"

    # 1) Подменю лечения -> в «Ещё»
    if screen in _BACK_TO_MORE:
        await _show_more_menu(message)
        return

    # 2) Магазины / крафт / ловушки -> в текущий район города
    if screen in _BACK_TO_DISTRICT:
        await _show_current_district(message, player)
        return

    # 3) Районы / доска / гильдии -> в городской хаб
    if screen in _BACK_TO_CITY:
        await _show_city_hub(message, player)
        return

    # 4) Вторичные разделы -> в корневое меню
    if screen in _BACK_TO_ROOT:
        await _show_root_menu(message, player)
        return

    # 5) Любой неизвестный экран -> безопасный возврат домой
    await _show_root_menu(message, player)
