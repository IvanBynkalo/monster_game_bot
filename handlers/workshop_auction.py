"""
workshop_auction.py — Хендлеры Мастерской Геммы и Аукциона.
"""
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.repositories import get_player, _update_player_field
from game.crystal_workshop import (
    repair_crystal, upgrade_volume, change_resonance, identify_crystal,
    buy_shards, render_workshop_menu, RESONANCE_OPTIONS,
    REPAIR_COSTS, UPGRADE_COSTS, RESONANCE_CHANGE_COST, IDENTIFY_COST,
)
from game.auction_service import (
    get_active_lots, place_bid, render_auction,
)
from game.crystal_service import get_player_crystals, get_crystal
from keyboards.main_menu import main_menu


# ── Мастерская ────────────────────────────────────────────────────────────────

def workshop_inline(telegram_id: int) -> InlineKeyboardMarkup:
    crystals = get_player_crystals(telegram_id)
    rows = []
    for c in crystals:
        state = c.get("state", "normal")
        if state != "normal":
            label = f"🔧 Починить {c['name']} ({state})"
            rows.append([InlineKeyboardButton(text=label, callback_data=f"ws:repair:{c['id']}")])
        rows.append([InlineKeyboardButton(
            text=f"⬆️ Улучшить {c['name']} ({c['max_volume']} объём)",
            callback_data=f"ws:upgrade:{c['id']}"
        )])
        rows.append([InlineKeyboardButton(
            text=f"🔍 Идентифицировать {c['name']} — {IDENTIFY_COST}з",
            callback_data=f"ws:identify:{c['id']}"
        )])
        rows.append([InlineKeyboardButton(
            text=f"🔄 Сменить резонанс {c['name']}",
            callback_data=f"ws:resonance:{c['id']}"
        )])
        if state == "broken":
            rows.append([InlineKeyboardButton(
                text=f"🪨 Продать осколки {c['name']}",
                callback_data=f"ws:shards:{c['id']}"
            )])
    rows.append([InlineKeyboardButton(text="⬅️ Закрыть", callback_data="ws:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def resonance_kb(crystal_id: int) -> InlineKeyboardMarkup:
    rows = []
    for code, label in RESONANCE_OPTIONS.items():
        rows.append([InlineKeyboardButton(
            text=f"{label} — {RESONANCE_CHANGE_COST}з",
            callback_data=f"ws:set_res:{crystal_id}:{code}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="ws:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def workshop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала /start")
        return
    text = render_workshop_menu(message.from_user.id)
    await message.answer(text, reply_markup=workshop_inline(message.from_user.id))


async def workshop_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    player = get_player(uid)
    if not player:
        await callback.answer("Сначала /start")
        return
    data = callback.data
    await callback.answer()

    if data == "ws:close":
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    elif data == "ws:back":
        text = render_workshop_menu(uid)
        await callback.message.edit_text(text, reply_markup=workshop_inline(uid))

    elif data.startswith("ws:repair:"):
        cid = int(data.split(":")[-1])
        ok, msg, new_gold = repair_crystal(uid, cid, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            await callback.message.edit_text(
                render_workshop_menu(uid), reply_markup=workshop_inline(uid)
            )

    elif data.startswith("ws:upgrade:"):
        cid = int(data.split(":")[-1])
        ok, msg, new_gold = upgrade_volume(uid, cid, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            await callback.message.edit_text(
                render_workshop_menu(uid), reply_markup=workshop_inline(uid)
            )

    elif data.startswith("ws:identify:"):
        cid = int(data.split(":")[-1])
        ok, msg, new_gold = identify_crystal(uid, cid, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        if ok:
            await callback.message.answer(msg)
        else:
            await callback.answer(msg, show_alert=True)

    elif data.startswith("ws:resonance:"):
        cid = int(data.split(":")[-1])
        crystal = get_crystal(cid)
        if not crystal:
            await callback.answer("Кристалл не найден.", show_alert=True)
            return
        await callback.message.edit_text(
            f"🔄 Смена резонанса {crystal['name']}\n"
            f"Текущий: {crystal['emotion_affinity']}\n"
            f"Стоимость: {RESONANCE_CHANGE_COST}з\n\nВыбери новый:",
            reply_markup=resonance_kb(cid)
        )

    elif data.startswith("ws:set_res:"):
        parts = data.split(":")
        cid = int(parts[2])
        new_res = parts[3]
        ok, msg, new_gold = change_resonance(uid, cid, new_res, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            await callback.message.edit_text(
                render_workshop_menu(uid), reply_markup=workshop_inline(uid)
            )

    elif data.startswith("ws:shards:"):
        cid = int(data.split(":")[-1])
        ok, msg, new_gold = buy_shards(uid, cid, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            await callback.message.edit_text(
                render_workshop_menu(uid), reply_markup=workshop_inline(uid)
            )


# ── Аукцион ───────────────────────────────────────────────────────────────────

def auction_inline(telegram_id: int) -> InlineKeyboardMarkup:
    lots = get_active_lots()
    rows = []
    for i, lot in enumerate(lots, 1):
        min_bid = int(lot["current_bid"] * 1.10)
        is_winning = lot["top_bidder"] == telegram_id
        mark = " 🏆" if is_winning else ""
        rows.append([InlineKeyboardButton(
            text=f"Лот {i}: ставка {min_bid}з{mark}",
            callback_data=f"auc:bid:{lot['id']}:{min_bid}"
        )])
    rows.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="auc:refresh")])
    rows.append([InlineKeyboardButton(text="⬅️ Закрыть", callback_data="auc:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def auction_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала /start")
        return
    text = render_auction(message.from_user.id)
    await message.answer(text, reply_markup=auction_inline(message.from_user.id))


async def auction_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    player = get_player(uid)
    if not player:
        await callback.answer("Сначала /start")
        return
    data = callback.data
    await callback.answer()

    if data == "auc:close":
        try:
            await callback.message.delete()
        except Exception:
            pass

    elif data == "auc:refresh":
        text = render_auction(uid)
        try:
            await callback.message.edit_text(text, reply_markup=auction_inline(uid))
        except Exception:
            pass

    elif data.startswith("auc:bid:"):
        parts = data.split(":")
        lot_id = int(parts[2])
        amount = int(parts[3])
        ok, msg, new_gold = place_bid(uid, lot_id, amount, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            text = render_auction(uid)
            try:
                await callback.message.edit_text(text, reply_markup=auction_inline(uid))
            except Exception:
                pass


# ── Рынок редких заказов ─────────────────────────────────────────────────────

from game.rare_orders import (
    get_active_orders, check_order_fulfillment, complete_order, render_orders,
)


def orders_inline(telegram_id: int) -> InlineKeyboardMarkup:
    orders = get_active_orders(telegram_id)
    rows = []
    for o in orders:
        can_do = check_order_fulfillment(telegram_id, o)
        label = f"{'✅' if can_do else '📋'} {o['title']} — {o['reward_gold']}з"
        rows.append([InlineKeyboardButton(
            text=label,
            callback_data=f"ord:submit:{o['id']}"
        )])
    rows.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="ord:refresh")])
    rows.append([InlineKeyboardButton(text="⬅️ Закрыть", callback_data="ord:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def orders_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала /start")
        return
    text = render_orders(message.from_user.id)
    await message.answer(text, reply_markup=orders_inline(message.from_user.id))


async def orders_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    player = get_player(uid)
    if not player:
        await callback.answer("Сначала /start")
        return
    data = callback.data
    await callback.answer()

    if data == "ord:close":
        try:
            await callback.message.delete()
        except Exception:
            pass

    elif data == "ord:refresh":
        text = render_orders(uid)
        try:
            await callback.message.edit_text(text, reply_markup=orders_inline(uid))
        except Exception:
            pass

    elif data.startswith("ord:submit:"):
        order_id = data.split(":", 2)[-1]
        ok, msg, _ = complete_order(uid, order_id, player.gold)
        # complete_order internally calls add_player_gold - no need to update field
        if ok:
            await callback.message.answer(msg)  # показываем как обычное сообщение
            text = render_orders(uid)
            try:
                await callback.message.edit_text(text, reply_markup=orders_inline(uid))
            except Exception:
                await callback.message.answer(text, reply_markup=orders_inline(uid))
        else:
            await callback.answer(msg, show_alert=True)
