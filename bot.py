import asyncio
import logging
import re

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import ErrorEvent, Message

from config import BOT_TOKEN, ADMIN_IDS
from handlers.start import start_handler
from handlers.map import map_handler, location_handler, move_handler, navigation_handler
from handlers.world import world_handler
from handlers.story import story_handler
from handlers.more import more_handler, back_handler
from handlers.district import district_handler, district_move_handler
from handlers.explore import explore_handler, elite_expedition_handler
from handlers.dungeon import dungeon_handler, dungeon_next_room_handler, dungeon_fight_handler, dungeon_leave_handler
from handlers.gather import gather_handler
from handlers.encounter import attack_handler, capture_handler, flee_handler, skill_handler, trap_handler, poison_trap_handler
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
from handlers.craft import craft_handler, resources_handler, craft_item_handler, back_from_craft_handler
from handlers.profile import profile_handler, restore_energy_handler
from handlers.healing import heal_hero_handler, rest_hero_handler
from handlers.codex import codex_handler
from handlers.relics import relics_handler
from handlers.progression import (
    progression_handler,
    add_strength_handler,
    add_agility_handler,
    add_intellect_handler,
    upgrade_bag_handler,
    back_from_progression_handler,
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
dp.message.register(profile_handler, text_is("Профиль", "🧭 Профиль", "🧭 Профіль", "🧭 профиль"))
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
dp.message.register(dungeon_fight_handler, text_is("⚔️ Сразиться", "Сразиться"))
dp.message.register(dungeon_leave_handler, text_is("🏃 Покинуть подземелье", "Покинуть подземелье"))
dp.message.register(gather_handler, text_is("🧺 Собирать ресурсы", "Собирать ресурсы"))
dp.message.register(story_handler, text_is("Сюжет", "🧾 Сюжет"))
dp.message.register(quests_handler, text_is("Квесты", "📜 Квесты"))
dp.message.register(
    navigation_handler,
    text_is("🧭 Перемещение", "Перемещение", "🧭 Навигация", "Навигация"),
)
dp.message.register(more_handler, text_is("📂 Ещё", "Ещё"))

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

dp.message.register(boss_attack_handler, text_is("Атаковать босса", "⚔️ Атаковать босса"))
dp.message.register(boss_flee_handler, text_is("Убежать от босса", "🏃 Убежать от босса"))

dp.callback_query.register(
    market_inline_callback,
    lambda c: c.data and c.data.startswith("marketnpc:"),
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


@dp.errors()
async def global_error_handler(event: ErrorEvent):
    logger.exception("Unhandled update error: %s", event.exception)
    return True


@dp.message()
async def fallback_handler(message: Message):
    logger.info("UNHANDLED MESSAGE: user=%s text=%r", message.from_user.id, message.text)
    await message.answer(
        f"Кнопка получена, но обработчик не сработал:\n{message.text}\n\n"
        f"Нажми /start для перезагрузки меню."
    )


async def main():
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
