import asyncio
import logging
import re

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery, ErrorEvent, Message, PreCheckoutQuery, SuccessfulPayment,
)

from config import BOT_TOKEN, ADMIN_IDS
from database.init_db import init_db
from utils.notifier import set_bot
from handlers.start import start_handler
from handlers.map import map_handler, location_handler, move_handler, navigation_handler
from handlers.world import world_handler
from handlers.story import story_handler
from handlers.more import more_handler, back_handler, healing_menu_handler
from handlers.district import district_handler, district_move_handler
from handlers.explore import explore_handler, elite_expedition_handler
from handlers.dungeon import dungeon_handler, dungeon_next_room_handler, dungeon_fight_handler, dungeon_leave_handler
from handlers.gather import gather_handler
from handlers.encounter import (
    attack_handler,
    capture_handler,
    flee_handler,
    skill_handler,
    trap_handler,
    poison_trap_handler,
)
from handlers.world_boss import boss_attack_handler, boss_flee_handler
from handlers.monsters import monsters_handler, set_active_monster_handler, heal_monster_handler
from handlers.inventory import (
    inventory_handler,
    use_small_potion_handler,
    use_big_potion_handler,
    use_energy_capsule_handler,
    use_spark_tonic_handler,
    use_field_elixir_handler,
    use_crystal_focus_handler,
    use_swamp_antidote_handler,
    back_to_menu_handler,
)
from handlers.craft import craft_handler, resources_handler, craft_item_handler
from handlers.profile import profile_handler, restore_energy_handler, profile_tab_callback, profile_stat_callback
from handlers.healing import heal_hero_handler, rest_hero_handler
from handlers.codex import codex_handler, bestiary_callback
from handlers.relics import relics_handler
from handlers.progression import (
    progression_handler,
    add_strength_handler,
    add_agility_handler,
    add_intellect_handler,
    upgrade_bag_handler,
)
from handlers.quests import quests_handler
from handlers.shop import (
    shop_handler,
    item_shop_handler,
    monster_shop_handler,
    bag_shop_handler,
    buy_bag_handler,
    buy_item_handler,
    buy_monster_handler,
    back_to_shop_handler,
    sell_resources_handler,
    sell_resource_item_handler,
)
from handlers.city import (
    city_handler,
    city_board_handler,
    guild_hunters_handler,
    guild_gatherers_handler,
    guild_geologists_handler,
    guild_alchemists_handler,
    city_guard_handler,
    city_guilds_handler,
    leave_city_handler,
    city_market_handler,
    city_bags_handler,
    city_monsters_handler,
    city_buyer_handler,
    city_craft_quarter_handler,
    city_alchemy_handler,
    city_traps_handler,
    take_herbalist_order_handler,
    take_ore_order_handler,
    my_board_orders_handler,
    back_to_city_from_board_handler,
    market_inline_callback,
)
from handlers.admin import (
    admin_panel_handler,
    admin_buttons_handler,
    grant_gold_handler,
    grant_energy_handler,
    heal_all_handler,
    teleport_location_handler,
    teleport_district_handler,
    reset_player_handler,
    ADMIN_STATES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    text = value.strip().lower()
    text = re.sub(r"[\u200b-\u200d\ufe0f]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def text_is(*variants: str):
    normalized_variants = {normalize_text(v) for v in variants}

    def _check(message: Message) -> bool:
        return normalize_text(message.text) in normalized_variants

    return _check


def text_startswith(*prefixes: str):
    normalized_prefixes = [normalize_text(p) for p in prefixes]

    def _check(message: Message) -> bool:
        text = normalize_text(message.text)
        return any(text.startswith(prefix) for prefix in normalized_prefixes)

    return _check


def text_contains(*variants: str):
    normalized_variants = [normalize_text(v) for v in variants]

    def _check(message: Message) -> bool:
        text = normalize_text(message.text)
        return any(variant in text for variant in normalized_variants)

    return _check


def is_admin(user_id: int) -> bool:
    return user_id in set(ADMIN_IDS or [])


def has_admin_state(message: Message) -> bool:
    return is_admin(message.from_user.id) and message.from_user.id in ADMIN_STATES


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.message.register(start_handler, Command("start"))
dp.message.register(admin_panel_handler, Command("admin"))
dp.message.register(grant_gold_handler, Command("grant_gold"))
dp.message.register(grant_energy_handler, Command("grant_energy"))
dp.message.register(heal_all_handler, Command("heal_all"))
dp.message.register(teleport_location_handler, Command("teleport_location"))
dp.message.register(teleport_district_handler, Command("teleport_district"))
dp.message.register(reset_player_handler, Command("reset_player"))

dp.message.register(codex_handler, text_is("📖 Кодекс", "Кодекс"))
dp.message.register(relics_handler, text_is("🔮 Реликвии", "Реликвии"))
dp.message.register(profile_handler, text_is("Профиль", "🧭 Профиль", "🧭 Профіль", "🧭 профиль", "👤 Персонаж", "Персонаж"))
dp.message.register(monsters_handler, text_is("Мои монстры", "🐲 Мои монстры", "🐉 Мои монстры"))

dp.message.register(set_active_monster_handler, text_startswith("✅ "))

dp.message.register(inventory_handler, text_is("🎒 Инвентарь", "Инвентарь"))
dp.message.register(craft_handler, text_is("🛠 Мастерская", "Мастерская"))
dp.message.register(resources_handler, text_is("📦 Ресурсы", "Ресурсы"))
dp.message.register(use_small_potion_handler, text_is("🧪 Малое зелье", "Малое зелье"))
dp.message.register(use_big_potion_handler, text_is("🧪 Большое зелье", "Большое зелье"))
dp.message.register(use_energy_capsule_handler, text_is("⚡ Капсула энергии", "Капсула энергии"))
dp.message.register(use_spark_tonic_handler, text_is("✨ Настой искры", "Настой искры"))
dp.message.register(use_field_elixir_handler, text_is("🌼 Эликсир лугов", "Эликсир лугов"))
dp.message.register(use_crystal_focus_handler, text_is("💎 Кристальный концентрат", "Кристальный концентрат"))
dp.message.register(use_swamp_antidote_handler, text_is("🪷 Болотный антидот", "Болотный антидот"))
dp.message.register(back_to_menu_handler, text_is("⬅️ Назад в меню", "Назад в меню"))
dp.message.register(
    craft_item_handler,
    text_startswith(
        "🧪 Создать:",
        "🪤 Создать:",
        "✨ Создать:",
        "🌼 Создать:",
        "💎 Создать:",
        "🪷 Создать:",
    )
)

dp.message.register(explore_handler, text_is("Исследовать", "🌲 Исследовать"))
dp.message.register(elite_expedition_handler, text_is("🔥 Элитная экспедиция", "Элитная экспедиция"))
dp.message.register(dungeon_handler, text_is("🕳 Подземелье", "Подземелье"))
dp.message.register(dungeon_next_room_handler, text_is("➡️ Следующая комната", "Следующая комната"))
dp.message.register(dungeon_fight_handler, text_is("⚔️ Сразиться", "⚔ Сразиться", "Сразиться"))
dp.message.register(dungeon_leave_handler, text_is("🏃 Покинуть подземелье", "Покинуть подземелье"))
dp.message.register(gather_handler, text_is("🧺 Собирать ресурсы", "Собирать ресурсы"))
dp.message.register(story_handler, text_is("Сюжет", "🧾 Сюжет"))
dp.message.register(quests_handler, text_is("Квесты", "📜 Квесты"))
dp.message.register(
    navigation_handler,
    text_is("🧭 Перемещение", "Перемещение", "🧭 Навигация", "Навигация",
            "🧭 Переместиться", "Переместиться"),
)
dp.message.register(more_handler, text_is("📂 Ещё", "Ещё"))
dp.message.register(healing_menu_handler, text_is("❤️ Лечение", "Лечение"))

dp.message.register(city_handler, text_is("🏙 Город", "Город"))
dp.message.register(progression_handler, text_is("📈 Развитие", "Развитие"))
dp.message.register(add_strength_handler, text_is("💪 +Сила", "+Сила"))
dp.message.register(add_agility_handler, text_is("🤸 +Ловкость", "+Ловкость"))
dp.message.register(add_intellect_handler, text_is("🧠 +Интеллект", "+Интеллект"))
dp.message.register(upgrade_bag_handler, text_is("🎒 Улучшить сумку", "Улучшить сумку"))

dp.message.register(shop_handler, text_is("🏪 Магазин", "Магазин"))
dp.message.register(
    city_market_handler,
    text_is(
        "🏬 Торговый квартал",
        "🏪 Торговая лавка",
        "Торговый квартал",
        "Торговая лавка",
    ),
)
dp.message.register(city_bags_handler, text_is("🎒 Лавка сумок", "Лавка сумок"))
dp.message.register(city_monsters_handler, text_is("🐲 Рынок монстров", "Рынок монстров"))
dp.message.register(city_buyer_handler, text_is("💰 Скупщик ресурсов", "Скупщик ресурсов"))
dp.message.register(city_board_handler, text_is("📜 Доска заказов", "Доска заказов"))
dp.message.register(city_guilds_handler, text_is("🏛 Гильдии", "Гильдии"))
dp.message.register(city_craft_quarter_handler, text_is("⚒ Ремесленный квартал", "Ремесленный квартал"))
dp.message.register(take_herbalist_order_handler, text_is("📌 Взять заказ: Травник"))
dp.message.register(take_ore_order_handler, text_is("📌 Взять заказ: Руда"))
dp.message.register(my_board_orders_handler, text_is("📒 Мои заказы"))
dp.message.register(back_to_city_from_board_handler, text_is("⬅️ Назад в город"))
dp.message.register(city_alchemy_handler, text_is("⚗ Алхимическая лаборатория", "Алхимическая лаборатория"))
dp.message.register(city_traps_handler, text_is("🪤 Мастер ловушек", "Мастер ловушек"))
dp.message.register(guild_hunters_handler, text_is("🎯 Гильдия ловцов", "Гильдия ловцов"))
dp.message.register(guild_gatherers_handler, text_is("🌿 Гильдия собирателей", "Гильдия собирателей"))
dp.message.register(guild_geologists_handler, text_is("⛏ Гильдия геологов", "Гильдия геологов"))
dp.message.register(guild_alchemists_handler, text_is("⚗ Гильдия алхимиков", "Гильдия алхимиков"))
dp.message.register(city_guard_handler, text_is("🛡 Городская стража", "Городская стража"))
dp.message.register(leave_city_handler, text_is("🚶 Покинуть город", "Покинуть город"))

# Магазины
dp.message.register(bag_shop_handler, text_is("🎒 Сумки", "Сумки"))
dp.message.register(buy_bag_handler, text_startswith("🛒 Купить сумку:", "Купить сумку:"))
dp.message.register(sell_resources_handler, text_is("💰 Продать ресурсы", "Продать ресурсы"))
dp.message.register(sell_resource_item_handler, text_startswith("💰 Продать:", "Продать:"))
dp.message.register(item_shop_handler, text_is("🧪 Магазин предметов", "Магазин предметов"))
dp.message.register(monster_shop_handler, text_is("🐲 Магазин монстров", "Магазин монстров"))
dp.message.register(back_to_shop_handler, text_is("⬅️ Назад в магазин", "Назад в магазин"))
dp.message.register(buy_item_handler, text_startswith("🛒 Купить:", "Купить:"))
dp.message.register(buy_monster_handler, text_startswith("🛒 Купить монстра:", "Купить монстра:"))

dp.message.register(world_handler, text_is("Мир", "🌍 Мир"))
dp.message.register(map_handler, text_is("Карта", "🗺 Карта"))
dp.message.register(location_handler, text_is("Локация", "📍 Локация"))
dp.message.register(district_handler, text_is("Район", "🧭 Район"))
dp.message.register(heal_monster_handler, text_is("Лечить монстра", "❤️ Лечить монстра"))
dp.message.register(restore_energy_handler, text_is("Восстановить энергию", "⚡ Восстановить энергию"))
dp.message.register(heal_hero_handler, text_is("Лечить героя", "🩹 Лечить героя"))
dp.message.register(rest_hero_handler, text_is("Отдых героя", "😴 Отдых героя"))

dp.message.register(back_handler, text_is("⬅️ Назад", "Назад"))

dp.message.register(move_handler, text_startswith("Перейти:", "🚶 "))
dp.message.register(district_move_handler, text_startswith("Район:", "🧭→ "))

# ===== Обычный бой с монстром =====
dp.message.register(
    attack_handler,
    lambda m: text_contains("атаковать")(m) and not text_contains("босса")(m),
)
dp.message.register(
    skill_handler,
    lambda m: text_contains("навык")(m),
)
dp.message.register(
    capture_handler,
    lambda m: text_contains("поймать")(m),
)
dp.message.register(
    trap_handler,
    lambda m: text_contains("ловушка")(m) and not text_contains("ядовит")(m),
)
dp.message.register(
    poison_trap_handler,
    lambda m: text_contains("ядовитая ловушка", "ядовит ловушка")(m),
)
dp.message.register(
    flee_handler,
    lambda m: text_contains("убежать")(m) and not text_contains("босса")(m),
)

# ===== Бой с мировым боссом =====
dp.message.register(
    boss_attack_handler,
    text_contains("атаковать босса"),
)
dp.message.register(
    boss_flee_handler,
    text_contains("убежать от босса"),
)

dp.callback_query.register(
    market_inline_callback,
    lambda c: c.data and c.data.startswith("marketnpc:"),
)
dp.callback_query.register(
    profile_tab_callback,
    lambda c: c.data and c.data.startswith("profile:tab:"),
)
dp.callback_query.register(
    profile_stat_callback,
    lambda c: c.data and c.data.startswith("profile:stat:"),
)
dp.callback_query.register(
    bestiary_callback,
    lambda c: c.data and c.data.startswith("bestiary:"),
)

dp.message.register(admin_panel_handler, text_is("🛠 Админ-панель"))
dp.message.register(
    admin_buttons_handler,
    lambda message: is_admin(message.from_user.id) and (
        normalize_text(message.text) in {
            normalize_text("💰 Выдать золото"),
            normalize_text("⚡ Выдать энергию"),
            normalize_text("❤️ Вылечить монстров"),
            normalize_text("🧹 Сбросить игрока"),
            normalize_text("🗺 Телепорт по локации"),
            normalize_text("🧭 Телепорт по району"),
            normalize_text("❌ Закрыть админ-панель"),
        } or has_admin_state(message)
    )
)



# ═══════════════════════════════════════════════════════════════════════
# НОВЫЕ СИСТЕМЫ v3.0
# ═══════════════════════════════════════════════════════════════════════

# ── Stars оплата (рек. #14) ───────────────────────────────────────────

@dp.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(lambda m: m.successful_payment is not None)
async def successful_payment_handler(message: Message):
    from game.stars_shop import process_stars_purchase
    result = await process_stars_purchase(message.from_user.id,
                                          message.successful_payment.invoice_payload)
    if result:
        await message.answer(result)

@dp.message(Command("stars_shop"))
async def stars_shop_cmd(message: Message):
    from game.stars_shop import render_stars_shop
    await message.answer(render_stars_shop())

@dp.message(Command("buy_stars"))
async def buy_stars_cmd(message: Message):
    from game.stars_shop import send_stars_invoice, STARS_CATALOG
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /buy_stars <slug>\n/stars_shop — список товаров")
        return
    slug = parts[1].strip()
    if slug not in STARS_CATALOG:
        await message.answer(f"Товар не найден. /stars_shop — список")
        return
    await send_stars_invoice(bot, message.chat.id, slug)

@dp.message(Command("buy_season_pass"))
async def buy_season_pass_cmd(message: Message):
    from game.stars_shop import send_stars_invoice
    await send_stars_invoice(bot, message.chat.id, "season_pass")


# ── PvP (рек. #8) ─────────────────────────────────────────────────────

@dp.message(Command("pvp"))
async def pvp_cmd(message: Message):
    from game.pvp_service import render_pvp_stats
    await message.answer(render_pvp_stats(message.from_user.id))

@dp.message(Command("challenge"))
async def challenge_cmd(message: Message):
    from database.repositories import get_player, get_active_monster
    from game.pvp_service import calculate_pvp_battle, render_pvp_result
    from utils.notifier import notify_pvp_result
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /challenge <telegram_id>")
        return
    try:
        target_id = int(parts[1].strip())
    except ValueError:
        await message.answer("Укажи числовой Telegram ID.")
        return
    if target_id == message.from_user.id:
        await message.answer("Нельзя вызвать самого себя.")
        return
    target = get_player(target_id)
    if not target:
        await message.answer("Игрок не найден.")
        return
    if not get_active_monster(target_id):
        await message.answer(f"У {target.name} нет активного монстра.")
        return
    if not get_active_monster(message.from_user.id):
        await message.answer("У тебя нет активного монстра.")
        return
    result = calculate_pvp_battle(message.from_user.id, target_id)
    if "error" in result:
        await message.answer(f"❌ {result['error']}")
        return
    await message.answer(render_pvp_result(result, message.from_user.id))
    import asyncio
    asyncio.create_task(notify_pvp_result(target_id, result, target_id == result["winner_id"]))

@dp.message(Command("pvp_top"))
async def pvp_top_cmd(message: Message):
    from game.daily_service import render_pvp_leaderboard_text
    await message.answer(render_pvp_leaderboard_text())


# ── Таблица лидеров (рек. #13) ────────────────────────────────────────

@dp.message(Command("top"))
async def top_cmd(message: Message):
    from game.daily_service import render_leaderboard
    await message.answer(render_leaderboard())


# ── Ежедневные задания (рек. #12) ─────────────────────────────────────

@dp.message(Command("daily"))
async def daily_cmd(message: Message):
    from game.daily_service import get_daily_panel
    await message.answer(get_daily_panel(message.from_user.id))


# ── Сезонный пасс (рек. #15) ─────────────────────────────────────────

@dp.message(Command("season"))
async def season_cmd(message: Message):
    from game.season_pass_service import get_season_panel
    await message.answer(get_season_panel(message.from_user.id))


# ── Гильдии (рек. #10) ────────────────────────────────────────────────

@dp.message(Command("guild"))
async def guild_cmd(message: Message):
    from database.repositories import get_player_guild, get_guild_members
    from game.guild_service import render_guild_info, render_guild_list, list_guilds
    guild = get_player_guild(message.from_user.id)
    if guild:
        members = get_guild_members(guild["id"])
        await message.answer(render_guild_info(guild, members))
    else:
        guilds = list_guilds()
        text = render_guild_list(guilds)
        text += "\n\n/create_guild <название> — создать (200з, ур.5+)"
        text += "\n/join_guild <id> — вступить"
        await message.answer(text)

@dp.message(Command("create_guild"))
async def create_guild_cmd(message: Message):
    from game.guild_service import try_create_guild
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /create_guild <название>")
        return
    guild, err = try_create_guild(message.from_user.id, parts[1].strip())
    if err:
        await message.answer(f"❌ {err}")
    else:
        await message.answer(f"🏰 Гильдия «{guild['name']}» создана! ID: {guild['id']}")

@dp.message(Command("join_guild"))
async def join_guild_cmd(message: Message):
    from game.guild_service import try_join_guild
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /join_guild <id>")
        return
    try:
        ok, err = try_join_guild(message.from_user.id, int(parts[1].strip()))
        await message.answer("✅ Ты в гильдии!" if ok else f"❌ {err}")
    except ValueError:
        await message.answer("Укажи числовой ID гильдии.")

@dp.message(Command("leave_guild"))
async def leave_guild_cmd(message: Message):
    from game.guild_service import try_leave_guild
    ok, err = try_leave_guild(message.from_user.id)
    await message.answer("✅ Ты покинул гильдию." if ok else f"❌ {err}")

@dp.message(Command("guild_raid"))
async def guild_raid_cmd(message: Message):
    from database.repositories import get_player_guild
    from game.guild_service import simulate_guild_raid, GUILD_BOSSES
    guild = get_player_guild(message.from_user.id)
    if not guild:
        await message.answer("Ты не в гильдии. /guild")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        boss_list = "\n".join(f"  {b['slug']} — {b['name']} (HP {b['hp']})" for b in GUILD_BOSSES)
        await message.answer(f"Выбери босса:\n{boss_list}\n\n/guild_raid <slug>")
        return
    result = simulate_guild_raid(guild["id"], parts[1].strip())
    if "error" in result:
        await message.answer(f"❌ {result['error']}")
        return
    lines = [f"🏰 Рейд на {result['boss_name']}", f"Участников: {result['participants']}", ""]
    lines.extend(result["log"][:8])
    lines.append("")
    if result["victory"]:
        lines.append(f"🏆 ПОБЕДА! +{result['split_gold']}з, +{result['split_exp']} опыта каждому")
    else:
        lines.append(f"💀 Провал. HP босса: {result['boss_hp_left']} | Частичная: +{result['split_gold']}з")
    await message.answer("\n".join(lines))


# ── P2P рынок монстров (рек. #16) ─────────────────────────────────────

@dp.message(Command("market"))
async def market_p2p_cmd(message: Message):
    from game.p2p_market_service import render_p2p_market
    from database.repositories import get_p2p_market_listings
    await message.answer(render_p2p_market(get_p2p_market_listings()))

@dp.message(Command("sell_monster"))
async def sell_monster_cmd(message: Message):
    from game.p2p_market_service import try_list_monster
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /sell_monster <id> <цена>")
        return
    try:
        ok, err = try_list_monster(message.from_user.id, int(parts[1]), int(parts[2]))
        await message.answer(f"✅ Выставлен за {parts[2]}з!" if ok else f"❌ {err}")
    except ValueError:
        await message.answer("Неверный формат. Пример: /sell_monster 5 200")

@dp.message(Command("buy_monster"))
async def buy_monster_p2p_cmd(message: Message):
    from game.p2p_market_service import try_buy_monster
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /buy_monster <id>")
        return
    try:
        monster, info = try_buy_monster(message.from_user.id, int(parts[1]))
        if not monster:
            await message.answer(f"❌ {info}")
        else:
            seller_got = info.split(":")[1] if ":" in info else "?"
            await message.answer(f"✅ {monster['name']} куплен! Продавец получил {seller_got}з")
    except ValueError:
        await message.answer("Укажи числовой ID монстра.")

@dp.message(Command("delist"))
async def delist_cmd(message: Message):
    from game.p2p_market_service import try_delist_monster
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /delist <id>")
        return
    try:
        ok, err = try_delist_monster(message.from_user.id, int(parts[1]))
        await message.answer("✅ Снят с продажи." if ok else f"❌ {err}")
    except ValueError:
        await message.answer("Укажи числовой ID.")

@dp.message(Command("my_listings"))
async def my_listings_cmd(message: Message):
    from game.p2p_market_service import render_my_listings
    await message.answer(render_my_listings(message.from_user.id))


# ── Аналитика — только для админа (рек. #20) ─────────────────────────

@dp.message(Command("analytics"))
async def analytics_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    from utils.analytics import render_analytics_report
    await message.answer(render_analytics_report())



# ── Inline-бой (рек. от GPT: бой через Callback вместо Reply) ────────────────

@dp.callback_query(lambda c: c.data and c.data.startswith("fight:"))
async def fight_inline_callback(callback: CallbackQuery):
    """
    Inline-кнопки боя. Напрямую вызывает игровую логику
    (НЕ через handler(message) — там from_user был бы бот, а не игрок).
    """
    action = callback.data.split(":")[1]
    uid = callback.from_user.id

    from database.repositories import (
        get_pending_encounter, save_pending_encounter, clear_pending_encounter,
        get_player, get_active_monster, damage_active_monster, damage_player_hp,
        add_player_gold, add_player_experience, add_active_monster_experience,
    )
    from game.encounter_service import resolve_attack, resolve_capture, resolve_flee
    from game.monster_abilities import get_capture_bonus
    from game.skill_service import apply_skill
    from keyboards.main_menu import main_menu
    from keyboards.encounter_menu import encounter_inline_menu

    await callback.answer()

    enc = get_pending_encounter(uid)
    if not enc or enc.get("type") != "monster":
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.message.answer("Встреча завершена.")
        return

    player = get_player(uid)
    active = get_active_monster(uid)
    if not player or not active:
        await callback.message.answer("Ошибка: нет игрока или монстра.", reply_markup=main_menu(player.location_slug if player else "silver_city"))
        return

    result = None

    if action == "attack":
        result = resolve_attack(enc,
            active_monster_attack=active.get("attack", 3) + player.strength,
            attacker_type=active.get("monster_type"),
            active_monster=active)

    elif action == "skill":
        result = apply_skill(enc, active, player)
        if result is None:
            result = resolve_attack(enc,
                active_monster_attack=active.get("attack", 3) + player.strength,
                attacker_type=active.get("monster_type"),
                active_monster=active)

    elif action == "capture":
        capture_bon = get_capture_bonus(active)
        enc["bonus_capture"] = enc.get("bonus_capture", 0.0) + capture_bon
        result = resolve_capture(enc)

    elif action == "trap":
        from database.repositories import spend_item, get_item_count
        if get_item_count(uid, "basic_trap") <= 0:
            await callback.message.answer("У тебя нет ловушек.")
            return
        spend_item(uid, "basic_trap", 1)
        enc["hp"] = max(0, enc["hp"] - 8)
        enc["counter_multiplier"] = 0.5
        save_pending_encounter(uid, enc)
        result = {"ok": True, "finished": enc["hp"] <= 0, "victory": enc["hp"] <= 0,
                  "monster_defeated": enc["hp"] <= 0, "player_damage": 0,
                  "text": f"🪤 Ловушка сработала! {enc['monster_name']} получает 8 урона. HP: {max(0,enc['hp'])}",
                  "gold": enc.get("reward_gold", 0), "exp": enc.get("reward_exp", 0)}

    elif action == "poison_trap":
        from database.repositories import spend_item, get_item_count
        if get_item_count(uid, "poison_trap") <= 0:
            await callback.message.answer("У тебя нет ядовитых ловушек.")
            return
        spend_item(uid, "poison_trap", 1)
        enc["hp"] = max(0, enc["hp"] - 14)
        enc["counter_multiplier"] = 0.3
        save_pending_encounter(uid, enc)
        result = {"ok": True, "finished": enc["hp"] <= 0, "victory": enc["hp"] <= 0,
                  "monster_defeated": enc["hp"] <= 0, "player_damage": 0,
                  "text": f"☠️ Ядовитая ловушка! {enc['monster_name']} получает 14 урона. HP: {max(0,enc['hp'])}",
                  "gold": enc.get("reward_gold", 0), "exp": enc.get("reward_exp", 0)}

    elif action == "flee":
        result = resolve_flee(enc)

    if not result:
        await callback.message.answer("Неизвестное действие.")
        return

    # Apply damage to player's monster from enemy counter-attack
    if result.get("player_damage", 0) > 0:
        damage_active_monster(uid, result["player_damage"])
        active = get_active_monster(uid)

    lines = [result["text"]]

    # Monster HP after player's hit
    if not result.get("finished") and active:
        lines.append(f"❤️ Твой монстр: {active.get('current_hp',active['hp'])}/{active.get('max_hp',active['hp'])} HP")

    if result.get("finished"):
        clear_pending_encounter(uid)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        if result.get("victory") or result.get("captured"):
            gold = result.get("gold", 0)
            exp  = result.get("exp", 0)
            add_player_gold(uid, gold)
            add_player_experience(uid, exp)
            m, lvlups = add_active_monster_experience(uid, exp)
            lines.append(f"💰 +{gold} золота  ✨ +{exp} опыта")
            for lu in lvlups:
                lines.append(f"⬆️ Монстр достиг уровня {lu['level']}!")

            # Лут с зверя + бестиарий + трофей + недельный квест
            if enc.get("type") == "wildlife":
                from game.bestiary_service import register_bestiary_seen, check_trophy_drop
                from game.weekly_quest_service import progress_weekly_quest, claim_weekly_reward
                register_bestiary_seen(uid, enc["name"], "wildlife")

                # Лут-ресурс
                if enc.get("loot_slug"):
                    from database.repositories import add_resource
                    add_resource(uid, enc["loot_slug"], 1)
                    from game.gather_service import RESOURCES_BY_LOCATION
                    loot_name = enc["loot_slug"]
                    for loc_pool in RESOURCES_BY_LOCATION.values():
                        for r in loc_pool:
                            if r["slug"] == enc["loot_slug"]:
                                loot_name = r["name"]
                                break
                    lines.append(f"🎒 Добыча: {loot_name} x1")

                # Трофей (15% шанс с редких зверей)
                trophy = check_trophy_drop(enc["name"])
                if trophy:
                    from database.repositories import add_resource
                    add_resource(uid, trophy, 1)
                    from game.bestiary_service import TROPHY_ITEMS
                    trophy_name = TROPHY_ITEMS.get(trophy, {}).get("name", trophy)
                    lines.append(f"🏆 Трофей: {trophy_name}!")

                # Прогресс недельного квеста
                player_now = get_player(uid)
                if player_now:
                    wq_done = progress_weekly_quest(
                        uid, player_now.location_slug,
                        action="defeat_wildlife", name=enc["name"]
                    )
                    if wq_done:
                        reward_text = claim_weekly_reward(uid, wq_done)
                        lines.append(f"\n🎉 Недельный квест выполнен!\n{reward_text}")

            if result.get("captured"):
                from database.repositories import add_captured_monster
                add_captured_monster(uid, enc["monster_name"], enc.get("rarity","common"),
                    enc.get("mood","instinct"), enc.get("max_hp", enc.get("hp",10)),
                    enc.get("attack",3), source_type="wild")
                lines.append(f"🎯 {enc['monster_name']} пойман и добавлен в команду!")

            # Infection & birth
            from game.infection_service import apply_dominant_emotion_infection, render_infection_update
            from game.emotion_birth_service import try_birth_emotional_monster, render_birth_text
            from game.emotion_service import grant_event_emotions, render_emotion_changes
            district_mood = None
            _, changes = grant_event_emotions(uid, "battle_win", district_mood=district_mood)
            ec = render_emotion_changes(changes)
            if ec: lines.append(ec)
            inf = render_infection_update(apply_dominant_emotion_infection(uid))
            if inf: lines.append(inf)
            born = render_birth_text(try_birth_emotional_monster(uid))
            if born: lines.append(born)

        player = get_player(uid)
        await callback.message.answer("\n".join(lines),
            reply_markup=main_menu(player.location_slug if player else "silver_city"))
    else:
        # Battle continues - update encounter and show inline buttons again
        save_pending_encounter(uid, enc)
        active = get_active_monster(uid)
        has_trap = False
        has_ptrap = False
        from database.repositories import get_item_count
        has_trap  = get_item_count(uid, "basic_trap") > 0
        has_ptrap = get_item_count(uid, "poison_trap") > 0
        await callback.message.answer("\n".join(lines),
            reply_markup=encounter_inline_menu(has_trap=has_trap, has_poison_trap=has_ptrap))


@dp.callback_query(lambda c: c.data and c.data.startswith("loc:"))
async def location_inline_callback(callback: CallbackQuery):
    """Inline-действия в локации (исследовать, собирать, навигация)."""
    action = callback.data.split(":")[1]
    await callback.answer()
    if action == "explore":
        await explore_handler(callback.message)
    elif action == "gather":
        await gather_handler(callback.message)
    elif action == "dungeon":
        await dungeon_handler(callback.message)
    elif action == "navigate":
        await navigation_handler(callback.message)


@dp.callback_query(lambda c: c.data and c.data.startswith("monster:"))
async def monster_inline_callback(callback: CallbackQuery):
    """Inline-действия с монстрами (выбор активного, лечение, листинг)."""
    parts = callback.data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    mid_str = parts[2] if len(parts) > 2 else ""
    uid = callback.from_user.id

    await callback.answer()

    if action == "select" and mid_str.isdigit():
        # Показываем карточку монстра с inline-кнопками действий
        from database.repositories import get_monster_by_id
        from keyboards.monsters_menu import monster_actions_inline
        from game.infection_service import render_monster_infection
        from game.monster_abilities import render_abilities
        from game.type_service import get_type_label
        m = get_monster_by_id(uid, int(mid_str))
        if not m:
            await callback.message.answer("Монстр не найден.")
            return
        RARITY = {"common":"Обычный","rare":"Редкий","epic":"Эпический",
                  "legendary":"Легендарный","mythic":"Мифический"}
        text = (
            f"{'✅ Активный — ' if m.get('is_active') else ''}{m['name']}\n"
            f"Редкость: {RARITY.get(m['rarity'], m['rarity'])}\n"
            f"Уровень: {m.get('level',1)} | XP: {m.get('experience',0)}/{m.get('level',1)*5}\n"
            f"HP: {m.get('current_hp',m['hp'])}/{m.get('max_hp',m['hp'])} | ATK: {m['attack']}\n"
            f"Тип: {get_type_label(m.get('monster_type'))}\n"
            f"{render_abilities(m)}\n"
            f"{render_monster_infection(m)}"
        )
        if m.get("combo_mutation"):
            text += f"\n⚡ Комбо: {m['combo_mutation']}"
        await callback.message.answer(text, reply_markup=monster_actions_inline(m))

    elif action == "activate" and mid_str.isdigit():
        from database.repositories import set_active_monster
        m = set_active_monster(uid, int(mid_str))
        if m:
            await callback.message.answer(f"✅ {m['name']} теперь активный монстр.")
        else:
            await callback.message.answer("Не удалось сменить монстра.")

    elif action == "heal" and mid_str.isdigit():
        from database.repositories import get_monster_by_id, save_monster
        m = get_monster_by_id(uid, int(mid_str))
        if m:
            m["current_hp"] = m.get("max_hp", m["hp"])
            save_monster(m)
            await callback.message.answer(f"❤️ {m['name']} вылечен! HP: {m['current_hp']}/{m['max_hp']}")

    elif action == "list" and mid_str.isdigit():
        await callback.message.answer(
            f"Укажи цену: /sell_monster {mid_str} <цена>\n"
            f"Пример: /sell_monster {mid_str} 150"
        )

    elif action == "delist" and mid_str.isdigit():
        from game.p2p_market_service import try_delist_monster
        ok, err = try_delist_monster(uid, int(mid_str))
        await callback.message.answer("✅ Снят с продажи." if ok else f"❌ {err}")

    elif action == "back":
        await monsters_handler(callback.message)



@dp.message(Command("wildlife_raid"))
async def wildlife_raid_cmd(message: Message):
    from database.repositories import get_player_guild
    from game.guild_service import simulate_wildlife_raid, RARE_WILDLIFE_BOSSES
    guild = get_player_guild(message.from_user.id)
    if not guild:
        await message.answer("Ты не в гильдии. /guild")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        boss_list = "\n".join(
            f"  {b['slug']} — {b['name']} (HP {b['hp']}, исслед. {b['min_exploration']}%+)"
            for b in RARE_WILDLIFE_BOSSES
        )
        await message.answer(f"🐾 Рейд на редкого зверя:\n{boss_list}\n\n/wildlife_raid <slug>")
        return
    result = simulate_wildlife_raid(guild["id"], parts[1].strip())
    if "error" in result:
        await message.answer(f"❌ {result['error']}")
        return
    lines = [f"🐾 Рейд гильдии на {result['boss_name']}", f"Участников: {result['participants']}", ""]
    lines.extend(result["log"][:8])
    lines.append("")
    if result["victory"]:
        lines.append(f"🏆 ПОБЕДА! +{result['split_gold']}з, +{result['split_exp']} опыта каждому")
        lines.append(f"🏅 Трофей получает победитель рейда!")
    else:
        lines.append(f"💀 Провал. Осталось HP: {result['boss_hp_left']} | Частичная: +{result['split_gold']}з")
    await message.answer("\n".join(lines))

@dp.errors()
async def global_error_handler(event: ErrorEvent):
    logger.exception("Unhandled update error: %s", event.exception)
    return True


@dp.message()
async def fallback_handler(message: Message):
    logger.info(
        "UNHANDLED MESSAGE: user=%s raw=%r normalized=%r",
        message.from_user.id,
        message.text,
        normalize_text(message.text),
    )
    await message.answer(
        f"Кнопка получена, но обработчик не сработал:\n{message.text}\n\n"
        f"Нажми /start для перезагрузки меню."
    )


async def main():
    # Инициализируем SQLite базу данных (рек. #1)
    init_db()
    logger.info("Database initialized")

    # Регистрируем бот в системе уведомлений (рек. #19)
    set_bot(bot)
    logger.info("Bot started — v3.0")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
