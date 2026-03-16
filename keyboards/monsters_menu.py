from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def monsters_menu(monsters: list[dict]):
    keyboard = []
    for monster in monsters:
        if monster.get("is_active"):
            continue
        keyboard.append([KeyboardButton(text=f"✅ {monster['id']}")])
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
