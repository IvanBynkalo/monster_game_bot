"""
equipment.py — Хендлеры системы экипировки.
"""
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.repositories import get_player, _update_player_field
from game.equipment_service import (
    EQUIPMENT_CATALOG, SLOT_NAMES, SLOTS,
    get_equipped, get_equipment_inventory, equip_item, unequip_item,
    buy_equipment, repair_boots, render_equipment_panel, get_equipment_bonuses,
)
from keyboards.main_menu import main_menu


def equipment_shop_inline(slot_filter: str | None = None) -> InlineKeyboardMarkup:
    """Inline-меню магазина экипировки."""
    rows = []
    for slug, item in EQUIPMENT_CATALOG.items():
        if slot_filter and item["slot"] != slot_filter:
            continue
        rows.append([InlineKeyboardButton(
            text=f"{item['name']} — {item['price']}з",
            callback_data=f"equip:buy:{slug}"
        )])
    # Фильтры по слотам
    filter_row = []
    for slot in SLOTS:
        icon = SLOT_NAMES[slot].split()[0]
        filter_row.append(InlineKeyboardButton(
            text=icon, callback_data=f"equip:filter:{slot}"
        ))
    rows.append(filter_row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="equip:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_equipment_inline(telegram_id: int) -> InlineKeyboardMarkup:
    """Inline-меню надетой экипировки — снять/починить."""
    equipped = get_equipped(telegram_id)
    inv = get_equipment_inventory(telegram_id)
    rows = []
    for slot in SLOTS:
        item = equipped.get(slot)
        if item:
            rows.append([
                InlineKeyboardButton(text=f"❌ Снять {item['name']}", callback_data=f"equip:unequip:{slot}")
            ])
            if slot == "boots" and item.get("durability", 100) < EQUIPMENT_CATALOG.get(item["slug"], {}).get("durability", 100):
                rows.append([InlineKeyboardButton(text="🔧 Починить сапоги", callback_data="equip:repair")])
    # Предметы в инвентаре
    if inv:
        rows.append([InlineKeyboardButton(text="📦 Надеть из инвентаря", callback_data="equip:inventory")])
    rows.append([InlineKeyboardButton(text="🛒 В магазин экипировки", callback_data="equip:shop")])
    rows.append([InlineKeyboardButton(text="⬅️ Закрыть", callback_data="equip:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def inventory_equip_inline(items: list[dict]) -> InlineKeyboardMarkup:
    """Список предметов в инвентаре для надевания."""
    rows = []
    for item in items:
        rows.append([InlineKeyboardButton(
            text=f"👆 Надеть {item['name']} (прочн. {item['durability']})",
            callback_data=f"equip:wear:{item['slug']}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="equip:myequip")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def equipment_handler(message: Message):
    """Показывает экипировку персонажа."""
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    panel = render_equipment_panel(message.from_user.id)
    await message.answer(panel, reply_markup=my_equipment_inline(message.from_user.id))


async def equipment_callback(callback: CallbackQuery):
    """Обрабатывает все equip: коллбэки."""
    data = callback.data
    uid = callback.from_user.id
    player = get_player(uid)
    if not player:
        await callback.answer("Сначала /start")
        return
    await callback.answer()

    if data == "equip:myequip" or data == "equip:close":
        if data == "equip:close":
            try:
                await callback.message.delete()
            except Exception:
                pass
            return
        panel = render_equipment_panel(uid)
        await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))

    elif data == "equip:shop" or data.startswith("equip:filter:"):
        slot_filter = data.split(":")[-1] if data.startswith("equip:filter:") else None
        if slot_filter == "shop":
            slot_filter = None
        shop_text = "🛒 Магазин экипировки\n\nВыбери предмет:"
        if slot_filter:
            shop_text += f" (фильтр: {SLOT_NAMES.get(slot_filter, slot_filter)})"
        await callback.message.edit_text(shop_text,
                                          reply_markup=equipment_shop_inline(slot_filter))

    elif data.startswith("equip:buy:"):
        slug = data.split(":", 2)[-1]
        ok, msg, new_gold = buy_equipment(uid, slug, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            panel = render_equipment_panel(uid)
            await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))

    elif data.startswith("equip:unequip:"):
        slot = data.split(":", 2)[-1]
        ok, msg = unequip_item(uid, slot)
        await callback.answer(msg, show_alert=True)
        if ok:
            panel = render_equipment_panel(uid)
            await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))

    elif data == "equip:inventory":
        inv = get_equipment_inventory(uid)
        if not inv:
            await callback.answer("Инвентарь экипировки пуст.", show_alert=True)
            return
        await callback.message.edit_text(
            "📦 Инвентарь экипировки\nВыбери предмет для надевания:",
            reply_markup=inventory_equip_inline(inv)
        )

    elif data.startswith("equip:wear:"):
        slug = data.split(":", 2)[-1]
        ok, msg = equip_item(uid, slug)
        await callback.answer(msg, show_alert=True)
        if ok:
            panel = render_equipment_panel(uid)
            await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))

    elif data == "equip:repair":
        ok, msg, new_gold = repair_boots(uid, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            panel = render_equipment_panel(uid)
            await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))
