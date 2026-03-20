from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.repositories import get_player
from game.bestiary_service import render_bestiary, get_bestiary_count
from keyboards.main_menu import main_menu


def bestiary_tabs(active: str = "wildlife") -> InlineKeyboardMarkup:
    sections = [
        ("🐾", "wildlife", "Звери"),
        ("👾", "monsters", "Монстры"),
        ("💀", "bosses",   "Боссы"),
    ]
    rows = []
    for icon, key, label in sections:
        text = f"› {icon} {label}" if key == active else f"{icon} {label}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"bestiary:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def codex_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    stats = get_bestiary_count(message.from_user.id)
    header = (
        f"📖 Кодекс существ\n\n"
        f"🐾 Зверей: {stats['wildlife']}/{stats['wildlife_total']}\n"
        f"👾 Монстров: {stats['monster']}\n"
        f"💀 Боссов: {stats['boss']}\n\n"
        f"Выбери раздел:"
    )
    await message.answer(header, reply_markup=main_menu(player.location_slug))
    await message.answer(
        render_bestiary(message.from_user.id, "wildlife"),
        reply_markup=bestiary_tabs("wildlife"),
    )


async def bestiary_callback(callback: CallbackQuery):
    section = callback.data.split(":")[1]
    uid = callback.from_user.id
    await callback.answer()
    try:
        await callback.message.edit_text(
            render_bestiary(uid, section),
            reply_markup=bestiary_tabs(section),
        )
    except Exception:
        await callback.message.answer(
            render_bestiary(uid, section),
            reply_markup=bestiary_tabs(section),
        )
