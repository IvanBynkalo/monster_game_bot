import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command

from config import BOT_TOKEN
from handlers.start import start_handler
from handlers.map import map_handler, location_handler, move_handler
from handlers.world import world_handler
from handlers.district import district_handler, district_move_handler
from handlers.explore import explore_handler
from handlers.encounter import attack_handler, capture_handler, flee_handler
from handlers.monsters import monsters_handler, set_active_monster_handler, heal_monster_handler
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

dp.message.register(profile_handler, lambda message: message.text == "🧭 Профиль")
dp.message.register(quests_handler, lambda message: message.text == "📜 Квесты")
dp.message.register(restore_energy_handler, lambda message: message.text == "⚡ Восстановить энергию")
dp.message.register(monsters_handler, lambda message: message.text == "🐲 Мои монстры")
dp.message.register(heal_monster_handler, lambda message: message.text == "❤️ Лечить монстра")
dp.message.register(world_handler, lambda message: message.text == "🌍 Мир")
dp.message.register(map_handler, lambda message: message.text == "🗺 Карта")
dp.message.register(location_handler, lambda message: message.text == "📍 Локация")
dp.message.register(district_handler, lambda message: message.text == "🧭 Район")
dp.message.register(move_handler, lambda message: message.text and message.text.startswith("🚶 "))
dp.message.register(district_move_handler, lambda message: message.text and message.text.startswith("🧭→ "))
dp.message.register(explore_handler, lambda message: message.text == "🌲 Исследовать")
dp.message.register(attack_handler, lambda message: message.text == "⚔️ Атаковать")
dp.message.register(capture_handler, lambda message: message.text == "🎯 Поймать")
dp.message.register(flee_handler, lambda message: message.text == "🏃 Убежать")
dp.message.register(set_active_monster_handler, lambda message: message.text and message.text.startswith("✅ "))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
