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
)

from game.city_service import render_city_menu, render_guild_text, GUILD_QUESTS
from game.craft_service import render_craft_text
from game.location_rules import is_city
from keyboards.board_menu import board_menu
from keyboards.city_menu import city_menu, district_actions_menu
from keyboards.main_menu import main_menu
from keyboards.shop_menu import bag_shop_menu, monster_shop_menu, sell_menu
from keyboards.craft_menu import craft_menu

# Эти импорты используют текущие товарные данные магазина.
# Если у тебя названия модулей/констант отличаются, скажи — подгоню под твой проект.
from game.shop_service import MONSTER_SHOP_OFFERS
from game.market_service import BAG_OFFERS, get_resource_label
from database.repositories import get_city_resource_market

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


# =========================================================
# INLINE UI: ТОРГОВЫЙ КВАРТАЛ
# =========================================================

def market_merchants_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧵 Мирна — портная лавка", callback_data="marketnpc:mirna")],
            [InlineKeyboardButton(text="🐲 Варг — лавка монстров", callback_data="marketnpc:varg")],
            [InlineKeyboardButton(text="📦 Борт — лавка ресурсов", callback_data="marketnpc:bort")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="marketnpc:back")],
        ]
    )


def mirna_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧾 Показать товары", callback_data="mirna:catalog")],
            [InlineKeyboardButton(text="🛒 Открыть лавку", callback_data="mirna:open_shop")],
            [InlineKeyboardButton(text="⬅️ К торговцам", callback_data="marketnpc:list")],
        ]
    )


def varg_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧾 Показать монстров", callback_data="varg:catalog")],
            [InlineKeyboardButton(text="🛒 Купить монстра", callback_data="varg:open_buy")],
            [InlineKeyboardButton(text="💰 Продать монстра", callback_data="varg:open_sell")],
            [InlineKeyboardButton(text="⬅️ К торговцам", callback_data="marketnpc:list")],
        ]
    )


def bort_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧾 Витрина ресурсов", callback_data="bort:catalog")],
            [InlineKeyboardButton(text="💰 Продать ресурсы", callback_data="bort:open_sell")],
            [InlineKeyboardButton(text="🛒 Купить ресурсы", callback_data="bort:open_buy")],
            [InlineKeyboardButton(text="⬅️ К торговцам", callback_data="marketnpc:list")],
        ]
    )


def render_mirna_catalog_text() -> str:
    lines = [
        "🧵 Мирна — портная лавка",
        "",
        "Мирна шьёт полезные вещи для вылазок.",
        "Сейчас в продаже в первую очередь сумки, позже сюда добавим плащи, одежду и прочее тканевое снаряжение.",
        "",
        "Текущие товары:",
    ]

    if not BAG_OFFERS:
        lines.append("• Сейчас товары не настроены.")
    else:
        for offer in BAG_OFFERS.values():
            name = offer.get("name", "Неизвестный товар")
            price = offer.get("price", 0)
            capacity = offer.get("capacity", 0)
            lines.append(f"• {name} — {price} золота (вместимость: {capacity})")

    lines.append("")
    lines.append("Нажми «Открыть лавку», чтобы перейти к текущей покупке.")
    return "\n".join(lines)


def render_varg_catalog_text() -> str:
    lines = [
        "🐲 Варг — лавка монстров",
        "",
        "Варг торгует монстрами и также готов выкупать подходящих существ.",
        "",
        "Сейчас в продаже:",
    ]

    if not MONSTER_SHOP_OFFERS:
        lines.append("• Список монстров пока пуст.")
    else:
        for offer in MONSTER_SHOP_OFFERS.values():
            name = offer.get("name", "Неизвестный монстр")
            price = offer.get("price", 0)
            lines.append(f"• {name} — {price} золота")

    lines.append("")
    lines.append("Покупка уже подключена через текущий магазин. Продажу монстров можно подключить следующим этапом.")
    return "\n".join(lines)


def render_bort_catalog_text(city_slug: str) -> str:
    market = get_city_resource_market(city_slug)

    lines = [
        "📦 Борт — лавка ресурсов",
        "",
        "Борт торгует городскими запасами и выкупает добытые материалы.",
        "",
        "Текущая витрина / рынок города:",
    ]

    if not market:
        lines.append("• Сейчас товары не настроены.")
    else:
        for slug, entry in market.items():
            label = get_resource_label(slug)
            buy_price = int(entry.get("buy_price", 0))
            sell_price = int(entry.get("sell_price", 0))
            stock = int(entry.get("stock", 0))
            lines.append(
                f"• {label} — покупает по {buy_price}, продаёт по {sell_price}, запас: {stock}"
            )

    lines.append("")
    lines.append("Продажа ресурсов уже работает через текущий экран. Покупку подключим следующим этапом, если в проекте уже есть готовый buy-flow.")
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

    await message.answer(
        "👥 Торговцы квартала\n\nВыбери, к кому подойти:",
        reply_markup=market_merchants_inline(),
    )


async def city_bags_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Портная лавка доступна только в городе.")
        return

    set_ui_screen(message.from_user.id, "bag_shop")
    await _answer_with_city_image(
        message,
        "bag_market.png",
        "🧵 Мирна открывает портную лавку.\n\nСейчас здесь доступны в первую очередь сумки, позже добавим и другие швейные товары.",
        bag_shop_menu(),
    )


async def city_monsters_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Лавка монстров доступна только в городе.")
        return

    set_ui_screen(message.from_user.id, "monster_shop")
    await _answer_with_city_image(
        message,
        "bag_market.png",
        "🐲 Варг открывает лавку монстров.\n\nСейчас можно покупать монстров, позже сюда подключим и полноценную продажу монстров Варгу.",
        monster_shop_menu(),
    )


async def city_buyer_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "shop")

    await message.answer(
        "📦 Борт открывает лавку ресурсов.\n\n"
        "Сейчас через этот экран уже работает продажа ресурсов городу.",
        reply_markup=sell_menu(
            city_slug=player.location_slug,
            resources=resources,
            merchant_level=player.merchant_level,
        ),
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
# CALLBACK: ТОРГОВЫЙ КВАРТАЛ
# =========================================================

async def market_inline_callback(callback: CallbackQuery):
    player = get_player(callback.from_user.id)
    if not player:
        await callback.answer("Сначала напиши /start", show_alert=True)
        return

    data = callback.data or ""

    if data in {"marketnpc:list", "marketnpc:back"}:
        await callback.message.edit_text(
            "👥 Торговцы квартала\n\nВыбери, к кому подойти:",
            reply_markup=market_merchants_inline(),
        )
        await callback.answer()
        return

    if data == "marketnpc:mirna":
        await callback.message.edit_text(
            "🧵 Мирна — портная лавка\n\n"
            "Мирна шьёт вещи для путешественников.\n"
            "Сейчас у неё в продаже главным образом сумки, но дальше здесь появятся и другие швейные товары.",
            reply_markup=mirna_inline(),
        )
        await callback.answer()
        return

    if data == "marketnpc:varg":
        await callback.message.edit_text(
            "🐲 Варг — лавка монстров\n\n"
            "Варг торгует монстрами и в будущем сможет выкупать подходящих существ у игрока.",
            reply_markup=varg_inline(),
        )
        await callback.answer()
        return

    if data == "marketnpc:bort":
        await callback.message.edit_text(
            "📦 Борт — лавка ресурсов\n\n"
            "Борт работает с городскими запасами и ресурсами экспедиций.\n"
            "У него можно и продавать, и покупать ресурсы.",
            reply_markup=bort_inline(),
        )
        await callback.answer()
        return

    if data == "mirna:catalog":
        await callback.message.edit_text(
            render_mirna_catalog_text(),
            reply_markup=mirna_inline(),
        )
        await callback.answer()
        return

    if data == "mirna:open_shop":
        await callback.answer("Открываю лавку Мирны...")
        await city_bags_handler(callback.message)
        return

    if data == "varg:catalog":
        await callback.message.edit_text(
            render_varg_catalog_text(),
            reply_markup=varg_inline(),
        )
        await callback.answer()
        return

    if data == "varg:open_buy":
        await callback.answer("Открываю лавку Варга...")
        await city_monsters_handler(callback.message)
        return

    if data == "varg:open_sell":
        await callback.message.edit_text(
            "🐲 Варг — продажа монстров\n\n"
            "Интерфейс продажи монстров Варгу будет следующим этапом.\n"
            "Сейчас в проекте уже сохранён смысл этой роли: Варг не только продаёт, но и покупает монстров.",
            reply_markup=varg_inline(),
        )
        await callback.answer()
        return

    if data == "bort:catalog":
        await callback.message.edit_text(
            render_bort_catalog_text(player.location_slug),
            reply_markup=bort_inline(),
        )
        await callback.answer()
        return

    if data == "bort:open_sell":
        await callback.answer("Открываю продажу ресурсов...")
        await city_buyer_handler(callback.message)
        return

    if data == "bort:open_buy":
        await callback.message.edit_text(
            "📦 Борт — покупка ресурсов\n\n"
            "Смысл роли уже заложен: Борт и покупает, и продаёт ресурсы.\n"
            "Следующим этапом сюда подключим реальный экран покупки ресурсов, если он уже есть в проекте.",
            reply_markup=bort_inline(),
        )
        await callback.answer()
        return

    await callback.answer()
