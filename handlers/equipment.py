"""
equipment.py — Магазин экипировки у торговца Брума.

UX: категория → список → карточка предмета → купить/назад
"""
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.repositories import get_player, _update_player_field
from game.equipment_service import (
    EQUIPMENT_CATALOG, SLOT_NAMES, SLOTS,
    get_equipped, get_equipment_inventory, equip_item, unequip_item,
    buy_equipment, repair_boots, render_equipment_panel,
)

NPC_NAME = "🧰 Брум"
NPC_GREETING = "«Лучшая экипировка в Сереброграде — и точка. Что тебя интересует?»"

SLOT_ICONS = {
    "belt":  "🪢",
    "boots": "👞",
    "hat":   "🎩",
    "suit":  "🥻",
}
SLOT_DESCRIPTIONS = {
    "belt":  "Ремень — хранит кристаллы. Больше слотов = больше монстров с собой.",
    "boots": "Сапоги — ускоряют переходы. Изнашиваются, требуют ремонта.",
    "hat":   "Шляпа — влияет на цены. Дешевле купить, дороже продать.",
    "suit":  "Комбез — ускоряет восстановление энергии.",
}


# ── Клавиатуры ────────────────────────────────────────────────────────────────

def shop_categories_kb() -> InlineKeyboardMarkup:
    """Главное меню магазина — выбор категории."""
    rows = []
    for slot in SLOTS:
        icon = SLOT_ICONS[slot]
        name = SLOT_NAMES[slot]
        rows.append([InlineKeyboardButton(
            text=f"{icon} {name}",
            callback_data=f"equip:cat:{slot}"
        )])
    rows.append([InlineKeyboardButton(text="🎒 Моя экипировка", callback_data="equip:myequip")])
    rows.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="equip:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def slot_items_kb(slot: str, uid: int) -> InlineKeyboardMarkup:
    """Список товаров в категории."""
    equipped = get_equipped(uid)
    currently = equipped.get(slot)
    rows = []
    for slug, item in EQUIPMENT_CATALOG.items():
        if item["slot"] != slot:
            continue
        is_equipped = currently and currently.get("slug") == slug
        mark = "✅ " if is_equipped else ""
        rows.append([InlineKeyboardButton(
            text=f"{mark}{item['name']} — {item['price']}з",
            callback_data=f"equip:item:{slug}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ К категориям", callback_data="equip:shop")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def item_detail_kb(slug: str, uid: int, gold: int) -> InlineKeyboardMarkup:
    """Карточка предмета — купить / назад."""
    item = EQUIPMENT_CATALOG[slug]
    slot = item["slot"]
    # Проверяем есть ли уже в инвентаре
    inv = get_equipment_inventory(uid)
    owned = any(i["slug"] == slug for i in inv)
    equipped = get_equipped(uid)
    is_equipped = equipped.get(slot, {}) and equipped[slot].get("slug") == slug if equipped.get(slot) else False

    rows = []
    if is_equipped:
        rows.append([InlineKeyboardButton(
            text="✅ Надет — Снять",
            callback_data=f"equip:unequip:{slot}"
        )])
    elif owned:
        rows.append([InlineKeyboardButton(
            text="📦 Надеть из инвентаря",
            callback_data=f"equip:wear:{slug}"
        )])
    else:
        can_buy = gold >= item["price"]
        buy_label = f"🛒 Купить за {item['price']}з" if can_buy else f"❌ Нужно {item['price']}з (не хватает {item['price']-gold}з)"
        rows.append([InlineKeyboardButton(
            text=buy_label,
            callback_data=f"equip:buy:{slug}" if can_buy else "equip:noop"
        )])
    rows.append([InlineKeyboardButton(
        text=f"⬅️ Назад к {SLOT_NAMES[slot]}",
        callback_data=f"equip:cat:{slot}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_equipment_inline(uid: int) -> InlineKeyboardMarkup:
    """Надетая экипировка — снять/починить."""
    equipped = get_equipped(uid)
    inv = get_equipment_inventory(uid)
    rows = []
    for slot in SLOTS:
        item = equipped.get(slot)
        if item:
            rows.append([InlineKeyboardButton(
                text=f"❌ Снять {item['name']}",
                callback_data=f"equip:unequip:{slot}"
            )])
            if slot == "boots":
                max_d = EQUIPMENT_CATALOG.get(item.get("slug",""), {}).get("durability", 100)
                if item.get("durability", 100) < max_d:
                    rows.append([InlineKeyboardButton(
                        text="🔧 Починить сапоги",
                        callback_data="equip:repair"
                    )])
    if inv:
        rows.append([InlineKeyboardButton(
            text=f"📦 Инвентарь ({len(inv)} пред.)",
            callback_data="equip:inventory"
        )])
    rows.append([InlineKeyboardButton(text="🛒 В магазин", callback_data="equip:shop")])
    rows.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="equip:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def inventory_equip_inline(items: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        dur = item.get("durability", 100)
        max_d = EQUIPMENT_CATALOG.get(item.get("slug",""), {}).get("durability", 100)
        dur_str = f" ({dur}/{max_d})" if item["slot"] == "boots" else ""
        rows.append([InlineKeyboardButton(
            text=f"👆 {item['name']}{dur_str}",
            callback_data=f"equip:wear:{item['slug']}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="equip:myequip")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Тексты ────────────────────────────────────────────────────────────────────

def _shop_welcome_text() -> str:
    return (
        f"{NPC_NAME}\n"
        f"{NPC_GREETING}\n\n"
        f"Выбери категорию товара:"
    )


def _slot_list_text(slot: str) -> str:
    icon = SLOT_ICONS[slot]
    name = SLOT_NAMES[slot]
    desc = SLOT_DESCRIPTIONS[slot]
    items = [(s, i) for s, i in EQUIPMENT_CATALOG.items() if i["slot"] == slot]
    lines = [
        f"{icon} {name}",
        f"{desc}\n",
        f"Доступные варианты:",
    ]
    for slug, item in items:
        lines.append(f"• {item['name']} — {item['price']}з")
    return "\n".join(lines)


def _item_detail_text(slug: str) -> str:
    item = EQUIPMENT_CATALOG[slug]
    slot = item["slot"]
    icon = SLOT_ICONS[slot]
    lines = [
        f"{icon} {item['name']}",
        f"{'─'*25}",
        f"📋 {item.get('desc', '')}",
        f"💰 Цена: {item['price']}з",
    ]
    if slot == "boots":
        max_d = item.get("durability", 100)
        repair = item.get("repair", 30)
        lines.append(f"🔧 Прочность: {max_d} | Ремонт: {repair}з")
    if slot == "belt":
        lines.append(f"💎 Слотов кристаллов: {item.get('crystal_slots', 0)}")
    if slot == "hat":
        buy_d = int(item.get("buy_discount", 0) * 100)
        sell_b = int(item.get("sell_bonus", 0) * 100)
        lines.append(f"🛒 Покупка: -{buy_d}% | Продажа: +{sell_b}%")
    if slot == "suit":
        regen = int(item.get("energy_regen", 0) * 100)
        lines.append(f"⚡ Регенерация энергии: +{regen}%")
    return "\n".join(lines)


# ── Хендлеры ─────────────────────────────────────────────────────────────────

async def equipment_handler(message: Message):
    """Открывает магазин экипировки у Брума."""
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    from game.location_rules import is_city
    if not is_city(player.location_slug):
        await message.answer(
            "⚒ Мастерская Брума находится в Ремесленном квартале Сереброграда.\n"
            "Вернись в город, чтобы купить или улучшить снаряжение."
        )
        return
    await message.answer(_shop_welcome_text(), reply_markup=shop_categories_kb())


async def equipment_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    player = get_player(uid)
    if not player:
        await callback.answer("Сначала /start")
        return
    data = callback.data
    await callback.answer()

    # Главное меню магазина
    if data == "equip:shop":
        try:
            await callback.message.edit_text(
                _shop_welcome_text(), reply_markup=shop_categories_kb()
            )
        except Exception:
            await callback.message.answer(
                _shop_welcome_text(), reply_markup=shop_categories_kb()
            )

    # Категория
    elif data.startswith("equip:cat:"):
        slot = data.split(":")[-1]
        text = _slot_list_text(slot)
        try:
            await callback.message.edit_text(text, reply_markup=slot_items_kb(slot, uid))
        except Exception:
            await callback.message.answer(text, reply_markup=slot_items_kb(slot, uid))

    # Карточка предмета
    elif data.startswith("equip:item:"):
        slug = data.split(":", 2)[-1]
        text = _item_detail_text(slug)
        try:
            await callback.message.edit_text(
                text, reply_markup=item_detail_kb(slug, uid, player.gold)
            )
        except Exception:
            await callback.message.answer(
                text, reply_markup=item_detail_kb(slug, uid, player.gold)
            )

    # Покупка
    elif data.startswith("equip:buy:"):
        slug = data.split(":", 2)[-1]
        ok, msg, new_gold = buy_equipment(uid, slug, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
            item = EQUIPMENT_CATALOG.get(slug, {})
            slot = item.get("slot","belt")
            # Авто-надеваем если слот свободен
            equipped = get_equipped(uid)
            if not equipped.get(slot):
                equip_item(uid, slug)
                msg = f"✅ Куплено и надето: {item.get('name','')}"
            else:
                msg = f"✅ Куплено: {item.get('name','')} — в инвентаре"
        await callback.answer(msg, show_alert=True)
        if ok:
            text = _item_detail_text(slug)
            try:
                await callback.message.edit_text(
                    text, reply_markup=item_detail_kb(slug, uid, new_gold)
                )
            except Exception:
                pass

    # Моя экипировка
    elif data == "equip:myequip":
        panel = render_equipment_panel(uid)
        try:
            await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))
        except Exception:
            await callback.message.answer(panel, reply_markup=my_equipment_inline(uid))

    # Снять
    elif data.startswith("equip:unequip:"):
        slot = data.split(":", 2)[-1]
        ok, msg = unequip_item(uid, slot)
        await callback.answer(msg, show_alert=True)
        if ok:
            panel = render_equipment_panel(uid)
            try:
                await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))
            except Exception:
                pass

    # Надеть из инвентаря
    elif data == "equip:inventory":
        inv = get_equipment_inventory(uid)
        if not inv:
            await callback.answer("Инвентарь экипировки пуст.", show_alert=True)
            return
        try:
            await callback.message.edit_text(
                "📦 Инвентарь\nВыбери предмет для надевания:",
                reply_markup=inventory_equip_inline(inv)
            )
        except Exception:
            pass

    elif data.startswith("equip:wear:"):
        slug = data.split(":", 2)[-1]
        ok, msg = equip_item(uid, slug)
        await callback.answer(msg, show_alert=True)
        if ok:
            panel = render_equipment_panel(uid)
            try:
                await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))
            except Exception:
                pass

    # Починить сапоги
    elif data == "equip:repair":
        ok, msg, new_gold = repair_boots(uid, player.gold)
        if ok:
            _update_player_field(uid, gold=new_gold)
        await callback.answer(msg, show_alert=True)
        if ok:
            panel = render_equipment_panel(uid)
            try:
                await callback.message.edit_text(panel, reply_markup=my_equipment_inline(uid))
            except Exception:
                pass

    elif data in ("equip:noop",):
        pass

    elif data == "equip:close":
        try:
            await callback.message.delete()
        except Exception:
            pass
