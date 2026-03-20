"""
Меню монстров — v3.1: список через InlineKeyboard.
Каждый монстр — inline-кнопка, удобно листать без флуда reply-кнопками.
"""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from game.infection_service import INFECTION_STAGE_LABELS


def monsters_inline_menu(monsters: list[dict]) -> InlineKeyboardMarkup:
    """
    Inline-список монстров для выбора активного.
    Каждая кнопка показывает: имя, уровень, HP, стадию мутации.
    """
    rows = []
    for m in monsters:
        active_mark = "✅ " if m.get("is_active") else ""
        stage = m.get("infection_stage", 0)
        stage_icon = {0: "", 1: "〰", 2: "🌀", 3: "🔮", 4: "💀"}.get(stage, "")
        combo = "⚡" if m.get("combo_mutation") else ""
        listed = "🏷" if m.get("is_listed") else ""
        label = (
            f"{active_mark}{m['name']} "
            f"Ур.{m.get('level',1)} "
            f"HP:{m.get('current_hp', m['hp'])}/{m.get('max_hp', m['hp'])} "
            f"{stage_icon}{combo}{listed}"
        ).strip()
        rows.append([InlineKeyboardButton(
            text=label,
            callback_data=f"monster:select:{m['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def monster_actions_inline(monster: dict) -> InlineKeyboardMarkup:
    """
    Inline-меню действий с конкретным монстром.
    Показывается под карточкой монстра.
    """
    mid = monster["id"]
    is_active = monster.get("is_active", False)
    is_listed = monster.get("is_listed", False)
    rows = []

    if not is_active:
        rows.append([InlineKeyboardButton(text="✅ Сделать активным", callback_data=f"monster:activate:{mid}")])

    rows.append([InlineKeyboardButton(text="❤️ Лечить монстра", callback_data=f"monster:heal:{mid}")])

    if not is_active:
        if is_listed:
            rows.append([InlineKeyboardButton(text="🏷 Снять с продажи", callback_data=f"monster:delist:{mid}")])
        else:
            rows.append([InlineKeyboardButton(text="🏪 Выставить на P2P", callback_data=f"monster:list:{mid}")])

    rows.append([InlineKeyboardButton(text="⬅️ К списку", callback_data="monster:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Legacy reply-меню — используется в некоторых старых хендлерах как fallback
def monsters_menu(monsters: list[dict]) -> ReplyKeyboardMarkup:
    keyboard = []
    for monster in monsters:
        if monster.get("is_active"):
            continue
        keyboard.append([KeyboardButton(text=f"✅ {monster['id']}")])
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
