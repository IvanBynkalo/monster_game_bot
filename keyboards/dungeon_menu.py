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


def _get_risk_emoji(chance: float) -> str:
    percent = int(chance * 100)

    if percent < 50:
        return "🔴"  # опасно
    elif percent < 75:
        return "🟡"  # риск
    else:
        return "🟢"  # безопасно


def _get_stat_hint(stat: str | None) -> str:
    if stat == "strength":
        return " • сила"
    if stat == "intellect":
        return " • интеллект"
    if stat == "agility":
        return " • ловкость"
    if stat == "defense":
        return " • защита"
    return ""


def dungeon_choice_menu(choices: list[dict], player=None):
    from handlers.dungeon import calculate_choice_chance

    rows = []

    for choice in choices:
        text = choice["text"]

        if player:
            chance = calculate_choice_chance(player, choice)
            percent = int(chance * 100)
            risk = _get_risk_emoji(chance)
            stat_hint = _get_stat_hint(choice.get("stat"))

            text = f"{risk} {text} ({percent}%){stat_hint}"

        rows.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"dungeon:choice:{choice['id']}",
                )
            ]
        )

    # кнопка выхода (inline)
    rows.append(
        [
            InlineKeyboardButton(
                text="🏃 Покинуть подземелье",
                callback_data="dungeon:leave_inline",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
