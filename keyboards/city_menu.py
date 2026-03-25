"""
keyboards/city_menu.py

Единое городское меню и меню районов города.

Цели:
- сделать город логичным хабом;
- не смешивать районные действия и глобальные разделы игрока;
- сохранить совместимость с текущими обработчиками bot.py / handlers/*.py;
- сохранить индикаторы квестов и уведомлений.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import time as _time

# ──────────────────────────────────────────────────────────────────────────────
# Кэш статусов квестов
# ──────────────────────────────────────────────────────────────────────────────

_quest_status_cache: dict[tuple, tuple] = {}  # (uid, key) -> (status, expires_at)
_QUEST_CACHE_TTL = 10  # секунд


def invalidate_quest_status_cache(telegram_id: int, npc_key: str | None = None):
    """Сбрасывает кэш индикаторов квестов для игрока."""
    keys_to_delete = []
    for key in list(_quest_status_cache.keys()):
        uid, current_key = key
        if uid != telegram_id:
            continue
        if npc_key is None or current_key == npc_key:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        _quest_status_cache.pop(key, None)


def _cached_quest_status(telegram_id: int, npc_key: str) -> str | None:
    """Возвращает статус квеста с кэшированием."""
    cache_key = (telegram_id, npc_key)
    now = _time.time()

    if cache_key in _quest_status_cache:
        status, expires = _quest_status_cache[cache_key]
        if now < expires:
            return status

    try:
        from database.repositories import get_npc_quest_status
        status = get_npc_quest_status(telegram_id, npc_key)
    except Exception:
        status = None

    _quest_status_cache[cache_key] = (status, now + _QUEST_CACHE_TTL)
    return status


def _qi(telegram_id: int | None, base: str, npc_key: str) -> str:
    """
    Индикатор состояния квеста для кнопок.
    available -> 📌
    active    -> ❗
    ready     -> ✅
    """
    if not telegram_id:
        return base

    try:
        st = _cached_quest_status(telegram_id, npc_key)
        if st == "ready":
            return f"{base} (✅)"
        if st == "active":
            return f"{base} (❗)"
        if st == "available":
            return f"{base} (📌)"
    except Exception:
        pass

    return base


def _notif_label(telegram_id: int | None = None) -> str:
    if not telegram_id:
        return "🔔 Уведомления"

    try:
        from game.notification_service import get_unread_count
        unread = get_unread_count(telegram_id)
        return f"🔔 Уведомления ({unread} 🔵)" if unread > 0 else "🔔 Уведомления"
    except Exception:
        return "🔔 Уведомления"


# ──────────────────────────────────────────────────────────────────────────────
# Главное меню города
# ──────────────────────────────────────────────────────────────────────────────

def city_menu(district_slug: str | None = None, telegram_id: int | None = None) -> ReplyKeyboardMarkup:
    """
    Корневое меню города.

    Принцип:
    1. Верхняя часть — городские разделы.
    2. Нижняя часть — глобальные разделы игрока.
    3. Квартальные экраны и конкретные продавцы открываются уже внутри city/district handlers.
    """

    keyboard = [
        [KeyboardButton(text="🏙 Город")],

        [KeyboardButton(text="🏬 Торговый квартал"),
         KeyboardButton(text=_qi(telegram_id, "🏛 Гильдии", "guild_any"))],

        [KeyboardButton(text="⚒ Ремесленный квартал"),
         KeyboardButton(text=_qi(telegram_id, "📜 Доска заказов", "board"))],

        [KeyboardButton(text="🧭 Перемещение"),
         KeyboardButton(text="🚶 Покинуть город")],

        [KeyboardButton(text="🐲 Мои монстры"),
         KeyboardButton(text="🎒 Инвентарь")],

        [KeyboardButton(text="👤 Персонаж"),
         KeyboardButton(text="💎 Кристаллы")],

        [KeyboardButton(text="⚔️ Экипировка"),
         KeyboardButton(text=_notif_label(telegram_id))],

        [KeyboardButton(text="📂 Ещё")],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Меню действий внутри районов города
# ──────────────────────────────────────────────────────────────────────────────

def district_actions_menu(district_slug: str, telegram_id: int | None = None) -> ReplyKeyboardMarkup:
    """
    Локальное меню действий для конкретного района города.

    Здесь только то, что логически относится к району.
    Глобальные разделы игрока (инвентарь/персонаж/монстры) сюда не добавляем.
    """

    if district_slug == "market_square":
        keyboard = [
            [KeyboardButton(text=_qi(telegram_id, "🎒 Лавка сумок", "mirna")),
             KeyboardButton(text=_qi(telegram_id, "🐲 Рынок монстров", "varg"))],

            [KeyboardButton(text="🧪 Лавка зелий"),
             KeyboardButton(text=_qi(telegram_id, "💰 Скупщик ресурсов", "bort"))],

            [KeyboardButton(text=_qi(telegram_id, "📜 Доска заказов", "board"))],

            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "craft_quarter":
        keyboard = [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"),
             KeyboardButton(text="🪤 Мастер ловушек")],

            [KeyboardButton(text=_qi(telegram_id, "🔨 Мастерская", "gemma")),
             KeyboardButton(text="🏛 Аукцион")],

            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "guild_quarter":
        keyboard = [
            [KeyboardButton(text=_qi(telegram_id, "🎯 Гильдия ловцов", "hunter")),
             KeyboardButton(text=_qi(telegram_id, "🌿 Гильдия собирателей", "gatherer"))],

            [KeyboardButton(text=_qi(telegram_id, "⛏ Гильдия геологов", "geologist")),
             KeyboardButton(text=_qi(telegram_id, "⚗ Гильдия алхимиков", "alchemist"))],

            [KeyboardButton(text="🌌 Алтарь рождения")],

            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "main_gate":
        keyboard = [
            [KeyboardButton(text="🚶 Покинуть город")],
            [KeyboardButton(text="🛡 Городская стража")],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    else:
        keyboard = [
            [KeyboardButton(text="⬅️ Назад")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
