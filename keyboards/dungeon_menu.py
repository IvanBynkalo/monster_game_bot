from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def dungeon_menu(in_room_type: str | None = None, completed: bool = False):
    rows = []

    if completed:
        rows.append([KeyboardButton(text="🏃 Покинуть подземелье")])
    elif in_room_type in {"combat", "elite", "boss"}:
        rows.append(
            [
                KeyboardButton(text="⚔️ Сразиться"),
                KeyboardButton(text="🏃 Покинуть подземелье"),
            ]
        )
    else:
        rows.append(
            [
                KeyboardButton(text="➡️ Следующая комната"),
                KeyboardButton(text="🏃 Покинуть подземелье"),
            ]
        )

    rows.append(
        [
            KeyboardButton(text="👤 Персонаж"),
            KeyboardButton(text="🐲 Мои монстры"),
        ]
    )
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def dungeon_choice_menu(choices: list[dict]):
    rows = []
    for choice in choices:
        rows.append(
            [
                InlineKeyboardButton(
                    text=choice["text"],
                    callback_data=f"dungeon:choice:{choice['id']}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="🏃 Покинуть подземелье",
                callback_data="dungeon:leave_inline",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
