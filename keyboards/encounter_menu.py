"""
Меню боя — v3.1: InlineKeyboard вместо ReplyKeyboard.

Преимущества:
- Не засоряет основное меню
- Не конфликтует с текстовыми обработчиками
- Кнопки привязаны к конкретному сообщению о встрече
- Можно обновлять (edit_message) без флуда
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def encounter_inline_menu(
    has_trap: bool = True,
    has_poison_trap: bool = True,
    has_multiple_monsters: bool = False,
) -> InlineKeyboardMarkup:
    """Inline-меню боя — 2 ряда по 2 кнопки + ловушки + смена монстра."""
    rows = [
        [
            InlineKeyboardButton(text="⚔️ Атаковать", callback_data="fight:attack"),
            InlineKeyboardButton(text="✨ Навык",      callback_data="fight:skill"),
        ],
        [
            InlineKeyboardButton(text="🎯 Поймать",   callback_data="fight:capture"),
            InlineKeyboardButton(text="🏃 Убежать",   callback_data="fight:flee"),
        ],
    ]
    trap_row = []
    if has_trap:
        trap_row.append(InlineKeyboardButton(text="🪤 Ловушка",      callback_data="fight:trap"))
    if has_poison_trap:
        trap_row.append(InlineKeyboardButton(text="☠️ Яд. ловушка", callback_data="fight:poison_trap"))
    if trap_row:
        rows.append(trap_row)
    # Кнопка смены монстра — если у игрока есть другие живые монстры
    if has_multiple_monsters:
        rows.append([
            InlineKeyboardButton(text="🔄 Сменить монстра", callback_data="fight:switch")
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dungeon_fight_inline_menu() -> InlineKeyboardMarkup:
    """Inline-меню боя в подземелье (без поимки)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚔️ Сразиться",  callback_data="dungeon:fight"),
            InlineKeyboardButton(text="🏃 Покинуть",   callback_data="dungeon:leave"),
        ],
    ])


# Оставляем fallback reply-меню для случаев когда inline недоступен
def encounter_menu() -> ReplyKeyboardMarkup:
    """Legacy reply-меню боя. Используется только как fallback."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ Атаковать"), KeyboardButton(text="✨ Навык")],
            [KeyboardButton(text="🎯 Поймать"),    KeyboardButton(text="🪤 Ловушка")],
            [KeyboardButton(text="🏃 Убежать")],
        ],
        resize_keyboard=True,
    )
