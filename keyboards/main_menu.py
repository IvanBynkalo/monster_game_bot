from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_IDS

def main_menu(location_slug: str):
    buttons = [
        [KeyboardButton(text="🧭 Профиль"), KeyboardButton(text="🐲 Мои монстры")],
        [KeyboardButton(text="🧾 Сюжет"), KeyboardButton(text="📜 Квесты")],
        [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="🌲 Исследовать")],
        [KeyboardButton(text="🧭 Перемещение"), KeyboardButton(text="🌍 Мир")],
        [KeyboardButton(text="🗺 Карта"), KeyboardButton(text="📍 Локация")],
        [KeyboardButton(text="🧭 Район")],
        [KeyboardButton(text="❤️ Лечить монстра"), KeyboardButton(text="⚡ Восстановить энергию")],
    ]
    # Кнопка админ-панели показывается только администраторам в их собственном чате.
    # В этом проекте меню строится без user_id, поэтому кнопку добавляем всегда, а доступ проверяется в handler.
    buttons.append([KeyboardButton(text="🛠 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
