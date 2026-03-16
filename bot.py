import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command

from config import BOT_TOKEN
from handlers.start import start_handler
from handlers.map import map_handler, location_handler, move_handler, navigation_handler
from handlers.world import world_handler
from handlers.story import story_handler
from handlers.district import district_handler, district_move_handler
from handlers.explore import explore_handler
from handlers.encounter import attack_handler, capture_handler, flee_handler, skill_handler, trap_handler
from handlers.monsters import monsters_handler, set_active_monster_handler, heal_monster_handler
from handlers.inventory import inventory_handler, use_small_potion_handler, use_energy_capsule_handler, back_to_menu_handler
from handlers.profile import profile_handler, restore_energy_handler
from handlers.quests import quests_handler
from handlers.admin import (
    admin_panel_handler,
    grant_gold_handler,
    grant_energy_handler,
    heal_all_handler,
    teleport_location_handler,
    teleport_district_handler,
    reset_player_handler,
)

def text_is(*variants):
    return lambda message: (message.text or "").strip() in variants

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

dp.message.register(profile_handler, text_is("Профиль", "🧭 Профиль", "🧭 Профіль"))
dp.message.register(story_handler, text_is("Сюжет", "🧾 Сюжет"))
dp.message.register(quests_handler, text_is("Квесты", "📜 Квесты"))
dp.message.register(restore_energy_handler, text_is("Восстановить энергию", "⚡ Восстановить энергию"))
dp.message.register(monsters_handler, text_is("Мои монстры", "🐲 Мои монстры", "🐉 Мои монстры"))
dp.message.register(inventory_handler, text_is("🎒 Инвентарь", "Инвентарь"))
dp.message.register(heal_monster_handler, text_is("Лечить монстра", "❤️ Лечить монстра"))
dp.message.register(world_handler, text_is("Мир", "🌍 Мир"))
dp.message.register(map_handler, text_is("Карта", "🗺 Карта"))
dp.message.register(location_handler, text_is("Локация", "📍 Локация"))
dp.message.register(district_handler, text_is("Район", "🧭 Район"))
dp.message.register(navigation_handler, text_is("🧭 Перемещение", "Перемещение"))
dp.message.register(move_handler, lambda message: (message.text or "").startswith("Перейти: ") or (message.text or "").startswith("🚶 "))
dp.message.register(district_move_handler, lambda message: (message.text or "").startswith("Район: ") or (message.text or "").startswith("🧭→ "))
dp.message.register(explore_handler, text_is("Исследовать", "🌲 Исследовать"))
dp.message.register(attack_handler, text_is("Атаковать", "⚔️ Атаковать"))
dp.message.register(skill_handler, text_is("Навык", "✨ Навык"))
dp.message.register(use_small_potion_handler, text_is("🧪 Малое зелье"))
dp.message.register(use_energy_capsule_handler, text_is("⚡ Капсула энергии"))
dp.message.register(back_to_menu_handler, text_is("⬅️ Назад в меню"))
dp.message.register(capture_handler, text_is("Поймать", "🎯 Поймать"))
dp.message.register(trap_handler, text_is("🪤 Простая ловушка", "🪤 Ловушка"))
dp.message.register(flee_handler, text_is("Убежать", "🏃 Убежать"))
dp.message.register(set_active_monster_handler, lambda message: (message.text or "").startswith("Активный ") or (message.text or "").startswith("✅ "))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
