from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def dungeon_menu(in_room_type: str | None = None):
    rows = []
    if in_room_type in {"combat", "boss"}:
        rows.append([KeyboardButton(text="⚔️ Сразиться"), KeyboardButton(text="🏃 Покинуть подземелье")])
    else:
        rows.append([KeyboardButton(text="➡️ Следующая комната"), KeyboardButton(text="🏃 Покинуть подземелье")])
    rows.append([KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="🐲 Мои монстры")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
