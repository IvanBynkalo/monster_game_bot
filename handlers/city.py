from pathlib import Path

from aiogram.types import (
    Message,
    FSInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.repositories import (
    add_player_experience,
    add_player_gold,
    get_player,
    get_resources,
    update_player_location,
    update_player_district,
    get_active_city_orders,
    count_active_city_orders,
    has_active_city_order,
    add_city_order,
    set_ui_screen,
    get_city_resource_market,
)

# Опциональные функции. Если в проекте они уже есть — механики включатся.
# Если каких-то нет, файл всё равно соберётся, а интерфейс останется рабочим.
try:
    from database.repositories import get_inventory, spend_item
except ImportError:
    def get_inventory(_telegram_id: int):
        return {}

    def spend_item(_telegram_id: int, _item_slug: str, _amount: int) -> bool:
        return False

try:
    from database.repositories import get_player_monsters, remove_player_monster
except ImportError:
    def get_player_monsters(_telegram_id: int):
        return []

    def remove_player_monster(_telegram_id: int, _monster_id: int) -> bool:
        return False

from game.city_service import render_city_menu, render_guild_text, GUILD_QUESTS
from game.craft_service import render_craft_text
from game.item_service import ITEMS
from game.location_rules import is_city
from game.market_service import BAG_OFFERS, get_resource_label
from game.shop_service import MONSTER_SHOP_OFFERS

from keyboards.board_menu import board_menu
from keyboards.city_menu import city_menu, district_actions_menu
from keyboards.main_menu import main_menu
from keyboards.shop_menu import bag_shop_menu, monster_shop_menu, sell_menu
from keyboards.craft_menu import craft_menu

# Используем существующие shop-handler'ы как backend,
# но в inline-режиме скрываем reply keyboard.
from handlers.shop import (
    buy_bag_handler,
    buy_monster_handler,
    sell_resource_item_handler,
)

try:
    from handlers.shop import buy_resource_item_handler
except ImportError:
    buy_resource_item_handler = None


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "city"

CITY_ORDER_LIMIT = 2

CITY_BOARD_ORDER_DEFS = {
    "herbalist_order": {
        "title": "Заказ травника",
        "goal_text": "Продай 3 🌿 Лесная трава Борту в лавку ресурсов.",
        "reward_gold": 35,
        "reward_exp": 12,
    },
    "ore_order": {
        "title": "Нужна руда для печей",
        "goal_text": "Продай 2 🔥 Угольный камень Борту в лавку ресурсов.",
        "reward_gold": 40,
        "reward_exp": 14,
    },
}

# Какие товары Мирна готова выкупать
MIRNA_BUY_PRICES = {
    "small_potion": 6,
    "big_potion": 11,
    "energy_capsule": 9,
    "basic_trap": 7,
    "poison_trap": 12,
    "spark_tonic": 14,
    "field_elixir": 16,
    "crystal_focus": 20,
    "swamp_antidote": 16,
}

RARITY_SELL_BASE = {
    "common": 20,
    "rare": 45,
    "epic": 90,
    "legendary": 180,
    "mythic": 320,
}


def _reward_text(player_id: int, quests: list[dict]) -> str:
    parts = []
    for quest in quests:
        add_player_gold(player_id, quest["reward_gold"])
        add_player_experience(player_id, quest["reward_exp"])
        parts.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )
    return "\n\n".join(parts)


async def _answer_with_city_image(message: Message, image_name: str, text: str, reply_markup):
    image_path = ASSETS_DIR / image_name
    if image_path.exists():
        await message.answer_photo(
            photo=FSInputFile(str(image_path)),
            caption=text,
            reply_markup=reply_markup,
        )
    else:
        await message.answer(text, reply_markup=reply_markup)


class InlineProxyMessage:
    """
    Проксируем callback в message-like объект, чтобы использовать существующие handlers.shop,
    но не менять нижнюю клавиатуру Telegram.
    """

    def __init__(self, callback: CallbackQuery, text: str):
        self._callback = callback
        self.text = text
        self.from_user = callback.from_user

    async def answer(self, text: str, reply_markup=None, **kwargs):
        # reply_markup специально игнорируем, чтобы не прыгало нижнее меню
        return await self._callback.message.answer(text, **kwargs)

    async def answer_photo(self, photo, caption=None, reply_markup=None, **kwargs):
        return await self._callback.message.answer_photo(photo=photo, caption=caption, **kwargs)


async def _run_existing_handler(callback: CallbackQuery, handler, text: str):
    proxy = InlineProxyMessage(callback, text)
    await handler(proxy)


# =========================================================
# INLINE UI: МИРНА / ВАРГ / БОРТ
# =========================================================

def mirna_main_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить у Мирны", callback_data="marketnpc:mirna_buy_menu")],
            [InlineKeyboardButton(text="💰 Продать товары Мирне", callback_data="marketnpc:mirna_sell_menu")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="marketnpc:close")],
        ]
    )


def mirna_buy_inline() -> InlineKeyboardMarkup:
    rows = []
    for slug, offer in BAG_OFFERS.items():
        title = f"🛒 {offer['name']} • {offer['price']}з"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"marketnpc:mirna_buy:{slug}")])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Мирне", callback_data="marketnpc:mirna_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mirna_sell_inline(player_id: int) -> InlineKeyboardMarkup:
    inventory = get_inventory(player_id)
    rows = []

    for slug, price in MIRNA_BUY_PRICES.items():
        qty = inventory.get(slug, 0)
        if qty <= 0:
            continue

        item = ITEMS.get(slug)
        if not item:
            continue

        rows.append([
            InlineKeyboardButton(
                text=f"💰 {item['emoji']} {item['name']} • {price}з • x{qty}",
                callback_data=f"marketnpc:mirna_sell:{slug}",
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Мирне", callback_data="marketnpc:mirna_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def varg_main_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить у Варга", callback_data="marketnpc:varg_buy_menu")],
            [InlineKeyboardButton(text="💰 Продать Варгу монстра", callback_data="marketnpc:varg_sell_menu")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="marketnpc:close")],
        ]
    )


def varg_buy_inline() -> InlineKeyboardMarkup:
    rows = []
    for slug, offer in MONSTER_SHOP_OFFERS.items():
        price = offer.get("price", offer.get("base_price", 0))
        rows.append([
            InlineKeyboardButton(
                text=f"🛒 {offer['name']} • {price}з",
                callback_data=f"marketnpc:varg_buy:{slug}",
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Варгу", callback_data="marketnpc:varg_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _get_monster_sell_price(monster: dict) -> int:
    rarity = monster.get("rarity", "common")
    base = RARITY_SELL_BASE.get(rarity, 20)
    level = int(monster.get("level", 1))
    attack = int(monster.get("attack", 1))
    max_hp = int(monster.get("max_hp", monster.get("hp", 1)))
    return max(10, base + level * 8 + attack * 2 + max_hp // 3)


def varg_sell_inline(player_id: int) -> InlineKeyboardMarkup:
    monsters = get_player_monsters(player_id)
    rows = []

    for monster in monsters:
        if monster.get("is_active"):
            continue

        price = _get_monster_sell_price(monster)
        rows.append([
            InlineKeyboardButton(
                text=f"💰 {monster['name']} • {price}з",
                callback_data=f"marketnpc:varg_sell:{monster['id']}",
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Варгу", callback_data="marketnpc:varg_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bort_main_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить у Борта", callback_data="marketnpc:bort_buy_menu")],
            [InlineKeyboardButton(text="💰 Продать ресурсы Борту", callback_data="marketnpc:bort_sell_menu")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="marketnpc:close")],
        ]
    )


def bort_buy_inline(city_slug: str) -> InlineKeyboardMarkup:
    market = get_city_resource_market(city_slug)
    rows = []

    for slug, entry in market.items():
        stock = int(entry.get("stock", 0))
        sell_price = int(entry.get("sell_price", 0))
        if stock <= 0 or sell_price <= 0:
            continue

        label = get_resource_label(slug)
        rows.append([
            InlineKeyboardButton(
                text=f"🛒 {label} • {sell_price}з",
                callback_data=f"marketnpc:bort_buy:{slug}",
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Борту", callback_data="marketnpc:bort_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bort_sell_inline(player_id: int, city_slug: str) -> InlineKeyboardMarkup:
    resources = get_resources(player_id)
    market = get_city_resource_market(city_slug)
    rows = []

    for slug, qty in resources.items():
        if qty <= 0:
            continue

        entry = market.get(slug, {})
        buy_price = int(entry.get("buy_price", 0))
        if buy_price <= 0:
            continue

        label = get_resource_label(slug)
        rows.append([
            InlineKeyboardButton(
                text=f"💰 {label} • {buy_price}з • x{qty}",
                callback_data=f"marketnpc:bort_sell:{slug}",
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Борту", callback_data="marketnpc:bort_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# =========================================================
# РЕНДЕРЫ ТЕКСТА
# =========================================================

def render_mirna_text(player_id: int) -> str:
    player = get_player(player_id)
    gold = getattr(player, "gold", 0) if player else 0

    lines = [
        "🧵 Мирна — портная лавка",
        "",
        f"💰 Твоё золото: {gold}",
        "",
        "Мирна шьёт полезные вещи для путешественников.",
        "Сейчас у неё в продаже в первую очередь сумки, а дальше здесь появятся одежда, плащи и прочие швейные товары.",
        "",
        "Текущий ассортимент:",
    ]

    if not BAG_OFFERS:
        lines.append("• Товары пока не настроены.")
    else:
        for offer in BAG_OFFERS.values():
            lines.append(
                f"• {offer['name']} — {offer['price']} золота "
                f"(вместимость: {offer['capacity']})"
            )

    lines.append("")
    lines.append("Мирна также может выкупить у тебя некоторые походные товары.")
    return "\n".join(lines)


def render_mirna_buy_text(player_id: int) -> str:
    player = get_player(player_id)
    gold = getattr(player, "gold", 0) if player else 0

    lines = [
        "🛒 Мирна — покупка",
        "",
        f"💰 Твоё золото: {gold}",
        "",
        "Выбери сумку:",
    ]

    for offer in BAG_OFFERS.values():
        lines.append(
            f"• {offer['name']} — {offer['price']} золота "
            f"(вместимость: {offer['capacity']})"
        )

    return "\n".join(lines)


def render_mirna_sell_text(player_id: int) -> str:
    inventory = get_inventory(player_id)

    lines = [
        "💰 Мирна — выкуп товаров",
        "",
        "Мирна принимает полезные походные товары.",
        "",
        "Доступно для продажи:",
    ]

    shown = False
    for slug, price in MIRNA_BUY_PRICES.items():
        qty = inventory.get(slug, 0)
        if qty <= 0:
            continue

        item = ITEMS.get(slug)
        if not item:
            continue

        shown = True
        lines.append(f"• {item['emoji']} {item['name']} — {price} золота • у тебя x{qty}")

    if not shown:
        lines.append("У тебя нет подходящих товаров для продажи Мирне.")

    return "\n".join(lines)


def render_varg_text(player_id: int) -> str:
    player = get_player(player_id)
    gold = getattr(player, "gold", 0) if player else 0

    lines = [
        "🐲 Варг — лавка монстров",
        "",
        f"💰 Твоё золото: {gold}",
        "",
        "Варг продаёт монстров и также выкупает подходящих существ у игрока.",
        "",
        "Сейчас в продаже:",
    ]

    if not MONSTER_SHOP_OFFERS:
        lines.append("• Монстры пока не настроены.")
    else:
        for offer in MONSTER_SHOP_OFFERS.values():
            price = offer.get("price", offer.get("base_price", 0))
            lines.append(f"• {offer['name']} — {price} золота")

    return "\n".join(lines)


def render_varg_buy_text(player_id: int) -> str:
    player = get_player(player_id)
    gold = getattr(player, "gold", 0) if player else 0

    lines = [
        "🛒 Варг — покупка монстров",
        "",
        f"💰 Твоё золото: {gold}",
        "",
        "Выбери монстра:",
    ]

    for offer in MONSTER_SHOP_OFFERS.values():
        price = offer.get("price", offer.get("base_price", 0))
        lines.append(f"• {offer['name']} — {price} золота")

    return "\n".join(lines)


def render_varg_sell_text(player_id: int) -> str:
    monsters = get_player_monsters(player_id)
    lines = [
        "💰 Варг — выкуп монстров",
        "",
        "Варг покупает только неактивных монстров.",
        "",
        "Доступно для продажи:",
    ]

    shown = False
    for monster in monsters:
        if monster.get("is_active"):
            continue

        shown = True
        price = _get_monster_sell_price(monster)
        lines.append(
            f"• {monster['name']} — {price} золота "
            f"(редкость: {monster.get('rarity', 'common')}, ур. {monster.get('level', 1)})"
        )

    if not shown:
        lines.append("У тебя нет неактивных монстров для продажи Варгу.")

    return "\n".join(lines)


def render_bort_text(city_slug: str, player_id: int) -> str:
    player = get_player(player_id)
    gold = getattr(player, "gold", 0) if player else 0
    market = get_city_resource_market(city_slug)

    lines = [
        "📦 Борт — лавка ресурсов",
        "",
        f"💰 Твоё золото: {gold}",
        "",
        "Борт покупает и продаёт ресурсы города.",
        "",
        "Текущий рынок:",
    ]

    if not market:
        lines.append("• Рынок пока не настроен.")
    else:
        for slug, entry in market.items():
            label = get_resource_label(slug)
            buy_price = int(entry.get("buy_price", 0))
            sell_price = int(entry.get("sell_price", 0))
            stock = int(entry.get("stock", 0))
            lines.append(
                f"• {label} — покупает по {buy_price}з, продаёт по {sell_price}з, запас: {stock}"
            )

    return "\n".join(lines)


def render_bort_buy_text(city_slug: str, player_id: int) -> str:
    player = get_player(player_id)
    gold = getattr(player, "gold", 0) if player else 0
    market = get_city_resource_market(city_slug)

    lines = [
        "🛒 Борт — покупка ресурсов",
        "",
        f"💰 Твоё золото: {gold}",
        "",
        "Выбери ресурс:",
    ]

    shown = False
    for slug, entry in market.items():
        stock = int(entry.get("stock", 0))
        sell_price = int(entry.get("sell_price", 0))
        if stock <= 0 or sell_price <= 0:
            continue

        shown = True
        lines.append(f"• {get_resource_label(slug)} — {sell_price} золота")

    if not shown:
        lines.append("Сейчас у Борта нечего купить.")

    return "\n".join(lines)


def render_bort_sell_text(city_slug: str, player_id: int) -> str:
    resources = get_resources(player_id)
    market = get_city_resource_market(city_slug)

    lines = [
        "💰 Борт — выкуп ресурсов",
        "",
        "Борт принимает городские ресурсы.",
        "",
        "Доступно для продажи:",
    ]

    shown = False
    for slug, qty in resources.items():
        if qty <= 0:
            continue

        entry = market.get(slug, {})
        buy_price = int(entry.get("buy_price", 0))
        if buy_price <= 0:
            continue

        shown = True
        lines.append(f"• {get_resource_label(slug)} — {buy_price} золота • у тебя x{qty}")

    if not shown:
        lines.append("У тебя нет подходящих ресурсов для продажи Борту.")

    return "\n".join(lines)


# =========================================================
# ГОРОД / ДОСКА / ГИЛЬДИИ
# =========================================================

async def city_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not is_city(player.location_slug):
        await message.answer(
            "Ты сейчас не в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    set_ui_screen(message.from_user.id, "city")

    district_to_image = {
        "market_square": "city_square.png",
        "craft_quarter": "alchemy_lab.png",
        "guild_quarter": "guild_hall.png",
        "main_gate": "city_square.png",
    }

    await _answer_with_city_image(
        message,
        district_to_image.get(player.current_district_slug, "city_square.png"),
        render_city_menu(player),
        city_menu(player.current_district_slug),
    )


async def city_board_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Доска заказов доступна только в городе.")
        return

    active_orders = get_active_city_orders(message.from_user.id)

    text = (
        "📜 Доска заказов\n\n"
        "1) Заказ травника\n"
        "Продай 3 🌿 Лесная трава Борту в лавку ресурсов.\n"
        "Награда: 35 золота, 12 опыта\n\n"
        "2) Нужна руда для печей\n"
        "Продай 2 🔥 Угольный камень Борту в лавку ресурсов.\n"
        "Награда: 40 золота, 14 опыта\n\n"
        f"Активных заказов: {len(active_orders)}/{CITY_ORDER_LIMIT}"
    )

    set_ui_screen(message.from_user.id, "board")
    await _answer_with_city_image(
        message,
        "bag_market.png",
        text,
        board_menu(),
    )


async def take_herbalist_order_handler(message: Message):
    await _take_city_order(message, "herbalist_order")


async def take_ore_order_handler(message: Message):
    await _take_city_order(message, "ore_order")


async def _take_city_order(message: Message, order_slug: str):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Доска заказов доступна только в городе.")
        return

    order_def = CITY_BOARD_ORDER_DEFS[order_slug]

    if has_active_city_order(message.from_user.id, order_slug):
        await message.answer(
            f"⚠️ Этот заказ уже активен:\n\n"
            f"{order_def['title']}\n"
            f"Награда: {order_def['reward_gold']} золота, {order_def['reward_exp']} опыта",
            reply_markup=board_menu(),
        )
        return

    active_count = count_active_city_orders(message.from_user.id)
    if active_count >= CITY_ORDER_LIMIT:
        await message.answer(
            f"⚠️ У тебя уже максимум активных городских заказов: {CITY_ORDER_LIMIT}.\n\n"
            "Открой «📒 Мои заказы», чтобы посмотреть текущие.",
            reply_markup=board_menu(),
        )
        return

    add_city_order(
        telegram_id=message.from_user.id,
        order_slug=order_slug,
        title=order_def["title"],
        goal_text=order_def["goal_text"],
        reward_gold=order_def["reward_gold"],
        reward_exp=order_def["reward_exp"],
    )

    await message.answer(
        f"✅ Заказ взят: {order_def['title']}\n\n"
        f"Цель: {order_def['goal_text']}\n"
        f"Награда: {order_def['reward_gold']} золота, {order_def['reward_exp']} опыта",
        reply_markup=board_menu(),
    )


async def my_board_orders_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Просмотр заказов доступен только в городе.")
        return

    active_orders = get_active_city_orders(message.from_user.id)
    if not active_orders:
        await message.answer(
            "📒 У тебя нет активных городских заказов.\n\n"
            "Открой доску заказов и возьми один или два заказа.",
            reply_markup=board_menu(),
        )
        return

    parts = ["📒 Мои заказы\n"]
    for idx, order in enumerate(active_orders, start=1):
        parts.append(
            f"{idx}. {order['title']}\n"
            f"Цель: {order['goal_text']}\n"
            f"Награда: {order['reward_gold']} золота, {order['reward_exp']} опыта"
        )

    await message.answer("\n\n".join(parts), reply_markup=board_menu())


async def back_to_city_from_board_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    set_ui_screen(message.from_user.id, "city")
    await message.answer(
        "🏙 Возвращаемся в городское меню.",
        reply_markup=city_menu(player.current_district_slug),
    )


async def city_guilds_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Гильдии доступны только в городе.")
        return

    update_player_district(message.from_user.id, "guild_quarter")
    set_ui_screen(message.from_user.id, "district")

    text = (
        "🏛 Квартал гильдий\n\n"
        "Здесь собраны главные профессиональные союзы Сереброграда.\n"
        "Выбери гильдию, чтобы посмотреть поручения и специализацию."
    )

    await _answer_with_city_image(
        message,
        "guild_hall.png",
        text,
        district_actions_menu("guild_quarter"),
    )


async def guild_hunters_handler(message: Message):
    await _guild_handler(
        message,
        "🎯 Гильдия ловцов",
        "Здесь учат лучше чувствовать момент для поимки и преследования.",
        "hunter",
        "hunters_guild.png",
    )


async def guild_gatherers_handler(message: Message):
    await _guild_handler(
        message,
        "🌿 Гильдия собирателей",
        "Здесь учат находить полезные травы и безопасно ходить в экспедиции.",
        "gatherer",
        "guild_hall.png",
    )


async def guild_geologists_handler(message: Message):
    await _guild_handler(
        message,
        "⛏ Гильдия геологов",
        "Здесь обучают находить жилы, руду и редкие каменные ядра.",
        "geologist",
        "guild_hall.png",
    )


async def guild_alchemists_handler(message: Message):
    await _guild_handler(
        message,
        "⚗ Гильдия алхимиков",
        "Здесь раскрывают секреты настоев, эссенций и устойчивых смесей.",
        "alchemist",
        "guild_hall.png",
    )


async def _guild_handler(
    message: Message,
    title: str,
    description: str,
    profession: str,
    image_name: str,
):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Гильдии доступны только в городе.")
        return

    quests = [q for q in GUILD_QUESTS if q["profession"] == profession]
    set_ui_screen(message.from_user.id, "district")

    await _answer_with_city_image(
        message,
        image_name,
        render_guild_text(title, description, quests),
        district_actions_menu("guild_quarter"),
    )


async def city_guard_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Стража доступна только в городе.")
        return

    text = (
        "🛡 Городская стража\n\n"
        "Стражник напоминает: за воротами опасно.\n"
        "Подготовь сумку, купи расходники и выходи только через главные ворота."
    )

    set_ui_screen(message.from_user.id, "district")
    await _answer_with_city_image(
        message,
        "city_square.png",
        text,
        district_actions_menu("main_gate"),
    )


async def leave_city_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Ты и так не в городе.")
        return

    if player.current_district_slug != "main_gate":
        await message.answer(
            "Покинуть город можно только через 🚪 Главные ворота.",
            reply_markup=city_menu(player.current_district_slug),
        )
        return

    update_player_location(message.from_user.id, "dark_forest")
    set_ui_screen(message.from_user.id, "main")

    await message.answer(
        "🚶 Ты покидаешь Сереброград через главные ворота и выходишь в Тёмный лес.",
        reply_markup=main_menu("dark_forest", None),
    )


# =========================================================
# ТОРГОВЫЙ КВАРТАЛ
# =========================================================

async def city_market_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Торговый квартал доступен только в городе.")
        return

    update_player_district(message.from_user.id, "market_square")
    set_ui_screen(message.from_user.id, "district")

    text = (
        "🏬 Торговый квартал\n\n"
        "Ты входишь в торговый квартал.\n"
        "Здесь работают три торговца:\n"
        "• Мирна — портная лавка\n"
        "• Варг — лавка монстров\n"
        "• Борт — лавка ресурсов"
    )

    await _answer_with_city_image(
        message,
        "city_square.png",
        text,
        district_actions_menu("market_square"),
    )


async def city_bags_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Портная лавка доступна только в городе.")
        return

    set_ui_screen(message.from_user.id, "district")
    await _answer_with_city_image(
        message,
        "bag_market.png",
        render_mirna_text(message.from_user.id),
        mirna_main_inline(),
    )


async def city_monsters_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Лавка монстров доступна только в городе.")
        return

    set_ui_screen(message.from_user.id, "district")
    await _answer_with_city_image(
        message,
        "bag_market.png",
        render_varg_text(message.from_user.id),
        varg_main_inline(),
    )


async def city_buyer_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Лавка ресурсов доступна только в городе.")
        return

    set_ui_screen(message.from_user.id, "district")
    await message.answer(
        render_bort_text(player.location_slug, message.from_user.id),
        reply_markup=bort_main_inline(),
    )


async def city_alchemy_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "craft")

    await message.answer(
        render_craft_text(player, resources),
        reply_markup=craft_menu(player, resources),
    )


async def city_traps_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Мастер ловушек доступен только в городе.")
        return

    text = (
        "🪤 Мастер ловушек\n\n"
        "Он советует всегда держать в запасе хотя бы одну ловушку и приносить редкие материалы "
        "для будущих улучшений."
    )

    set_ui_screen(message.from_user.id, "district")
    await _answer_with_city_image(
        message,
        "trap_workshop.png",
        text,
        district_actions_menu("craft_quarter"),
    )


# =========================================================
# CALLBACK: ТОРГОВЦЫ КВАРТАЛА
# =========================================================

async def market_inline_callback(callback: CallbackQuery):
    player = get_player(callback.from_user.id)
    if not player:
        await callback.answer("Сначала напиши /start", show_alert=True)
        return

    data = callback.data or ""

    # ---------------- MIRNA ----------------

    if data == "marketnpc:mirna_buy_menu":
        await callback.message.edit_text(
            render_mirna_buy_text(callback.from_user.id),
            reply_markup=mirna_buy_inline(),
        )
        await callback.answer()
        return

    if data.startswith("marketnpc:mirna_buy:"):
        slug = data.split(":")[-1]
        offer = BAG_OFFERS.get(slug)
        if not offer:
            await callback.answer("Товар не найден.", show_alert=True)
            return

        buy_text = f"🛒 Купить сумку: {offer['name']} • {offer['price']}з"
        await callback.answer("Покупаю у Мирны...")
        await _run_existing_handler(callback, buy_bag_handler, buy_text)
        return

    if data == "marketnpc:mirna_sell_menu":
        await callback.message.edit_text(
            render_mirna_sell_text(callback.from_user.id),
            reply_markup=mirna_sell_inline(callback.from_user.id),
        )
        await callback.answer()
        return

    if data.startswith("marketnpc:mirna_sell:"):
        slug = data.split(":")[-1]

        if slug not in MIRNA_BUY_PRICES:
            await callback.answer("Неизвестный товар.", show_alert=True)
            return

        item = ITEMS.get(slug)
        if not item:
            await callback.answer("Товар не найден.", show_alert=True)
            return

        if not spend_item(callback.from_user.id, slug, 1):
            await callback.answer("У тебя нет этого товара.", show_alert=True)
            return

        gold = MIRNA_BUY_PRICES[slug]
        add_player_gold(callback.from_user.id, gold)

        await callback.answer(f"Продано: {item['name']} (+{gold} золота)")
        await callback.message.answer(
            f"✅ Мирна купила у тебя:\n"
            f"{item['emoji']} {item['name']}\n"
            f"Получено: {gold} золота\n"
            f"Теперь золота: {get_player(callback.from_user.id).gold}",
        )
        await callback.message.answer(
            render_mirna_sell_text(callback.from_user.id),
            reply_markup=mirna_sell_inline(callback.from_user.id),
        )
        return

    if data == "marketnpc:mirna_back":
        await callback.message.edit_text(
            render_mirna_text(callback.from_user.id),
            reply_markup=mirna_main_inline(),
        )
        await callback.answer()
        return

    # ---------------- VARG ----------------

    if data == "marketnpc:varg_buy_menu":
        await callback.message.edit_text(
            render_varg_buy_text(callback.from_user.id),
            reply_markup=varg_buy_inline(),
        )
        await callback.answer()
        return

    if data.startswith("marketnpc:varg_buy:"):
        slug = data.split(":")[-1]
        offer = MONSTER_SHOP_OFFERS.get(slug)
        if not offer:
            await callback.answer("Монстр не найден.", show_alert=True)
            return

        price = offer.get("price", offer.get("base_price", 0))
        buy_text = f"🛒 Купить монстра: {offer['name']} • {price}з"
        await callback.answer("Покупаю у Варга...")
        await _run_existing_handler(callback, buy_monster_handler, buy_text)
        return

    if data == "marketnpc:varg_sell_menu":
        await callback.message.edit_text(
            render_varg_sell_text(callback.from_user.id),
            reply_markup=varg_sell_inline(callback.from_user.id),
        )
        await callback.answer()
        return

    if data.startswith("marketnpc:varg_sell:"):
        try:
            monster_id = int(data.split(":")[-1])
        except ValueError:
            await callback.answer("Некорректный монстр.", show_alert=True)
            return

        monsters = get_player_monsters(callback.from_user.id)
        target = None
        for monster in monsters:
            if int(monster["id"]) == monster_id:
                target = monster
                break

        if not target:
            await callback.answer("Монстр не найден.", show_alert=True)
            return

        if target.get("is_active"):
            await callback.answer("Активного монстра продать нельзя.", show_alert=True)
            return

        if len(monsters) <= 1:
            await callback.answer("Нельзя продать последнего монстра.", show_alert=True)
            return

        if not remove_player_monster(callback.from_user.id, monster_id):
            await callback.answer(
                "Продажа монстра не сработала. Если у тебя в репозитории другая функция удаления, подстрою под неё.",
                show_alert=True,
            )
            return

        price = _get_monster_sell_price(target)
        add_player_gold(callback.from_user.id, price)

        await callback.answer(f"Продан монстр: {target['name']} (+{price} золота)")
        await callback.message.answer(
            f"✅ Варг купил у тебя монстра:\n"
            f"{target['name']}\n"
            f"Получено: {price} золота\n"
            f"Теперь золота: {get_player(callback.from_user.id).gold}",
        )
        await callback.message.answer(
            render_varg_sell_text(callback.from_user.id),
            reply_markup=varg_sell_inline(callback.from_user.id),
        )
        return

    if data == "marketnpc:varg_back":
        await callback.message.edit_text(
            render_varg_text(callback.from_user.id),
            reply_markup=varg_main_inline(),
        )
        await callback.answer()
        return

    # ---------------- BORT ----------------

    if data == "marketnpc:bort_buy_menu":
        await callback.message.edit_text(
            render_bort_buy_text(player.location_slug, callback.from_user.id),
            reply_markup=bort_buy_inline(player.location_slug),
        )
        await callback.answer()
        return

    if data.startswith("marketnpc:bort_buy:"):
        slug = data.split(":")[-1]
        market = get_city_resource_market(player.location_slug)
        entry = market.get(slug)
        if not entry:
            await callback.answer("Ресурс не найден.", show_alert=True)
            return

        if buy_resource_item_handler is None:
            await callback.answer(
                "В проекте не найден обработчик покупки ресурсов. UI готов, backend подключим следующим шагом.",
                show_alert=True,
            )
            return

        label = get_resource_label(slug)
        sell_price = int(entry.get("sell_price", 0))
        buy_text = f"🛒 Купить ресурс: {label} • {sell_price}з"
        await callback.answer("Покупаю у Борта...")
        await _run_existing_handler(callback, buy_resource_item_handler, buy_text)
        return

    if data == "marketnpc:bort_sell_menu":
        await callback.message.edit_text(
            render_bort_sell_text(player.location_slug, callback.from_user.id),
            reply_markup=bort_sell_inline(callback.from_user.id, player.location_slug),
        )
        await callback.answer()
        return

    if data.startswith("marketnpc:bort_sell:"):
        slug = data.split(":")[-1]
        market = get_city_resource_market(player.location_slug)
        entry = market.get(slug)
        if not entry:
            await callback.answer("Ресурс не найден.", show_alert=True)
            return

        label = get_resource_label(slug)
        buy_price = int(entry.get("buy_price", 0))
        sell_text = f"💰 Продать: {label} • {buy_price}з"
        await callback.answer("Продаю Борту...")
        await _run_existing_handler(callback, sell_resource_item_handler, sell_text)
        return

    if data == "marketnpc:bort_back":
        await callback.message.edit_text(
            render_bort_text(player.location_slug, callback.from_user.id),
            reply_markup=bort_main_inline(),
        )
        await callback.answer()
        return

    # ---------------- CLOSE ----------------

    if data == "marketnpc:close":
        await callback.message.edit_text("Выбери действие внизу клавиатуры квартала.")
        await callback.answer()
        return

    await callback.answer()
