from aiogram.types import Message

from database.repositories import (
    add_player_experience,
    add_player_gold,
    get_player,
    progress_extra_quests,
    progress_guild_quests,
)
from game.gather_service import gather_resource, render_gather_hint
from game.location_rules import is_city
from keyboards.main_menu import main_menu


async def gather_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if is_city(player.location_slug):
        await message.answer(
            "🏙 В городе ресурсы не собирают.\n"
            "Сначала выйди в дикую локацию, например в Тёмный лес.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    result = gather_resource(player, player.location_slug)

    if not result:
        await message.answer(
            render_gather_hint(player.location_slug),
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    if result.get("error"):
        await message.answer(
            result["error"],
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    reward_parts: list[str] = []

    guild_completed = progress_guild_quests(
        message.from_user.id,
        "gather",
        result.get("amount", 1),
    ) if not result.get("rare") else []

    if result.get("kind") == "geologist":
        guild_completed += progress_guild_quests(
            message.from_user.id,
            "geology",
            result.get("amount", 1),
        )

    if result.get("rare"):
        completed = progress_extra_quests(message.from_user.id, "rare_gather", 1)
        for quest in completed:
            add_player_gold(message.from_user.id, quest["reward_gold"])
            add_player_experience(message.from_user.id, quest["reward_exp"])
            reward_parts.append(
                f"📜 Квест выполнен: {quest['title']}\n"
                f"💰 Награда: +{quest['reward_gold']} золота\n"
                f"✨ Награда: +{quest['reward_exp']} опыта"
            )

    for quest in guild_completed:
        add_player_gold(message.from_user.id, quest["reward_gold"])
        add_player_experience(message.from_user.id, quest["reward_exp"])
        reward_parts.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )

    kind_text = {
        "gatherer": "🌿 Навык собирателя растёт.",
        "hunter": "🎯 Охотничье чутьё помогает находить редкие следы.",
        "geologist": "⛏ Геологический опыт помогает замечать полезные залежи.",
    }.get(result.get("kind"), "")

    rare_text = "⭐ Редкий ресурс!" if result.get("rare") else ""
    bag_text = f"🎒 Заполнено сумки: {result['bag_total_after']}/{result['bag_capacity']}"

    text_parts = [
        f"🧺 Сбор ресурсов — {result['location_title']}",
        "",
        f"Ты нашёл: {result['name']} x{result.get('amount', 1)}",
    ]

    if rare_text:
        text_parts.append(rare_text)

    if kind_text:
        text_parts.append(kind_text)

    text_parts.append(bag_text)
    text_parts.append("")
    text_parts.append("Можно продолжать исследование или собрать ещё ресурсов.")

    if reward_parts:
        text_parts.append("")
        text_parts.extend(reward_parts)

    await message.answer(
        "\n".join(text_parts),
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
    )
