from pathlib import Path
from aiogram.types import Message, FSInputFile

from database.repositories import (
    add_player_experience,
    add_player_gold,
    get_player,
    get_resources,
    update_player_location,
    get_active_city_orders,
    count_active_city_orders,
    has_active_city_order,
    add_city_order,
)
from game.city_service import render_city_board, render_city_menu, render_guild_text, GUILD_QUESTS
from game.location_rules import is_city
from keyboards.board_menu import board_menu
from keyboards.city_menu import city_menu
from keyboards.main_menu import main_menu
from keyboards.shop_menu import shop_menu, bag_shop_menu, monster_shop_menu, sell_menu
from keyboards.craft_menu import craft_menu

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "city"

CITY_ORDER_LIMIT = 2

CITY_BOARD_ORDER_DEFS = {
    "herbalist_order": {
        "title": "Заказ травника",
        "goal_text": "Продай 3 🌿 Лесная трава скупщику ресурсов.",
        "reward_gold": 35,
        "reward_exp": 12,
    },
    "ore_order": {
        "title": "Нужна руда для печей",
        "goal_text": "Продай 2 🔥 Угольный камень.",
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
        await message.answer_photo(photo=FSInputFile(str(image_path)), caption=text, reply_markup=reply_markup)
    else:
        await message.answer(text, reply_markup=reply_markup)


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
        "Продай 3 🌿 Лесная трава скупщику ресурсов.\n"
        "Награда: 35 золота, 12 опыта\n\n"
        "2) Нужна руда для печей\n"
        "Продай 2 🔥 Угольный камень.\n"
        "Награда: 40 золота, 14 опыта\n\n"
        f"Активных заказов: {len(active_orders)}/{CITY_ORDER_LIMIT}"
    )

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
            f"Открой «📒 Мои заказы», чтобы посмотреть текущие.",
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

    await message.answer(
        "🏙 Возвращаемся в городское меню.",
        reply_markup=city_menu(player.current_district_slug),
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


async def _guild_handler(message: Message, title: str, description: str, profession: str, image_name: str):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Гильдии доступны только в городе.")
        return
    quests = [q for q in GUILD_QUESTS if q["profession"] == profession]
    await _answer_with_city_image(
        message,
        image_name,
        render_guild_text(title, description, quests),
        city_menu(player.current_district_slug),
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
    await _answer_with_city_image(message, "city_square.png", text, city_menu(player.current_district_slug))


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
    await message.answer(
        "🚶 Ты покидаешь Сереброград через главные ворота и выходишь в Тёмный лес.",
        reply_markup=main_menu("dark_forest", None),
    )


async def city_market_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Торговый квартал доступен только в городе.")
        return

    text = (
        "🏬 Торговый квартал\n\n"
        "Выбери раздел:\n"
        "— предметы\n"
        "— монстры\n"
        "— сумки\n"
        "— продажа ресурсов"
    )
    await _answer_with_city_image(message, "city_square.png", text, shop_menu())


async def city_bags_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Лавка сумок доступна только в городе.")
        return
    await _answer_with_city_image(message, "bag_market.png", "🎒 Лавка сумок открыта.", bag_shop_menu())


async def city_monsters_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Рынок монстров доступен только в городе.")
        return
    await _answer_with_city_image(message, "bag_market.png", "🐲 Рынок монстров открыт.", monster_shop_menu())


async def city_buyer_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Скупщик доступен только в городе.")
        return
    await _answer_with_city_image(
        message,
        "bag_market.png",
        "💰 Скупщик ресурсов готов принять твой товар.",
        sell_menu(get_resources(message.from_user.id)),
    )


async def city_alchemy_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Лаборатория доступна только в городе.")
        return
    await _answer_with_city_image(
        message,
        "alchemy_lab.png",
        "⚗ Алхимическая лаборатория готова к работе.",
        craft_menu(),
    )


async def city_traps_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Мастер ловушек доступен только в городе.")
        return
    text = (
        "🪤 Мастер ловушек\n\n"
        "Он советует всегда держать в запасе хотя бы одну ловушку и приносить редкие материалы для будущих улучшений."
    )
    await _answer_with_city_image(message, "trap_workshop.png", text, city_menu(player.current_district_slug))
