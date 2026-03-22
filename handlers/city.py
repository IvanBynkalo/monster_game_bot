# ── Error tracking shim ─────────────────────────────
try:
    from game.error_tracker import log_logic_error as _log_logic, log_exception as _log_exc
except Exception:
    def _log_logic(*a, **k): pass
    def _log_exc(*a, **k): pass
# ────────────────────────────────────────────────────

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
    _update_player_field,
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
    get_city_resource_sell_price,
    get_city_resource_buy_price,
    sell_resource_to_city_market,
    buy_resource_from_city_market,
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

try:
    from database.repositories import spend_resource
except ImportError:
    def spend_resource(_telegram_id: int, _slug: str, _count: int) -> bool:
        return False

try:
    from database.repositories import complete_city_order
except ImportError:
    def complete_city_order(_order_id: int):
        return None

from game.city_service import render_city_menu, render_guild_text, GUILD_QUESTS
from game.guild_quests import (
    render_guild_panel, get_active_quests, get_available_quests,
    take_quest, claim_quest, progress_quest, WEEKLY_GUILD_QUESTS,
)
from game.craft_service import render_craft_text
from game.item_service import ITEMS
from game.location_rules import is_city
from game.trap_service import render_trap_shop, craft_trap_item, TRAP_RECIPES, CATEGORY_LABELS
from game.market_service import BAG_OFFERS, get_resource_label
from game.shop_service import MONSTER_SHOP_OFFERS

from keyboards.board_menu import board_menu
from keyboards.city_menu import city_menu, district_actions_menu
from keyboards.main_menu import main_menu
from keyboards.shop_menu import bag_shop_menu, monster_shop_menu, sell_menu
from keyboards.craft_menu import craft_menu

from handlers.shop import (
    buy_bag_handler,
    buy_monster_handler,
    sell_resource_item_handler,
)

try:
    from handlers.shop import buy_resource_item_handler
except ImportError:
    buy_resource_item_handler = None


# Images handled via utils.images — see utils/images.py

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

# Мирна выкупает походные товары
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

NPC_QUEST_DEFS = {
    "mirna_travel_set": {
        "npc": "mirna",
        "title": "Походный набор для каравана",
        "goal_text": "Принеси Мирне 2 🧪 Малое зелье и 1 ⚡ Капсула энергии.",
        "reward_gold": 35,
        "reward_exp": 18,
        "kind": "items",
        "requirements": {
            "small_potion": 2,
            "energy_capsule": 1,
        },
    },
    "varg_first_beast": {
        "npc": "varg",
        "title": "Первый зверь для перепродажи",
        "goal_text": "Отдай Варгу 1 неактивного монстра.",
        "reward_gold": 55,
        "reward_exp": 28,
        "kind": "monster",
        "requirements": {
            "count": 1,
        },
    },
    "bort_supply_batch": {
        "npc": "bort",
        "title": "Поставка для складов",
        "goal_text": "Принеси Борту 3 🌿 Лесная трава и 2 🔥 Угольный камень.",
        "reward_gold": 50,
        "reward_exp": 24,
        "kind": "resources",
        "requirements": {
            "forest_herb": 3,
            "ember_stone": 2,
        },
    },
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
    """Отправляет изображение города. image_name = ключ из CITY_IMAGES или имя файла."""
    from utils.images import send_city_image, CITY_DIR
    from aiogram.types import FSInputFile
    # Поддерживаем старый формат (filename.png) и новый (ключ из CITY_IMAGES)
    from utils.images import CITY_IMAGES
    # Если передан ключ контекста — используем маппинг
    context = image_name.replace(".png", "")
    mapped = CITY_IMAGES.get(context, image_name)
    image_path = CITY_DIR / mapped
    if image_path.exists():
        await message.answer_photo(
            photo=FSInputFile(str(image_path)),
            caption=text,
            reply_markup=reply_markup,
        )
    else:
        await message.answer(text, reply_markup=reply_markup)


class InlineProxyMessage:
    def __init__(self, callback: CallbackQuery, text: str):
        self._callback = callback
        self.text = text
        self.from_user = callback.from_user

    async def answer(self, text: str, reply_markup=None, **kwargs):
        return await self._callback.message.answer(text, **kwargs)

    async def answer_photo(self, photo, caption=None, reply_markup=None, **kwargs):
        return await self._callback.message.answer_photo(photo=photo, caption=caption, **kwargs)


async def _run_existing_handler(callback: CallbackQuery, handler, text: str):
    proxy = InlineProxyMessage(callback, text)
    await handler(proxy)


def _get_active_npc_order(player_id: int, npc_slug: str):
    active_orders = get_active_city_orders(player_id)
    quest_slugs = [slug for slug, data in NPC_QUEST_DEFS.items() if data["npc"] == npc_slug]
    for order in active_orders:
        if order["order_slug"] in quest_slugs:
            return order
    return None


def _npc_quest_ready(player_id: int, quest_slug: str) -> bool:
    quest = NPC_QUEST_DEFS[quest_slug]
    kind = quest["kind"]
    req = quest["requirements"]

    if kind == "items":
        inventory = get_inventory(player_id)
        return all(inventory.get(slug, 0) >= count for slug, count in req.items())

    if kind == "resources":
        resources = get_resources(player_id)
        return all(resources.get(slug, 0) >= count for slug, count in req.items())

    if kind == "monster":
        monsters = get_player_monsters(player_id)
        non_active = [m for m in monsters if not m.get("is_active")]
        return len(non_active) >= int(req.get("count", 1))

    return False


def _complete_npc_quest_requirements(player_id: int, quest_slug: str) -> bool:
    quest = NPC_QUEST_DEFS[quest_slug]
    kind = quest["kind"]
    req = quest["requirements"]

    if kind == "items":
        for slug, count in req.items():
            if not spend_item(player_id, slug, count):
                return False
        return True

    if kind == "resources":
        for slug, count in req.items():
            if not spend_resource(player_id, slug, count):
                return False
        return True

    if kind == "monster":
        monsters = get_player_monsters(player_id)
        target = None
        for monster in monsters:
            if not monster.get("is_active"):
                target = monster
                break

        if not target:
            return False

        if remove_player_monster(player_id, int(target["id"])):
            return True

        try:
            monsters.remove(target)
            return True
        except ValueError:
            return False

    return False


def _grant_npc_quest_rewards(player_id: int, quest_slug: str):
    quest = NPC_QUEST_DEFS[quest_slug]
    add_player_gold(player_id, quest["reward_gold"])
    add_player_experience(player_id, quest["reward_exp"])


def _npc_has_available_quest(player_id: int, npc_slug: str) -> bool:
    active = _get_active_npc_order(player_id, npc_slug)
    return active is None


def _npc_has_ready_quest(player_id: int, npc_slug: str) -> bool:
    active = _get_active_npc_order(player_id, npc_slug)
    if not active:
        return False
    return _npc_quest_ready(player_id, active["order_slug"])


# =========================================================
# INLINE UI: МИРНА / ВАРГ / БОРТ
# =========================================================

def mirna_main_inline(player_id: int) -> InlineKeyboardMarkup:
    quest_label = "📜 Квесты"
    if _npc_has_ready_quest(player_id, "mirna"):
        quest_label = "❗ Сдать квест"
    elif _npc_has_available_quest(player_id, "mirna"):
        quest_label = "📜 Взять квест"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить у Мирны", callback_data="marketnpc:mirna_buy_menu")],
            [InlineKeyboardButton(text="💰 Продать товары Мирне", callback_data="marketnpc:mirna_sell_menu")],
            [InlineKeyboardButton(text=quest_label, callback_data="marketnpc:mirna_quest_menu")],
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


def mirna_quest_inline(player_id: int) -> InlineKeyboardMarkup:
    active = _get_active_npc_order(player_id, "mirna")
    rows = []

    if not active:
        rows.append([InlineKeyboardButton(text="📌 Взять квест Мирны", callback_data="marketnpc:mirna_quest_take")])
    else:
        if _npc_quest_ready(player_id, active["order_slug"]):
            rows.append([InlineKeyboardButton(text="✅ Сдать квест Мирне", callback_data="marketnpc:mirna_quest_turnin")])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Мирне", callback_data="marketnpc:mirna_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def varg_main_inline(player_id: int) -> InlineKeyboardMarkup:
    quest_label = "📜 Квесты"
    if _npc_has_ready_quest(player_id, "varg"):
        quest_label = "❗ Сдать квест"
    elif _npc_has_available_quest(player_id, "varg"):
        quest_label = "📜 Взять квест"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить у Варга", callback_data="marketnpc:varg_buy_menu")],
            [InlineKeyboardButton(text="💰 Продать Варгу монстра", callback_data="marketnpc:varg_sell_menu")],
            [InlineKeyboardButton(text=quest_label, callback_data="marketnpc:varg_quest_menu")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="marketnpc:close")],
        ]
    )


def varg_buy_inline() -> InlineKeyboardMarkup:
    """Список монстров — нажать для просмотра деталей."""
    rows = []
    from game.shop_service import RARITY_LABELS, MOOD_LABELS, TYPE_LABELS
    for slug, offer in MONSTER_SHOP_OFFERS.items():
        price = offer.get("price", offer.get("base_price", 0))
        rarity = RARITY_LABELS.get(offer.get("rarity","common"), "")
        rows.append([InlineKeyboardButton(
            text=f"🐲 {offer['name']} | {rarity} | {price}з",
            callback_data=f"marketnpc:varg_detail:{slug}",
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к Варгу", callback_data="marketnpc:varg_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def varg_monster_detail_inline(slug: str) -> InlineKeyboardMarkup:
    """Детальная карточка монстра перед покупкой."""
    offer = MONSTER_SHOP_OFFERS.get(slug, {})
    price = offer.get("price", offer.get("base_price", 0))
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🛒 Купить за {price}з",
            callback_data=f"marketnpc:varg_buy:{slug}"
        )],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="marketnpc:varg_buy_menu")],
    ])


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


def varg_quest_inline(player_id: int) -> InlineKeyboardMarkup:
    active = _get_active_npc_order(player_id, "varg")
    rows = []

    if not active:
        rows.append([InlineKeyboardButton(text="📌 Взять квест Варга", callback_data="marketnpc:varg_quest_take")])
    else:
        if _npc_quest_ready(player_id, active["order_slug"]):
            rows.append([InlineKeyboardButton(text="✅ Сдать квест Варгу", callback_data="marketnpc:varg_quest_turnin")])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Варгу", callback_data="marketnpc:varg_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bort_main_inline(player_id: int) -> InlineKeyboardMarkup:
    quest_label = "📜 Квесты"
    if _npc_has_ready_quest(player_id, "bort"):
        quest_label = "❗ Сдать квест"
    elif _npc_has_available_quest(player_id, "bort"):
        quest_label = "📜 Взять квест"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить у Борта", callback_data="marketnpc:bort_buy_menu")],
            [InlineKeyboardButton(text="💰 Продать ресурсы Борту", callback_data="marketnpc:bort_sell_menu")],
            [InlineKeyboardButton(text=quest_label, callback_data="marketnpc:bort_quest_menu")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="marketnpc:close")],
        ]
    )


def bort_buy_inline(city_slug: str) -> InlineKeyboardMarkup:
    market = get_city_resource_market(city_slug)
    rows = []

    for slug in market:
        entry = market[slug]
        stock = int(float(entry.get("stock", 0)))
        if stock <= 0:
            continue
        price = get_city_resource_buy_price(city_slug, slug)
        label = get_resource_label(slug)
        rows.append([
            InlineKeyboardButton(
                text=f"🛒 {label} • 💰{price}з",
                callback_data=f"marketnpc:bort_buy:{slug}",
            )
        ])

    if not rows:
        rows.append([InlineKeyboardButton(text="Нет товаров", callback_data="marketnpc:bort_back")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к Борту", callback_data="marketnpc:bort_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bort_sell_inline(player_id: int, city_slug: str) -> InlineKeyboardMarkup:
    resources = get_resources(player_id)
    market = get_city_resource_market(city_slug)
    player = get_player(player_id)
    merchant_level = getattr(player, "merchant_level", 1) if player else 1
    rows = []

    for slug, qty in resources.items():
        if qty <= 0:
            continue
        if slug not in market:
            continue
        price = get_city_resource_sell_price(city_slug, slug, merchant_level=merchant_level)
        label = get_resource_label(slug)
        rows.append([
            InlineKeyboardButton(
                text=f"🪙 {label} • {price}з/шт • x{qty}",
                callback_data=f"marketnpc:bort_sell:{slug}",
            )
        ])

    if not rows:
        rows.append([InlineKeyboardButton(text="Нет ресурсов для продажи", callback_data="marketnpc:bort_back")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к Борту", callback_data="marketnpc:bort_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bort_quest_inline(player_id: int) -> InlineKeyboardMarkup:
    active = _get_active_npc_order(player_id, "bort")
    rows = []

    if not active:
        rows.append([InlineKeyboardButton(text="📌 Взять квест Борта", callback_data="marketnpc:bort_quest_take")])
    else:
        if _npc_quest_ready(player_id, active["order_slug"]):
            rows.append([InlineKeyboardButton(text="✅ Сдать квест Борту", callback_data="marketnpc:bort_quest_turnin")])

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


def render_mirna_quest_text(player_id: int) -> str:
    active = _get_active_npc_order(player_id, "mirna")
    quest = NPC_QUEST_DEFS["mirna_travel_set"]

    if not active:
        return (
            "📜 Квест Мирны\n\n"
            f"{quest['title']}\n"
            f"Цель: {quest['goal_text']}\n"
            f"Награда: {quest['reward_gold']} золота, {quest['reward_exp']} опыта"
        )

    ready = _npc_quest_ready(player_id, active["order_slug"])
    status = "✅ Всё готово к сдаче" if ready else "⌛ Материалы ещё не собраны"

    return (
        "📜 Активный квест Мирны\n\n"
        f"{active['title']}\n"
        f"Цель: {active['goal_text']}\n"
        f"Награда: {active['reward_gold']} золота, {active['reward_exp']} опыта\n\n"
        f"Статус: {status}"
    )


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


def render_varg_quest_text(player_id: int) -> str:
    active = _get_active_npc_order(player_id, "varg")
    quest = NPC_QUEST_DEFS["varg_first_beast"]

    if not active:
        return (
            "📜 Квест Варга\n\n"
            f"{quest['title']}\n"
            f"Цель: {quest['goal_text']}\n"
            f"Награда: {quest['reward_gold']} золота, {quest['reward_exp']} опыта"
        )

    ready = _npc_quest_ready(player_id, active["order_slug"])
    status = "✅ Всё готово к сдаче" if ready else "⌛ Подходящий монстр ещё не найден"

    return (
        "📜 Активный квест Варга\n\n"
        f"{active['title']}\n"
        f"Цель: {active['goal_text']}\n"
        f"Награда: {active['reward_gold']} золота, {active['reward_exp']} опыта\n\n"
        f"Статус: {status}"
    )


def render_bort_text(city_slug: str, player_id: int) -> str:
    player = get_player(player_id)
    gold = getattr(player, "gold", 0) if player else 0
    merchant_level = getattr(player, "merchant_level", 1) if player else 1
    market = get_city_resource_market(city_slug)

    lines = [
        "📦 Борт — лавка ресурсов",
        "",
        f"💰 Твоё золото: {gold} золота",
        "",
        "Борт покупает и продаёт ресурсы города.",
        "",
        "Текущий рынок:",
    ]

    if not market:
        lines.append("• Рынок пока не настроен.")
    else:
        for slug in market:
            label = get_resource_label(slug)
            entry = market[slug]
            stock = int(float(entry.get("stock", 0)))
            sell_p = get_city_resource_sell_price(city_slug, slug, merchant_level=merchant_level)
            buy_p  = get_city_resource_buy_price(city_slug, slug)
            lines.append(
                f"• {label}\n  🪙 Продашь: {sell_p}з | 🛒 Купишь: {buy_p}з | 📦 Запас: {stock}"
            )

    return "\n".join(lines)


def render_bort_buy_text(city_slug: str, player_id: int) -> str:
    player = get_player(player_id)
    gold = getattr(player, "gold", 0) if player else 0
    market = get_city_resource_market(city_slug)

    lines = [
        "🛒 Борт — покупка ресурсов",
        "",
        f"💰 Твоё золото: {gold} золота",
        "",
        "Нажми на ресурс чтобы купить 1 единицу:",
    ]

    shown = False
    for slug in market:
        entry = market[slug]
        stock = int(float(entry.get("stock", 0)))
        if stock <= 0:
            continue
        price = get_city_resource_buy_price(city_slug, slug)
        shown = True
        lines.append(f"• {get_resource_label(slug)} — 🛒 {price} золота (запас: {stock})")

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
        if slug not in market:
            continue
        buy_price = get_city_resource_sell_price(city_slug, slug, merchant_level=getattr(get_player(player_id), "merchant_level", 1))
        if buy_price <= 0:
            continue
        shown = True
        lines.append(f"• {get_resource_label(slug)} — {buy_price} золота • у тебя x{qty}")

    if not shown:
        lines.append("У тебя нет подходящих ресурсов для продажи Борту.")

    return "\n".join(lines)


def render_bort_quest_text(player_id: int) -> str:
    active = _get_active_npc_order(player_id, "bort")
    quest = NPC_QUEST_DEFS["bort_supply_batch"]

    if not active:
        return (
            "📜 Квест Борта\n\n"
            f"{quest['title']}\n"
            f"Цель: {quest['goal_text']}\n"
            f"Награда: {quest['reward_gold']} золота, {quest['reward_exp']} опыта"
        )

    ready = _npc_quest_ready(player_id, active["order_slug"])
    status = "✅ Всё готово к сдаче" if ready else "⌛ Поставка ещё не собрана"

    return (
        "📜 Активный квест Борта\n\n"
        f"{active['title']}\n"
        f"Цель: {active['goal_text']}\n"
        f"Награда: {active['reward_gold']} золота, {active['reward_exp']} опыта\n\n"
        f"Статус: {status}"
    )


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
        district_actions_menu("guild_quarter", message.from_user.id),
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

    set_ui_screen(message.from_user.id, "district")
    uid = message.from_user.id

    text = render_guild_panel(uid, profession, title, description)

    # Inline кнопки: взять поручение / сдать выполненное
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from game.guild_quests import get_active_quests, get_available_quests, WEEKLY_GUILD_QUESTS
    rows = []

    # Кнопки "Взять" для доступных
    available = get_available_quests(uid, profession)
    for q in available:
        rows.append([InlineKeyboardButton(
            text=f"📌 Взять: {q['title']}",
            callback_data=f"guild:take:{profession}:{q['id']}"
        )])

    # Кнопки "Сдать" для выполненных
    active = get_active_quests(uid, profession)
    for q in active:
        if q.get("completed"):
            rows.append([InlineKeyboardButton(
                text=f"✅ Сдать: {q['title']}",
                callback_data=f"guild:claim:{profession}:{q['id']}"
            )])

    # Еженедельное
    weekly = WEEKLY_GUILD_QUESTS.get(profession, {})
    active_ids = {q["id"] for q in active}
    if weekly and weekly["id"] not in active_ids:
        rows.append([InlineKeyboardButton(
            text=f"🌟 Взять недельное: {weekly['title']}",
            callback_data=f"guild:take:{profession}:{weekly['id']}"
        )])

    kb = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

    await _answer_with_city_image(
        message,
        image_name,
        text,
        district_actions_menu("guild_quarter", message.from_user.id),
    )
    if kb:
        await message.answer("Действия:", reply_markup=kb)


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
        district_actions_menu("main_gate", message.from_user.id),
    )


async def leave_city_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Ты и так не в городе.")
        return

    # Выходим напрямую — без требования идти в главные ворота
    update_player_location(message.from_user.id, "dark_forest")
    update_player_district(message.from_user.id, "mushroom_path")
    set_ui_screen(message.from_user.id, "main")

    from game.map_service import render_location_card
    from game.dungeon_service import DUNGEONS
    from keyboards.location_menu import location_actions_inline

    loc_card = render_location_card("dark_forest")
    try:
        from game.grid_exploration_service import render_exploration_panel as _grid_panel
        _expl = _grid_panel(message.from_user.id, "dark_forest")
    except Exception:
        _expl = ""

    loc_text = "🚶 Ты покидаешь Сереброград и выходишь в Тёмный лес.\n\n" + loc_card
    if _expl:
        loc_text += "\n\n" + _expl

    try:
        from game.grid_exploration_service import is_dungeon_available
        has_dungeon = "dark_forest" in DUNGEONS and is_dungeon_available(message.from_user.id, "dark_forest")
    except Exception:
        has_dungeon = False

    from utils.images import send_location_image
    await send_location_image(message, "dark_forest", loc_text,
                               reply_markup=main_menu("dark_forest", "mushroom_path"))
    await message.answer(
        "Что делать:",
        reply_markup=location_actions_inline("dark_forest", has_dungeon=has_dungeon)
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
        district_actions_menu("market_square", message.from_user.id),
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
        mirna_main_inline(message.from_user.id),
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
        varg_main_inline(message.from_user.id),
    )


async def city_buyer_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Лавка ресурсов доступна только в городе.")
        return

    set_ui_screen(message.from_user.id, "district")
    await message.answer(
        render_bort_text(player.location_slug, message.from_user.id),
        reply_markup=bort_main_inline(message.from_user.id),
    )


async def city_craft_quarter_handler(message: Message):
    """Вход в Ремесленный квартал — показывает меню квартала."""
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Ремесленный квартал доступен только в городе.")
        return
    set_ui_screen(message.from_user.id, "district")
    update_player_district(message.from_user.id, "craft_quarter")
    text = (
        "⚒ Ремесленный квартал\n\n"
        "Улицы мастерских и алхимических лавок. "
        "Здесь можно сварить зелья, создать ловушки и улучшить снаряжение."
    )
    await _answer_with_city_image(
        message,
        "alchemy_lab.png",
        text,
        district_actions_menu("craft_quarter", message.from_user.id),
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

    resources = get_resources(message.from_user.id)
    text = render_trap_shop(player, resources)
    set_ui_screen(message.from_user.id, "traps")

    # Inline кнопки крафта по категориям
    hunter_level = getattr(player, "hunter_level", 1)
    rows = []
    for slug, recipe in TRAP_RECIPES.items():
        if recipe["hunter_level"] > hunter_level:
            continue
        has_mats = all(resources.get(r, 0) >= qty for r, qty in recipe["ingredients"].items())
        can_afford = player.gold >= recipe["gold_cost"]
        status = "✅" if (has_mats and can_afford) else "❌"
        rows.append([InlineKeyboardButton(
            text=f"{status} {recipe['name']} — {recipe['gold_cost']}з",
            callback_data=f"trap:craft:{slug}",
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="trap:back")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await _answer_with_city_image(message, "trap_workshop.png", text, district_actions_menu("craft_quarter", message.from_user.id))
    await message.answer("Выбери предмет для крафта:", reply_markup=kb)


# =========================================================
# CALLBACK: ТОРГОВЦЫ КВАРТАЛА
# =========================================================


async def trap_inline_callback(callback: CallbackQuery):
    """Обработчик inline-кнопок Мастера ловушек."""
    data = callback.data or ""
    uid  = callback.from_user.id

    if data == "trap:back":
        await callback.answer()
        await callback.message.delete()
        return

    if data.startswith("trap:craft:"):
        slug   = data.split(":", 2)[2]
        player = get_player(uid)
        if not player:
            await callback.answer("Сначала напиши /start", show_alert=True)
            return

        resources = get_resources(uid)
        result = craft_trap_item(player, resources, slug)

        if not result["ok"]:
            await callback.answer(result["msg"], show_alert=True)
            return

        # Списываем ресурсы и золото, выдаём предмет
        from database.repositories import spend_resource, add_item, improve_profession_from_action
        for res_slug, qty in result["ingredients"].items():
            spend_resource(uid, res_slug, qty)
        add_player_gold(uid, -result["gold_cost"])
        add_item(uid, result["item"], result["amount"])
        improve_profession_from_action(uid, "hunter")

        await callback.answer(f"✅ Создано: {result['msg']}", show_alert=False)

        # Обновляем кнопки
        player = get_player(uid)
        resources = get_resources(uid)
        hunter_level = getattr(player, "hunter_level", 1)
        rows = []
        for s, recipe in TRAP_RECIPES.items():
            if recipe["hunter_level"] > hunter_level:
                continue
            has_mats = all(resources.get(r, 0) >= qty for r, qty in recipe["ingredients"].items())
            can_afford = player.gold >= recipe["gold_cost"]
            status = "✅" if (has_mats and can_afford) else "❌"
            rows.append([InlineKeyboardButton(
                text=f"{status} {recipe['name']} — {recipe['gold_cost']}з",
                callback_data=f"trap:craft:{s}",
            )])
        rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="trap:back")])
        try:
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        except Exception:
            pass

        msg_text = f"🪤 {result['msg']}\n💰 Потрачено: {result['gold_cost']}з\n🎒 Получено: x{result['amount']}"
        await callback.message.answer(msg_text)

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

    if data == "marketnpc:mirna_quest_menu":
        await callback.message.edit_text(
            render_mirna_quest_text(callback.from_user.id),
            reply_markup=mirna_quest_inline(callback.from_user.id),
        )
        await callback.answer()
        return

    if data == "marketnpc:mirna_quest_take":
        quest_slug = "mirna_travel_set"
        quest = NPC_QUEST_DEFS[quest_slug]

        if _get_active_npc_order(callback.from_user.id, "mirna"):
            await callback.answer("У Мирны уже есть активный квест.", show_alert=True)
            return

        add_city_order(
            telegram_id=callback.from_user.id,
            order_slug=quest_slug,
            title=quest["title"],
            goal_text=quest["goal_text"],
            reward_gold=quest["reward_gold"],
            reward_exp=quest["reward_exp"],
        )

        await callback.message.edit_text(
            render_mirna_quest_text(callback.from_user.id),
            reply_markup=mirna_quest_inline(callback.from_user.id),
        )
        await callback.answer("Квест Мирны взят.")
        return

    if data == "marketnpc:mirna_quest_turnin":
        active = _get_active_npc_order(callback.from_user.id, "mirna")
        if not active:
            await callback.answer("Нет активного квеста.", show_alert=True)
            return

        if not _npc_quest_ready(callback.from_user.id, active["order_slug"]):
            await callback.answer("Для сдачи ещё не хватает предметов.", show_alert=True)
            return

        if not _complete_npc_quest_requirements(callback.from_user.id, active["order_slug"]):
            await callback.answer("Не удалось списать предметы.", show_alert=True)
            return

        complete_city_order(active["id"])
        _grant_npc_quest_rewards(callback.from_user.id, active["order_slug"])
        q = NPC_QUEST_DEFS[active["order_slug"]]

        await callback.message.answer(
            f"✅ Мирна приняла квест:\n"
            f"{q['title']}\n"
            f"Награда: +{q['reward_gold']} золота, +{q['reward_exp']} опыта"
        )
        await callback.message.answer(
            render_mirna_text(callback.from_user.id),
            reply_markup=mirna_main_inline(callback.from_user.id),
        )
        await callback.answer("Квест сдан.")
        return

    if data == "marketnpc:mirna_back":
        await callback.message.edit_text(
            render_mirna_text(callback.from_user.id),
            reply_markup=mirna_main_inline(callback.from_user.id),
        )
        await callback.answer()
        return

    # ---------------- VARG ----------------

    if data.startswith("marketnpc:varg_detail:"):
        # Показываем карточку монстра с кнопкой «Купить»
        slug = data.split(":")[-1]
        offer = MONSTER_SHOP_OFFERS.get(slug)
        if not offer:
            await callback.answer("Монстр не найден.", show_alert=True)
            return
        from game.shop_service import RARITY_LABELS, MOOD_LABELS
        price   = offer.get("price", offer.get("base_price", 0))
        rarity  = RARITY_LABELS.get(offer.get("rarity", "common"), offer.get("rarity", ""))
        mood    = MOOD_LABELS.get(offer.get("mood", ""), offer.get("mood", ""))
        player  = get_player(callback.from_user.id)
        gold    = getattr(player, "gold", 0) if player else 0
        detail_text = (
            f"🐲 {offer['name']}\n"
            f"Редкость: {rarity}\n"
            f"Характер: {mood}\n"
            f"HP: {offer.get('hp', '?')} | Атака: {offer.get('attack', '?')}\n\n"
            f"Цена: {price}з\n"
            f"Твоё золото: {gold}з"
        )
        await callback.message.edit_text(
            detail_text,
            reply_markup=varg_monster_detail_inline(slug),
        )
        await callback.answer()
        return

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

        player = get_player(callback.from_user.id)
        if not player:
            await callback.answer("Ошибка игрока.", show_alert=True)
            return

        price = offer.get("price", offer.get("base_price", 0))
        if player.gold < price:
            await callback.answer(
                f"Недостаточно золота! Нужно {price}з, у тебя {player.gold}з",
                show_alert=True
            )
            return

        # Покупаем напрямую
        from database.repositories import add_captured_monster
        _update_player_field(callback.from_user.id, gold=player.gold - price)
        new_monster = add_captured_monster(
            telegram_id=callback.from_user.id,
            name=offer["name"],
            rarity=offer.get("rarity", "common"),
            mood=offer.get("mood", "instinct"),
            hp=offer.get("hp", 10),
            attack=offer.get("attack", 3),
            source_type="shop",
        )
        # Автоматически размещаем в кристалл
        from game.crystal_service import (
            auto_store_new_monster, get_player_crystals,
            get_monsters_in_crystal, calculate_monster_volume
        )
        _placed_ok, _placed_msg = auto_store_new_monster(callback.from_user.id, new_monster["id"])

        if _placed_ok:
            crystals = get_player_crystals(callback.from_user.id)
            crystal_name = next(
                (c["name"] for c in crystals
                 if any(m["id"] == new_monster["id"]
                        for m in get_monsters_in_crystal(c["id"]))),
                "кристалл"
            )
            await callback.answer(f"✅ {offer['name']} → {crystal_name}", show_alert=True)
            await callback.message.answer(
                f"✅ Куплен: {offer['name']}\n"
                f"Редкость: {offer.get('rarity','common')}\n"
                f"💰 Потрачено: {price}з\n\n"
                f"💎 Помещён в: {crystal_name}"
            )
        else:
            # Нет места — показываем выбор кристалла
            from aiogram.types import InlineKeyboardMarkup as _IKM, InlineKeyboardButton as _IKB
            vol = calculate_monster_volume(new_monster)
            rows = []
            for c in get_player_crystals(callback.from_user.id):
                fv = c["max_volume"] - c["current_volume"]
                fs = c["max_monsters"] - c["current_monsters"]
                loc = c.get("location", "on_hand")
                if fv >= vol and fs > 0 and loc == "on_hand":
                    rows.append([_IKB(
                        text=f"💎 {c['name']} [{c['current_volume']}/{c['max_volume']}]",
                        callback_data=f"mon:set_crystal:{new_monster['id']}:{c['id']}"
                    )])
            if rows:
                await callback.answer(f"✅ {offer['name']} куплен! Выбери кристалл.", show_alert=True)
                await callback.message.answer(
                    f"✅ Куплен: {offer['name']} (-{price}з)\n"
                    f"💎 Выбери кристалл:",
                    reply_markup=_IKM(inline_keyboard=rows)
                )
            else:
                await callback.answer(
                    f"✅ Куплен {offer['name']}, но нет свободного кристалла!\n"
                    f"Нужно {vol} ед. объёма. Купи кристалл в Торговом квартале.",
                    show_alert=True
                )
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

        removed = remove_player_monster(callback.from_user.id, monster_id)
        if not removed:
            try:
                monsters.remove(target)
                removed = True
            except ValueError:
                removed = False

        if not removed:
            await callback.answer("Не удалось продать монстра.", show_alert=True)
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

    if data == "marketnpc:varg_quest_menu":
        await callback.message.edit_text(
            render_varg_quest_text(callback.from_user.id),
            reply_markup=varg_quest_inline(callback.from_user.id),
        )
        await callback.answer()
        return

    if data == "marketnpc:varg_quest_take":
        quest_slug = "varg_first_beast"
        quest = NPC_QUEST_DEFS[quest_slug]

        if _get_active_npc_order(callback.from_user.id, "varg"):
            await callback.answer("У Варга уже есть активный квест.", show_alert=True)
            return

        add_city_order(
            telegram_id=callback.from_user.id,
            order_slug=quest_slug,
            title=quest["title"],
            goal_text=quest["goal_text"],
            reward_gold=quest["reward_gold"],
            reward_exp=quest["reward_exp"],
        )

        await callback.message.edit_text(
            render_varg_quest_text(callback.from_user.id),
            reply_markup=varg_quest_inline(callback.from_user.id),
        )
        await callback.answer("Квест Варга взят.")
        return

    if data == "marketnpc:varg_quest_turnin":
        active = _get_active_npc_order(callback.from_user.id, "varg")
        if not active:
            await callback.answer("Нет активного квеста.", show_alert=True)
            return

        if not _npc_quest_ready(callback.from_user.id, active["order_slug"]):
            await callback.answer("Подходящего монстра пока нет.", show_alert=True)
            return

        if not _complete_npc_quest_requirements(callback.from_user.id, active["order_slug"]):
            await callback.answer("Не удалось передать монстра.", show_alert=True)
            return

        complete_city_order(active["id"])
        _grant_npc_quest_rewards(callback.from_user.id, active["order_slug"])
        q = NPC_QUEST_DEFS[active["order_slug"]]

        await callback.message.answer(
            f"✅ Варг принял квест:\n"
            f"{q['title']}\n"
            f"Награда: +{q['reward_gold']} золота, +{q['reward_exp']} опыта"
        )
        await callback.message.answer(
            render_varg_text(callback.from_user.id),
            reply_markup=varg_main_inline(callback.from_user.id),
        )
        await callback.answer("Квест сдан.")
        return

    if data == "marketnpc:varg_back":
        await callback.message.edit_text(
            render_varg_text(callback.from_user.id),
            reply_markup=varg_main_inline(callback.from_user.id),
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
        # Обновляем inline-меню Борта после продажи
        try:
            await callback.message.answer(
                render_bort_sell_text(player.location_slug, callback.from_user.id),
                reply_markup=bort_sell_inline(callback.from_user.id, player.location_slug),
            )
        except Exception:
            pass
        return

    if data == "marketnpc:bort_quest_menu":
        await callback.message.edit_text(
            render_bort_quest_text(callback.from_user.id),
            reply_markup=bort_quest_inline(callback.from_user.id),
        )
        await callback.answer()
        return

    if data == "marketnpc:bort_quest_take":
        quest_slug = "bort_supply_batch"
        quest = NPC_QUEST_DEFS[quest_slug]

        if _get_active_npc_order(callback.from_user.id, "bort"):
            await callback.answer("У Борта уже есть активный квест.", show_alert=True)
            return

        add_city_order(
            telegram_id=callback.from_user.id,
            order_slug=quest_slug,
            title=quest["title"],
            goal_text=quest["goal_text"],
            reward_gold=quest["reward_gold"],
            reward_exp=quest["reward_exp"],
        )

        await callback.message.edit_text(
            render_bort_quest_text(callback.from_user.id),
            reply_markup=bort_quest_inline(callback.from_user.id),
        )
        await callback.answer("Квест Борта взят.")
        return

    if data == "marketnpc:bort_quest_turnin":
        active = _get_active_npc_order(callback.from_user.id, "bort")
        if not active:
            await callback.answer("Нет активного квеста.", show_alert=True)
            return

        if not _npc_quest_ready(callback.from_user.id, active["order_slug"]):
            await callback.answer("Для сдачи ещё не хватает ресурсов.", show_alert=True)
            return

        if not _complete_npc_quest_requirements(callback.from_user.id, active["order_slug"]):
            await callback.answer("Не удалось списать ресурсы.", show_alert=True)
            return

        complete_city_order(active["id"])
        _grant_npc_quest_rewards(callback.from_user.id, active["order_slug"])
        q = NPC_QUEST_DEFS[active["order_slug"]]

        await callback.message.answer(
            f"✅ Борт принял квест:\n"
            f"{q['title']}\n"
            f"Награда: +{q['reward_gold']} золота, +{q['reward_exp']} опыта"
        )
        await callback.message.answer(
            render_bort_text(player.location_slug, callback.from_user.id),
            reply_markup=bort_main_inline(callback.from_user.id),
        )
        await callback.answer("Квест сдан.")
        return

    if data == "marketnpc:bort_back":
        await callback.message.edit_text(
            render_bort_text(player.location_slug, callback.from_user.id),
            reply_markup=bort_main_inline(callback.from_user.id),
        )
        await callback.answer()
        return

    # ---------------- CLOSE ----------------

    if data == "marketnpc:close":
        await callback.message.edit_text("Выбери действие внизу клавиатуры квартала.")
        await callback.answer()
        return

    await callback.answer()
