"""
Inline-меню профиля — вкладки вместо длинного текста.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TABS = [
    ("📊", "main",   "Основное"),
    ("🐲", "monster","Монстр"),
    ("💪", "stats",  "Характеристики"),
    ("📈", "progress","Развитие"),
    ("🎓", "prof",   "Профессии"),
    ("✨", "emo",    "Эмоции"),
    ("🎒", "effects","Эффекты"),
]


def profile_tabs(active: str = "main") -> InlineKeyboardMarkup:
    # Две вкладки в ряд для компактности на мобильных
    buttons = []
    for icon, key, label in TABS:
        text = f"› {icon} {label}" if key == active else f"{icon} {label}"
        buttons.append(InlineKeyboardButton(text=text, callback_data=f"profile:tab:{key}"))

    rows = []
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i+2])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def stat_spend_inline(stat_points: int) -> InlineKeyboardMarkup:
    """Inline-кнопки трат очков характеристик — показываются во вкладке Развитие."""
    if stat_points <= 0:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нет свободных очков", callback_data="profile:noop")]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💪 +Сила",     callback_data="profile:stat:strength"),
            InlineKeyboardButton(text="🤸 +Ловкость", callback_data="profile:stat:agility"),
            InlineKeyboardButton(text="🧠 +Интеллект",callback_data="profile:stat:intellect"),
        ]
    ])
