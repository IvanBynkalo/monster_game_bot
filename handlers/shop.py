from aiogram.types import Message

from database.repositories import (
    add_captured_monster,
    add_item,
    get_player,
    purchase_market_item,
    purchase_market_monster,
    get_resources,
    spend_resource,
    progress_board_quests,
    progress_extra_quests,
    add_player_gold,
    add_player_experience,
    set_ui_screen,
)
from game.shop_service import MONSTER_SHOP_OFFERS, render_item_shop_text, render_monster_shop_text, render_shop_menu_text
from game.location_rules import has_shop, get_shop_name, is_city
from game.market_service import get_resource_sell_price
from keyboards.shop_menu import shop_menu, item_shop_menu, monster_shop_menu, sell_menu, bag_shop_menu
from keyboards.main_menu import main_menu

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

BAG_OFFERS = {
    "🛒 Купить сумку: Поясная сумка": {"name": "Поясная сумка", "capacity": 16, "price": 45},
    "🛒 Купить сумку: Полевой ранец": {"name": "Полевой ранец", "capacity": 24, "price": 95},
    "🛒 Купить сумку: Экспедиционный рюкзак": {"name": "Экспедиционный рюкзак", "capacity": 36, "price": 180},
}

SELL_MAPPING = {
    "💰 Продать: 🌿 Лесная трава": "forest_herb",
    "💰 Продать: 🍄 Шляпка гриба": "mushroom_cap",
    "💰 Продать: ✨ Серебряный мох": "silver_moss",
    "💰 Продать: 🪴 Болотный мох": "swamp_moss",
    "💰 Продать: 🧫 Токсичная спора": "toxic_spore",
    "💰 Продать: ⚫ Чёрная жемчужина тины": "black_pearl",
    "💰 Продать: 🔥 Угольный камень": "ember_stone",
    "💰 Продать: 🍂 Пепельный лист": "ash_leaf",
    "💰 Продать: 💠 Ядро магмы": "magma_core",
    "💰 Продать: 🌾 Полевая трава": "field_grass",
    "💰 Продать: 🌼 Солнечный цветок": "sun_blossom",
    "💰 Продать: 💧 Кристалл росы": "dew_crystal",
    "💰 Продать: ⛏ Сырая руда": "raw_ore",
    "💰 Продать: 🪨 Осколок гранита": "granite_shard",
    "💰 Продать: 💎 Небесный кристалл": "sky_crystal",
    "💰 Продать: 🪷 Болотный цветок": "bog_flower",
    "💰 Продать: 🕯 Тёмная смола": "dark_resin",
    "💰 Продать: 🎐 Призрачный камыш": "ghost_reed",
}

def _check_city_shop(player):
    return player and has_shop(player.location_slug) and is_city(player.location_slug)

async def shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if not _check_city_shop(player):
        await message.answer("Лавки и здания работают только в городе. Вернись в Сереброград.", reply_markup=main_menu(player.location_slug))
        return
    await message.answer(get_shop_name(player.location_slug) + "\n\n" + render_shop_menu_text(), reply_markup=shop_menu())

async def item_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer("Покупки доступны только в городе.", reply_markup=main_menu(player.location_slug))
        return
    set_ui_screen(message.from_user.id, "item_shop")
    await message.answer(render_item_shop_text(), reply_markup=item_shop_menu())

async def monster_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer("Покупки доступны только в городе.", reply_markup=main_menu(player.location_slug))
        return
    set_ui_screen(message.from_user.id, "monster_shop")
    await message.answer(render_monster_shop_text(), reply_markup=monster_shop_menu())

async def bag_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer("Сумки продаются только в городе.", reply_markup=main_menu(player.location_slug))
        return
    lines = [
        "🎒 Лавка сумок",
        "",
        "Поясная сумка — 16 мест — 45 золота",
        "Полевой ранец — 24 места — 95 золота",
        "Экспедиционный рюкзак — 36 мест — 180 золота",
        "",
        f"Твоя текущая вместимость: {player.bag_capacity}",
    ]
    await message.answer("\n".join(lines), reply_markup=bag_shop_menu())

async def buy_bag_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer("Сумки продаются только в городе.", reply_markup=main_menu(player.location_slug))
        return
    offer = BAG_OFFERS.get((message.text or "").strip())
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
        extras.append(f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта")
    text = f"🎒 Куплена сумка: {offer['name']}\nНовая вместимость: {player.bag_capacity}\nОсталось золота: {player.gold}"
    if extras:
        text += "\n\n" + "\n\n".join(extras)
    await message.answer(text, reply_markup=bag_shop_menu())

async def buy_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer("Покупки доступны только в городе.", reply_markup=main_menu(player.location_slug))
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
    await message.answer(f"✅ Покупка успешна.\nТовар добавлен в инвентарь.\nПотрачено: {price} золота\nОсталось золота: {player.gold}", reply_markup=item_shop_menu())

async def buy_monster_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer("Покупки доступны только в городе.", reply_markup=main_menu(player.location_slug))
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
    await message.answer(f"✅ Ты купил монстра: {monster['name']}\nПотрачено: {price} золота\nОсталось золота: {player.gold}", reply_markup=monster_shop_menu())

async def sell_resources_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer("Продавать можно только в городе у торговца.", reply_markup=main_menu(player.location_slug))
        return
    set_ui_screen(message.from_user.id, "sell_shop")
    await message.answer("Выбери ресурс для продажи.", reply_markup=sell_menu(get_resources(message.from_user.id)))

async def sell_resource_item_handler(message: Message):
    player = get_player(message.from_user.id)
    if not _check_city_shop(player):
        await message.answer("Продавать можно только в городе у торговца.", reply_markup=main_menu(player.location_slug))
        return
    slug = SELL_MAPPING.get((message.text or "").strip())
    if not slug:
        await message.answer("Не удалось определить ресурс.", reply_markup=shop_menu())
        return
    resources = get_resources(message.from_user.id)
    if resources.get(slug, 0) <= 0:
        await message.answer("У тебя нет этого ресурса.", reply_markup=shop_menu())
        return
    spend_resource(message.from_user.id, slug, 1)
    gold = get_resource_sell_price(slug, merchant_level=player.merchant_level, amount=1)
    player.gold += gold
    if player.merchant_level < 5:
        player.merchant_level += 1
    extras = []
    for quest in progress_board_quests(message.from_user.id, "sell_resource", slug, 1):
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта")
    for quest in progress_extra_quests(message.from_user.id, "sell_gold", gold):
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        extras.append(f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта")
    text = f"💰 Продажа успешна. Получено: {gold} золота\nТеперь золота: {player.gold}\n💼 Торговец: {player.merchant_level}"
    if extras:
        text += "\n\n" + "\n\n".join(extras)
    set_ui_screen(message.from_user.id, "sell_shop")
    await message.answer(text, reply_markup=shop_menu())

async def back_to_shop_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    set_ui_screen(message.from_user.id, "shop")
    await message.answer(render_shop_menu_text(), reply_markup=shop_menu())
