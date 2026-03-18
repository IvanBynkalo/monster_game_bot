
from aiogram.types import Message
from database.repositories import get_player, progress_extra_quests, progress_guild_quests, add_player_gold, add_player_experience
from game.gather_service import gather_resource
from keyboards.main_menu import main_menu

async def gather_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    result = gather_resource(player, player.location_slug)

    if not result:
        await message.answer("В этой области пока нечего собрать.")
        return
    if result.get("error"):
        await message.answer(result["error"], reply_markup=main_menu(player.location_slug))
        return

    extra = ""
    guild_completed = progress_guild_quests(message.from_user.id, "gather", result.get('amount', 1)) if not result.get('rare') else []
    if result.get('kind') == 'geologist':
        guild_completed += progress_guild_quests(message.from_user.id, 'geology', result.get('amount', 1))
    if result.get("rare"):
        completed = progress_extra_quests(message.from_user.id, "rare_gather", 1)
        if completed:
            reward_parts = []
            for quest in completed:
                add_player_gold(message.from_user.id, quest["reward_gold"])
                add_player_experience(message.from_user.id, quest["reward_exp"])
                reward_parts.append(
                    f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта"
                )
            extra = "\n\n" + "\n\n".join(reward_parts)
    if guild_completed:
        reward_parts = []
        for quest in guild_completed:
            add_player_gold(message.from_user.id, quest['reward_gold'])
            add_player_experience(message.from_user.id, quest['reward_exp'])
            reward_parts.append(f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта")
        extra += ("\n\n" if extra else "") + "\n\n".join(reward_parts)

    rare_text = "\nРедкость: редкий ресурс!" if result.get("rare") else ""
    await message.answer(
        f"🧺 Ты нашёл ресурс: {result['name']} x{result.get('amount', 1)}{rare_text}" + extra,
        reply_markup=main_menu(player.location_slug)
    )
