"""
keyboards/more_menu.py

Подменю «Ещё».

Задача:
- собрать второстепенные, служебные и обзорные разделы в одном месте;
- не перегружать главное меню;
- сохранить совместимость с текущими обработчиками bot.py.

Важно:
- Тексты кнопок оставлены совместимыми с уже существующими хендлерами.
- Здесь НЕ должно быть навигации по локациям/городу — только доп. разделы.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def more_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Меню второго уровня для раздела «Ещё».

    Структура:
    1. Журналы / задачи
    2. Сервис и восстановление
    3. Коллекции / лор
    4. Спецразделы
    5. Назад
    """

    keyboard = [
        # Игровые задачи и дневные/недельные активности
        [KeyboardButton(text="📜 Квесты"), KeyboardButton(text="🧾 Сюжет")],
        [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="🎯 Охота недели")],

        # Сервисные разделы
        [KeyboardButton(text="❤️ Лечение"), KeyboardButton(text="🔔 Уведомления")],

        # Лор / коллекции
        [KeyboardButton(text="🔮 Реликвии"), KeyboardButton(text="📖 Кодекс")],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="🛠 Админ-панель")])

    keyboard.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
