from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def dungeon_menu(in_room_type: str | None = None, completed: bool = False):
    rows = []

    if completed:
        rows.append([KeyboardButton(text="🏃 Покинуть подземелье")])
    elif in_room_type in {"combat", "elite", "boss"}:
        rows.append([KeyboardButton(text="⚔️ Сразиться"), KeyboardButton(text="🏃 Покинуть подземелье")])
    else:
        rows.append([KeyboardButton(text="➡️ Следующая комната"), KeyboardButton(text="🏃 Покинуть подземелье")])

    rows.append([KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="🐲 Мои монстры")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
