"""
Главное меню — v3.1
Вне города: контекстное меню по данным локации.
В городе: city_menu.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.location_rules import is_city
from keyboards.city_menu import city_menu



def _get_notif_label(telegram_id: int = None) -> str:
    try:
        if not telegram_id:
            return "🔔 Уведомления"
        from game.notification_service import get_unread_count
        n = get_unread_count(telegram_id)
        return f"🔔 Уведомления ({n} 🔵)" if n > 0 else "🔔 Уведомления"
    except Exception:
        return "🔔 Уведомления"

def main_menu(location_slug: str, district_slug: str | None = None,
              is_traveling: bool = False, telegram_id: int = None) -> ReplyKeyboardMarkup:
    # Если игрок в пути — всегда показываем меню путешественника,
    # даже если физически ещё находится в городе
    if is_traveling:
        keyboard = [
            [KeyboardButton(text="🚫 Отменить перемещение"), KeyboardButton(text="🐲 Мои монстры")],
            [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="👤 Персонаж")],
            [KeyboardButton(text="📂 Ещё")],
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    if is_city(location_slug):
        return city_menu(district_slug, telegram_id=telegram_id)

    keyboard = [
        [KeyboardButton(text="🗺 Мир / переходы"), KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="👤 Персонаж")],
        [KeyboardButton(text="📂 Ещё")],
    ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
