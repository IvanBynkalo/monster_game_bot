from aiogram.types import Message

from database.repositories import get_player, get_player_quests
from keyboards.main_menu import main_menu

def _render_quests(quests: dict):
    lines = ["📜 Квесты игрока", ""]
    for quest_id, quest in quests.items():
        status = "✅ Выполнен" if quest["completed"] else "🕒 В процессе"
        lines.extend([
            f"{quest['title']}",
            f"{quest['description']}",
            f"Прогресс: {quest['progress']}/{quest['target_value']}",
            f"Награда: 💰 {quest['reward_gold']} | ✨ {quest['reward_exp']}",
            f"Статус: {status}",
            "",
        ])
    return "\n".join(lines)

async def quests_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    quests = get_player_quests(message.from_user.id)
    await message.answer(_render_quests(quests), reply_markup=main_menu(player.location_slug))
