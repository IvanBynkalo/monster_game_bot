"""
city_menu.py — Меню города и районов.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import time as _time

# Кэш статусов квестов (10 секунд) чтобы не делать DB запрос на каждый рендер меню
_quest_status_cache: dict[tuple, tuple] = {}  # (uid, key) -> (status, expires_at)
_QUEST_CACHE_TTL = 10  # секунд


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


def _qi(telegram_id: int, base: str, npc_key: str) -> str:
    """Единая функция индикатора квеста для любой кнопки."""
    if not telegram_id:
        return base
    try:
        from database.repositories import get_npc_quest_status
        st = get_npc_quest_status(telegram_id, npc_key)
        if st == "ready":
            return f"{base} (✅)"
        elif st == "active":
            return f"{base} (❗)"
        elif st == "available":
            return f"{base} (📌)"
    except Exception:
        pass
    return base


def _notif_label(telegram_id: int = None) -> str:
    if not telegram_id:
        return "🔔 Уведомления"
    try:
        from game.notification_service import get_unread_count
        n = get_unread_count(telegram_id)
        return f"🔔 Уведомления ({n} 🔵)" if n > 0 else "🔔 Уведомления"
    except Exception:
        return "🔔 Уведомления"


def _orders_label(telegram_id: int = None) -> str:
    if not telegram_id:
        return "📋 Заказы"
    try:
        from game.rare_orders import get_active_orders, check_order_fulfillment
        orders = get_active_orders(telegram_id)
        ready = sum(1 for o in orders if check_order_fulfillment(telegram_id, o))
        total = len(orders)
        if ready > 0:
            return f"📋 Заказы ({ready} ✅)"
        if total > 0:
            return f"📋 Заказы ({total} 📌)"
    except Exception:
        pass
    return "📋 Заказы"


def city_menu(district_slug: str | None = None, telegram_id: int = None) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🏬 Торговый квартал"),
         KeyboardButton(text=_qi(telegram_id, "📜 Доска заказов", "board"))],
        [KeyboardButton(text=_qi(telegram_id, "🏛 Гильдии", "guild_any")),
         KeyboardButton(text="⚒ Ремесленный квартал")],
        [KeyboardButton(text="🐲 Мои монстры"),
         KeyboardButton(text="💎 Кристаллы")],
        [KeyboardButton(text="🎒 Инвентарь"),
         KeyboardButton(text="👤 Персонаж")],
        [KeyboardButton(text="⚔️ Экипировка"),
         KeyboardButton(text=_notif_label(telegram_id))],
        [KeyboardButton(text="📂 Ещё")],
        [KeyboardButton(text="🧭 Перемещение"),
         KeyboardButton(text="🚶 Покинуть город")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def district_actions_menu(district_slug: str, telegram_id: int = None) -> ReplyKeyboardMarkup:
    keyboard = []

    if district_slug == "market_square":
        keyboard = [
            [KeyboardButton(text=_qi(telegram_id, "🎒 Лавка сумок", "mirna")),
             KeyboardButton(text=_qi(telegram_id, "🐲 Рынок монстров", "varg"))],
            [KeyboardButton(text="🧪 Лавка зелий"),
             KeyboardButton(text=_qi(telegram_id, "💰 Скупщик ресурсов", "bort"))],
            [KeyboardButton(text="💎 Кристаллы"),
             KeyboardButton(text="⚔️ Экипировка")],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "craft_quarter":
        keyboard = [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"),
             KeyboardButton(text="🪤 Мастер ловушек")],
            [KeyboardButton(text=_qi(telegram_id, "🔨 Мастерская", "gemma")),
             KeyboardButton(text="🏛 Аукцион")],
            [KeyboardButton(text=_orders_label(telegram_id))],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "guild_quarter":
        # Проверяем статус квестов по всем гильдиям
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
        keyboard = [[KeyboardButton(text="⬅️ Назад")]]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
