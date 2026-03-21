from aiogram.types import Message

from database.repositories import (
    add_captured_monster,
    add_item,
    add_player_experience,
    add_player_gold,
    buy_resource_from_city_market,
    get_city_resource_market,
    get_player,
    get_resources,
    improve_profession_from_action,
    progress_board_quests,
    progress_extra_quests,
    purchase_market_item,
    purchase_market_monster,
    sell_resource_to_city_market,
    set_ui_screen,
)
from game.location_rules import get_shop_name, has_shop, is_city
from game.market_service import (
    BAG_OFFERS,
    get_resource_label,
    get_resource_slug_from_buy_button,
    get_resource_slug_from_sell_button,
    render_bag_shop_text,
    render_resource_buy_text,
    render_resource_sell_text,
)
from game.shop_service import (
    MONSTER_SHOP_OFFERS,
    render_item_shop_text,
    render_monster_shop_text,
    render_shop_menu_text,
)
from keyboards.main_menu import main_menu
from keyboards.shop_menu import (
    bag_shop_menu,
    buy_resources_menu,
    item_shop_menu,
    monster_shop_menu,
    sell_menu,
    shop_menu,
)

ITEM_NAME_TO_SLUG = {
    "🛒 Купить: Малое зелье": "small_potion",
    "🛒 Купить: Капсула энергии": "energy_capsule",
    "🛒 Купить: Простая ловушка": "basic_trap",
}

MONSTER_BUTTON_TO_SLUG = {
    "🛒 Купить монстра: Лесной спрайт": "forest_sprite",
    "🛒 Купить монстра: Болотный охотник": "swamp_hunter",
    "🛒 Купить монстра: Угольный клык": "ember_fang",
}


def _check_city_shop(player):
    return player and has_shop(player.location_slug) and is_city(player.location_slug)


def _merchant_gain_text(gain: dict | None) -> str:
    if not gain:
        return ""

    if gain.get("is_max_level"):
        return "\n💼 Торговец: максимальный уровень."

    if gain.get("leveled_up"):
        return f"\n🎉 💼 Торговец повышен до {gain['level_after']} уровня!"

    return (
        f"\n💼 Торговец: +{gain['gained_exp']} опыта "
        f"({gain['exp_after']}/{gain['exp_to_next']})"
    )


async def shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await message.answer(
            "Лавки и здания работают только в городе. Вернись в Сереброград.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    set_ui_screen(message.from_user.id, "shop")
    await message.answer(
        get_shop_name(player.location_slug) + "\n\n" + render_shop_menu_text(),
        reply_markup=shop_menu(),
    )


async def item_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Покупки доступны только в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    set_ui_screen(message.from_user.id, "item_shop")
    from game.shop_service import ITEM_ORDER, get_market_item_price
    from database.repositories import get_market_item_entry
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    LABELS = {
        "small_potion":   ("🧪", "Малое зелье"),
        "energy_capsule": ("⚡", "Капсула энергии"),
        "basic_trap":     ("🪤", "Простая ловушка"),
        "flee_elixir":    ("💨", "Эликсир побега"),
        "revival_shard":  ("💎", "Осколок возрождения"),
    }
    rows = []
    for slug in ITEM_ORDER:
        emoji, name = LABELS.get(slug, ("🛒", slug))
        price = get_market_item_price(slug)
        rows.append([InlineKeyboardButton(
            text=f"🛒 {emoji} {name} — {price}з",
            callback_data=f"shop:buy:{slug}"
        )])
    # Extra items
    for slug in ["flee_elixir", "revival_shard"]:
        try:
            from game.item_service import ITEMS
            if slug in ITEMS:
                emoji, name = LABELS.get(slug, ("🛒", slug))
                rows.append([InlineKeyboardButton(
                    text=f"🛒 {emoji} {name} — 60з",
                    callback_data=f"shop:buy:{slug}"
                )])
        except Exception:
            pass
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="shop:back")])
    inline_kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await message.answer(
        render_item_shop_text(),
        reply_markup=item_shop_menu(),
    )
    await message.answer("🛒 Купить:", reply_markup=inline_kb)


async def monster_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Покупки доступны только в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    set_ui_screen(message.from_user.id, "monster_shop")
    await message.answer(
        render_monster_shop_text(),
        reply_markup=monster_shop_menu(),
    )


async def bag_shop_handler(message: Message):
    """Перенаправляем в inline-лавку сумок (Мирна в city.py)."""
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Сумки продаются только в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return
    # Используем inline-версию через city_bags_handler
    from handlers.city import city_bags_handler
    await city_bags_handler(message)


async def buy_bag_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Сумки продаются только в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    text = (message.text or "").strip()

    offer = None
    for item in BAG_OFFERS.values():
        if text.startswith(f"🛒 Купить сумку: {item['name']}"):
            offer = item
            break

    if not offer:
        await message.answer("Не удалось определить сумку.", reply_markup=bag_shop_menu())
        return

    if player.bag_capacity >= offer["capacity"]:
        await message.answer("У тебя уже есть сумка не хуже этой.", reply_markup=bag_shop_menu())
        return

    if player.gold < offer["price"]:
        await message.answer("Недостаточно золота.", reply_markup=bag_shop_menu())
        return

    player.gold -= offer["price"]
    player.bag_capacity = offer["capacity"]

    extras = []
    for quest in progress_extra_quests(message.from_user.id, "bag_upgrade", 1):
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )

    text = (
        f"🎒 Куплена сумка: {offer['name']}\n"
        f"Новая вместимость: {player.bag_capacity}\n"
        f"Потрачено: {offer['price']} золота\n"
        f"Осталось золота: {player.gold}"
    )

    if extras:
        text += "\n\n" + "\n\n".join(extras)

    await message.answer(text, reply_markup=bag_shop_menu())


async def buy_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Покупки доступны только в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    slug = ITEM_NAME_TO_SLUG.get((message.text or "").strip())
    if not slug:
        await message.answer("Не удалось определить товар.", reply_markup=item_shop_menu())
        return

    price = purchase_market_item(message.from_user.id, slug)
    if price is None:
        await message.answer("Недостаточно золота для покупки.", reply_markup=item_shop_menu())
        return

    add_item(message.from_user.id, slug, 1)

    await message.answer(
        f"✅ Покупка успешна.\n"
        f"Товар добавлен в инвентарь.\n"
        f"Потрачено: {price} золота\n"
        f"Осталось золота: {player.gold}",
        reply_markup=item_shop_menu(),
    )


async def buy_monster_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Покупки доступны только в городе.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    slug = MONSTER_BUTTON_TO_SLUG.get((message.text or "").strip())
    if not slug:
        await message.answer("Не удалось определить монстра.", reply_markup=monster_shop_menu())
        return

    price = purchase_market_monster(message.from_user.id, slug)
    if price is None:
        await message.answer("Недостаточно золота для покупки.", reply_markup=monster_shop_menu())
        return

    offer = MONSTER_SHOP_OFFERS[slug]
    monster = add_captured_monster(
        telegram_id=message.from_user.id,
        name=offer["name"],
        rarity=offer["rarity"],
        mood=offer["mood"],
        hp=offer["hp"],
        attack=offer["attack"],
        source_type="рынок",
    )
    monster["monster_type"] = offer["monster_type"]

    await message.answer(
        f"✅ Ты купил монстра: {monster['name']}\n"
        f"Потрачено: {price} золота\n"
        f"Осталось золота: {player.gold}",
        reply_markup=monster_shop_menu(),
    )


async def sell_resources_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Продавать можно только в городе у торговца.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "sell_shop")

    await message.answer(
        render_resource_sell_text(
            city_slug=player.location_slug,
            resources=resources,
            merchant_level=player.merchant_level,
        ),
        reply_markup=sell_menu(
            city_slug=player.location_slug,
            resources=resources,
            merchant_level=player.merchant_level,
        ),
    )


async def buy_resources_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Покупать ресурсы можно только в городе у торговца.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    market = get_city_resource_market(player.location_slug)
    set_ui_screen(message.from_user.id, "buy_resources")

    await message.answer(
        render_resource_buy_text(player.location_slug),
        reply_markup=buy_resources_menu(player.location_slug, market),
    )


async def sell_resource_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Продавать можно только в городе у торговца.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    slug = get_resource_slug_from_sell_button(message.text)
    if not slug:
        await message.answer("Не удалось определить ресурс.", reply_markup=shop_menu())
        return

    resources = get_resources(message.from_user.id)
    if resources.get(slug, 0) <= 0:
        await message.answer("У тебя нет этого ресурса.", reply_markup=shop_menu())
        return

    gold = sell_resource_to_city_market(
        telegram_id=message.from_user.id,
        city_slug=player.location_slug,
        slug=slug,
        amount=1,
    )

    if gold is None:
        await message.answer("Не удалось продать ресурс.", reply_markup=shop_menu())
        return

    profession_gain = improve_profession_from_action(message.from_user.id, "merchant", 1)

    extras = []
    for quest in progress_board_quests(message.from_user.id, "sell_resource", 1):
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )

    for quest in progress_extra_quests(message.from_user.id, "sell_gold", gold):
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )

    text = (
        f"💰 Продажа успешна.\n"
        f"Получено: {gold} золота за 1 шт.\n"
        f"Теперь золота: {player.gold}"
        f"{_merchant_gain_text(profession_gain)}"
    )

    if extras:
        text += "\n\n" + "\n\n".join(extras)

    updated_resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "sell_shop")

    await message.answer(
        text,
        reply_markup=sell_menu(
            city_slug=player.location_slug,
            resources=updated_resources,
            merchant_level=player.merchant_level,
        ),
    )


async def buy_resource_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer(
            "Покупать ресурсы можно только в городе у торговца.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    slug = get_resource_slug_from_buy_button(message.text)
    if not slug:
        await message.answer("Не удалось определить ресурс.", reply_markup=shop_menu())
        return

    price = buy_resource_from_city_market(
        telegram_id=message.from_user.id,
        city_slug=player.location_slug,
        slug=slug,
        amount=1,
    )

    if price is None:
        await message.answer(
            "Недостаточно золота или товара уже нет на складе.",
            reply_markup=buy_resources_menu(
                player.location_slug,
                get_city_resource_market(player.location_slug),
            ),
        )
        return

    await message.answer(
        f"🛒 Покупка успешна.\n"
        f"Получен ресурс: {get_resource_label(slug)}\n"
        f"Потрачено: {price} золота\n"
        f"Осталось золота: {player.gold}",
        reply_markup=buy_resources_menu(
            player.location_slug,
            get_city_resource_market(player.location_slug),
        ),
    )


async def back_to_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    set_ui_screen(message.from_user.id, "shop")
    await message.answer(
        render_shop_menu_text(),
        reply_markup=shop_menu(),
    )
