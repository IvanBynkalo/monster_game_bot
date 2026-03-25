"""
handlers/shop.py

Торговые цепочки города.

Что изменено:
- все входы в торговлю ведут в контекст Торгового квартала;
- ui_screen ставится явно для каждого экрана;
- кнопка "назад" возвращает в квартал, а не в случайное место;
- исправлен импорт grant_bag;
- добавлены безопасные обновления золота/данных игрока после покупок;
- сохранена совместимость по именам функций и кнопок из bot.py.
"""

# ── Error tracking shim ─────────────────────────────
try:
    from game.error_tracker import log_logic_error as _log_logic, log_exception as _log_exc
except Exception:
    def _log_logic(*a, **k):
        pass

    def _log_exc(*a, **k):
        pass
# ────────────────────────────────────────────────────

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
    grant_bag,
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
    render_resource_buy_text,
    render_resource_sell_text,
)
from game.shop_service import (
    MONSTER_SHOP_OFFERS,
    render_item_shop_text,
    render_monster_shop_text,
    render_shop_menu_text,
)
from keyboards.city_menu import district_actions_menu
from keyboards.main_menu import main_menu
from keyboards.shop_menu import buy_resources_menu, sell_menu

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


def _root_menu(player, telegram_id: int):
    return main_menu(
        player.location_slug,
        getattr(player, "current_district_slug", None),
        telegram_id=telegram_id,
    )


def _check_city_shop(player) -> bool:
    return bool(player and has_shop(player.location_slug) and is_city(player.location_slug))


def _market_quarter_kb(telegram_id: int):
    return district_actions_menu("market_square", telegram_id)


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


async def _send_city_only_error(message: Message, text: str):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    await message.answer(text, reply_markup=_root_menu(player, message.from_user.id))


async def shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(
            message,
            "Лавки и здания работают только в городе. Вернись в Сереброград.",
        )
        return

    set_ui_screen(message.from_user.id, "shop")
    await message.answer(
        get_shop_name(player.location_slug) + "\n\n" + render_shop_menu_text(),
        reply_markup=_market_quarter_kb(message.from_user.id),
    )


async def item_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Покупки доступны только в городе.")
        return

    set_ui_screen(message.from_user.id, "item_shop")

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from database.repositories import get_inventory as _get_inventory
    from game.shop_service import ITEM_ORDER, get_market_item_price

    labels = {
        "small_potion": ("🧪", "Малое зелье"),
        "energy_capsule": ("⚡", "Капсула энергии"),
        "basic_trap": ("🪤", "Простая ловушка"),
        "flee_elixir": ("💨", "Эликсир побега"),
        "revival_shard": ("💎", "Осколок возрождения"),
    }
    inventory = _get_inventory(message.from_user.id)

    rows = []
    for slug in ITEM_ORDER:
        emoji, name = labels.get(slug, ("🛒", slug))
        price = get_market_item_price(slug)
        have = inventory.get(slug, 0)
        suffix = f" · у тебя: {have}" if have > 0 else ""
        rows.append([
            InlineKeyboardButton(
                text=f"🛒 {emoji} {name} — {price}з{suffix}",
                callback_data=f"shop:buy:{slug}",
            )
        ])

    for slug in ("flee_elixir", "revival_shard"):
        try:
            from game.item_service import ITEMS
            if slug in ITEMS:
                emoji, name = labels.get(slug, ("🛒", slug))
                have = inventory.get(slug, 0)
                suffix = f" · у тебя: {have}" if have > 0 else ""
                rows.append([
                    InlineKeyboardButton(
                        text=f"🛒 {emoji} {name} — 60з{suffix}",
                        callback_data=f"shop:buy:{slug}",
                    )
                ])
        except Exception:
            pass

    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="shop:back")])

    await message.answer(
        render_item_shop_text(),
        reply_markup=_market_quarter_kb(message.from_user.id),
    )
    await message.answer(
        "🛒 Выбери предмет для покупки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


async def monster_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Покупки доступны только в городе.")
        return

    set_ui_screen(message.from_user.id, "monster_shop")
    await message.answer(
        render_monster_shop_text(),
        reply_markup=_market_quarter_kb(message.from_user.id),
    )


async def bag_shop_handler(message: Message):
    """Перенаправление в inline-лавку Мирны из city.py."""
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Сумки продаются только в городе.")
        return

    set_ui_screen(message.from_user.id, "bag_shop")
    from handlers.city import city_bags_handler
    await city_bags_handler(message)


async def buy_bag_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Сумки продаются только в городе.")
        return

    text = (message.text or "").strip()

    offer_slug = None
    offer = None
    for slug, item in BAG_OFFERS.items():
        if text.startswith(f"🛒 Купить сумку: {item['name']}"):
            offer_slug = slug
            offer = item
            break

    if not offer or not offer_slug:
        await message.answer(
            "Не удалось определить сумку.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
        return

    if player.gold < offer["price"]:
        await message.answer(
            "Недостаточно золота.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
        return

    added, bag = grant_bag(
        message.from_user.id,
        offer_slug,
        offer["name"],
        offer["capacity"],
        source="shop",
        sell_price=max(1, offer["price"] // 2),
        auto_equip=True,
    )
    if not added:
        await message.answer(
            "Такая сумка у тебя уже есть.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
        return

    add_player_gold(message.from_user.id, -offer["price"])
    updated_player = get_player(message.from_user.id)

    extras = []
    for quest in progress_extra_quests(message.from_user.id, "bag_upgrade", 1):
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )

    equip_text = (
        "Сумка автоматически надета." if bag and bag.get("is_equipped") else "Сумка отправлена в гардероб Мирны."
    )
    result = (
        f"🎒 Куплена сумка: {offer['name']}\n"
        f"Вместимость: {offer['capacity']}\n"
        f"{equip_text}\n"
        f"Потрачено: {offer['price']} золота\n"
        f"Осталось золота: {getattr(updated_player, 'gold', 0)}"
    )
    if extras:
        result += "\n\n" + "\n\n".join(extras)

    await message.answer(result, reply_markup=_market_quarter_kb(message.from_user.id))


async def buy_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Покупки доступны только в городе.")
        return

    slug = ITEM_NAME_TO_SLUG.get((message.text or "").strip())
    if not slug:
        await message.answer(
            "Не удалось определить товар.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
        return

    price = purchase_market_item(message.from_user.id, slug)
    if price is None:
        await message.answer(
            "Недостаточно золота для покупки.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
        return

    add_item(message.from_user.id, slug, 1)
    updated_player = get_player(message.from_user.id)

    await message.answer(
        "✅ Покупка успешна.\n"
        "Товар добавлен в инвентарь.\n"
        f"Потрачено: {price} золота\n"
        f"Осталось золота: {getattr(updated_player, 'gold', 0)}",
        reply_markup=_market_quarter_kb(message.from_user.id),
    )


async def buy_monster_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Покупки доступны только в городе.")
        return

    slug = MONSTER_BUTTON_TO_SLUG.get((message.text or "").strip())
    if not slug:
        await message.answer(
            "Не удалось определить монстра.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
        return

    price = purchase_market_monster(message.from_user.id, slug)
    if price is None:
        await message.answer(
            "Недостаточно золота для покупки.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
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
    updated_player = get_player(message.from_user.id)

    await message.answer(
        f"✅ Ты купил монстра: {monster['name']}\n"
        f"Потрачено: {price} золота\n"
        f"Осталось золота: {getattr(updated_player, 'gold', 0)}",
        reply_markup=_market_quarter_kb(message.from_user.id),
    )


async def sell_resources_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Продавать можно только в городе у торговца.")
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
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Покупать ресурсы можно только в городе у торговца.")
        return

    market = get_city_resource_market(player.location_slug)
    set_ui_screen(message.from_user.id, "buy_resources")

    await message.answer(
        render_resource_buy_text(player.location_slug),
        reply_markup=buy_resources_menu(player.location_slug, market),
    )


async def sell_resource_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Продавать можно только в городе у торговца.")
        return

    slug = get_resource_slug_from_sell_button(message.text)
    if not slug:
        await message.answer(
            "Не удалось определить ресурс.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
        return

    resources = get_resources(message.from_user.id)
    if resources.get(slug, 0) <= 0:
        await message.answer(
            "У тебя нет этого ресурса.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
        return

    gold = sell_resource_to_city_market(
        telegram_id=message.from_user.id,
        city_slug=player.location_slug,
        slug=slug,
        amount=1,
    )
    if gold is None:
        await message.answer(
            "Не удалось продать ресурс.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
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

    updated_player = get_player(message.from_user.id)
    updated_resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "sell_shop")

    text = (
        "💰 Продажа успешна.\n"
        f"Получено: {gold} золота за 1 шт.\n"
        f"Теперь золота: {getattr(updated_player, 'gold', 0)}"
        f"{_merchant_gain_text(profession_gain)}"
    )
    if extras:
        text += "\n\n" + "\n\n".join(extras)

    await message.answer(
        text,
        reply_markup=sell_menu(
            city_slug=player.location_slug,
            resources=updated_resources,
            merchant_level=getattr(updated_player, 'merchant_level', player.merchant_level),
        ),
    )


async def buy_resource_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not _check_city_shop(player):
        await _send_city_only_error(message, "Покупать ресурсы можно только в городе у торговца.")
        return

    slug = get_resource_slug_from_buy_button(message.text)
    if not slug:
        await message.answer(
            "Не удалось определить ресурс.",
            reply_markup=_market_quarter_kb(message.from_user.id),
        )
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

    updated_player = get_player(message.from_user.id)
    await message.answer(
        "🛒 Покупка успешна.\n"
        f"Получен ресурс: {get_resource_label(slug)}\n"
        f"Потрачено: {price} золота\n"
        f"Осталось золота: {getattr(updated_player, 'gold', 0)}",
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
        reply_markup=_market_quarter_kb(message.from_user.id),
    )
