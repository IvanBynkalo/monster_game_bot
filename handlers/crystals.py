"""
crystals.py — Хендлеры системы кристаллов.
"""
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.repositories import get_player, _update_player_field
from game.crystal_service import (
    CRYSTAL_TEMPLATES, get_player_crystals, get_crystal, get_monsters_in_crystal,
    create_crystal, render_crystal_list, render_crystal_detail,
    summon_monster, find_free_crystal, calculate_monster_volume,
    recalculate_crystal_load, repair_crystal, get_bond_level, get_combat_modifiers,
)
from keyboards.main_menu import main_menu


def crystals_list_inline(telegram_id: int) -> InlineKeyboardMarkup:
    crystals = get_player_crystals(telegram_id)
    rows = []
    for c in crystals:
        free = c["max_volume"] - c["current_volume"]
        label = f"{c['name']} [{c['current_volume']}/{c['max_volume']}]"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"crystal:open:{c['id']}")])
    rows.append([InlineKeyboardButton(text="🛒 Купить кристалл", callback_data="crystal:shop")])
    rows.append([InlineKeyboardButton(text="⬅️ Закрыть", callback_data="crystal:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def crystal_detail_inline(crystal_id: int, telegram_id: int) -> InlineKeyboardMarkup:
    crystal = get_crystal(crystal_id)
    monsters = get_monsters_in_crystal(crystal_id)
    rows = []
    for m in monsters:
        if m.get("is_dead"):
            rows.append([InlineKeyboardButton(
                text=f"💀 {m['name']} (пал)",
                callback_data=f"crystal:info:{m['id']}"
            )])
            continue
        bond = get_bond_level(m["id"], crystal_id)
        bond_str = f" 🔗{bond}" if bond > 0 else ""
        if m.get("is_summoned"):
            rows.append([InlineKeyboardButton(
                text=f"⚡ {m['name']} ур.{m['level']}{bond_str} (активен)",
                callback_data=f"crystal:info:{m['id']}"
            )])
        else:
            rows.append([InlineKeyboardButton(
                text=f"✨ Призвать {m['name']} ур.{m['level']}{bond_str}",
                callback_data=f"crystal:summon:{m['id']}"
            )])
    # Ремонт если кристалл треснут
    if crystal and crystal.get("state") in ("cracked", "broken"):
        state_label = "⚠️ Починить (треснут)" if crystal["state"] == "cracked" else "💔 Починить (разбит)"
        rows.append([InlineKeyboardButton(text=state_label, callback_data=f"crystal:repair:{crystal_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ К списку кристаллов", callback_data="crystal:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def crystal_shop_inline() -> InlineKeyboardMarkup:
    rows = []
    for code, tmpl in CRYSTAL_TEMPLATES.items():
        rows.append([InlineKeyboardButton(
            text=f"{tmpl['name']} — {tmpl['buy_price']}з ({tmpl['max_monsters']} монстра, {tmpl['max_volume']} объём)",
            callback_data=f"crystal:buy:{code}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="crystal:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def crystals_handler(message: Message):
    """Открывает список кристаллов."""
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    text = render_crystal_list(message.from_user.id)
    await message.answer(text, reply_markup=crystals_list_inline(message.from_user.id))


async def crystal_callback(callback: CallbackQuery):
    """Обрабатывает все crystal: коллбэки."""
    data = callback.data
    uid = callback.from_user.id
    player = get_player(uid)
    if not player:
        await callback.answer("Сначала /start")
        return
    await callback.answer()

    if data == "crystal:list":
        text = render_crystal_list(uid)
        try:
            await callback.message.edit_text(text, reply_markup=crystals_list_inline(uid))
        except Exception:
            await callback.message.answer(text, reply_markup=crystals_list_inline(uid))

    elif data.startswith("crystal:open:"):
        cid = int(data.split(":")[-1])
        crystal = get_crystal(cid)
        if not crystal or crystal["telegram_id"] != uid:
            await callback.answer("Кристалл не найден.", show_alert=True)
            return
        recalculate_crystal_load(cid)
        text = render_crystal_detail(cid)
        try:
            await callback.message.edit_text(text, reply_markup=crystal_detail_inline(cid, uid))
        except Exception:
            await callback.message.answer(text, reply_markup=crystal_detail_inline(cid, uid))

    elif data.startswith("crystal:summon:"):
        monster_id = int(data.split(":")[-1])
        ok, msg = summon_monster(uid, monster_id)
        await callback.answer(msg, show_alert=True)
        if ok:
            text = render_crystal_list(uid)
            try:
                await callback.message.edit_text(text, reply_markup=crystals_list_inline(uid))
            except Exception:
                pass

    elif data == "crystal:shop":
        if not player or player.location_slug != "silver_city":
            await callback.answer("Кристаллы продаются только в Сереброграде.", show_alert=True)
            return
        try:
            await callback.message.edit_text(
                "🛒 Магазин кристаллов\n\nВыбери кристалл для покупки:",
                reply_markup=crystal_shop_inline()
            )
        except Exception:
            await callback.message.answer(
                "🛒 Магазин кристаллов\n\nВыбери кристалл для покупки:",
                reply_markup=crystal_shop_inline()
            )

    elif data.startswith("crystal:buy:"):
        code = data.split(":", 2)[-1]
        tmpl = CRYSTAL_TEMPLATES.get(code)
        if not tmpl:
            await callback.answer("Кристалл не найден.", show_alert=True)
            return
        if player.gold < tmpl["buy_price"]:
            await callback.answer(
                f"Недостаточно золота! Нужно {tmpl['buy_price']}з, у тебя {player.gold}з",
                show_alert=True
            )
            return
        _update_player_field(uid, gold=player.gold - tmpl["buy_price"])
        crystal = create_crystal(uid, code)
        await callback.answer(f"✅ Куплен {crystal['name']}!", show_alert=False)
        text = render_crystal_list(uid)
        try:
            await callback.message.edit_text(text, reply_markup=crystals_list_inline(uid))
        except Exception:
            await callback.message.answer(text, reply_markup=crystals_list_inline(uid))

    elif data.startswith("crystal:repair:"):
        cid = int(data.split(":")[-1])
        ok, msg, new_gold = repair_crystal(uid, cid, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            recalculate_crystal_load(cid)
            text = render_crystal_detail(cid)
            try:
                await callback.message.edit_text(text, reply_markup=crystal_detail_inline(cid, uid))
            except Exception:
                pass

    elif data == "crystal:close":
        try:
            await callback.message.delete()
        except Exception:
            pass
