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
    rows = []
    row = []
    for icon, key, label in TABS:
        marker = f"› {icon}" if key == active else icon
        row.append(InlineKeyboardButton(
            text=marker,
            callback_data=f"profile:tab:{key}"
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
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
