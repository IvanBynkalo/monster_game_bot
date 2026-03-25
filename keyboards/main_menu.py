"""
keyboards/main_menu.py

Единое корневое меню игры.

Логика:
- В путешествии: отдельное компактное меню путешественника.
- В городе: корневое городское меню.
- Вне города: корневое полевое меню.

Важно:
- Reply keyboard здесь отвечает только за крупные разделы.
- Действия внутри экранов должны жить в inline-кнопках или отдельных подменю.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.location_rules import is_city


def main_menu(
    location_slug: str,
    district_slug: str | None = None,
    is_traveling: bool = False,
    telegram_id: int | None = None,
) -> ReplyKeyboardMarkup:
    """
    Возвращает корневое меню в зависимости от контекста игрока.

    Параметры district_slug и telegram_id пока оставлены для совместимости
    с текущими вызовами в проекте.
    """

    # Режим путешествия: минимум кнопок, без лишних отвлечений
    if is_traveling:
        keyboard = [
            [KeyboardButton(text="🚫 Отменить перемещение")],
            [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="🎒 Инвентарь")],
            [KeyboardButton(text="👤 Персонаж"), KeyboardButton(text="📂 Ещё")],
        ]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
        )

    # Городское корневое меню
    if is_city(location_slug):
        keyboard = [
            [KeyboardButton(text="🏙 Город")],
            [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="🎒 Инвентарь")],
            [KeyboardButton(text="👤 Персонаж"), KeyboardButton(text="📂 Ещё")],
        ]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
        )

    # Полевое корневое меню
    keyboard = [
        [KeyboardButton(text="🧭 Локация"), KeyboardButton(text="🗺 Переходы")],
        [KeyboardButton(text="🐲 Мои монстры"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="👤 Персонаж"), KeyboardButton(text="📂 Ещё")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
