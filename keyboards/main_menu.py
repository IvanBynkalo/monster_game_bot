"""
Главное меню — v3.1
Вне города: контекстное меню по данным локации.
В городе: city_menu.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.location_rules import is_city
from keyboards.city_menu import city_menu



def _get_notif_label(telegram_id: int = None) -> str:
    if not telegram_id:
        return "🔔 Уведомления"
    try:
        from game.notification_service import get_unread_count
        n = get_unread_count(telegram_id)
        return f"🔔 Уведомления ({n})" if n > 0 else "🔔 Уведомления"
    except Exception:
        return "🔔 Уведомления"

def main_menu(location_slug: str, district_slug: str | None = None,
              is_traveling: bool = False, telegram_id: int = None) -> ReplyKeyboardMarkup:
    if is_city(location_slug):
        return city_menu(district_slug, telegram_id=telegram_id)

    # Кнопка перемещения меняется во время путешествия
    move_btn = KeyboardButton(text="🚫 Отменить перемещение") if is_traveling else KeyboardButton(text="🧭 Переместиться")

    # Чистое меню — Собирать и Подземелье теперь в inline под сообщением локации
    keyboard = [
        [move_btn, KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="🎒 Инвентарь"),     KeyboardButton(text="👤 Персонаж")],
        [KeyboardButton(text="📂 Ещё")],
    ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
