from aiogram.types import Message
from database.repositories import (
    get_player, progress_extra_quests, progress_guild_quests,
    add_player_gold, add_player_experience,
)
from game.gather_service import gather_resource
from keyboards.main_menu import main_menu
from keyboards.location_menu import location_actions_inline
from game.dungeon_service import DUNGEONS
from utils.cooldown import cooldown_guard
from game.daily_service import progress_daily_tasks as _pdt_gather
from game.season_pass_service import progress_season as _ps_gather


PROFESSION_TITLES = {
    "gatherer": "🧺 Собиратель",
    "hunter": "🎯 Ловец",
    "geologist": "⛏ Геолог",
    "alchemist": "⚗ Алхимик",
    "merchant": "💼 Торговец",
}


def _render_profession_gain(gain: dict | None) -> str:
    if not gain:
        return ""

    title = PROFESSION_TITLES.get(gain["kind"], gain["kind"])
    if gain.get("is_max_level"):
        return f"\n{title}: максимальный уровень."

    text = f"\n{title}: +{gain['gained_exp']} опыта"
    if gain.get("leveled_up"):
        text += f"\n🎉 {title} повышен до {gain['level_after']} уровня!"
    else:
        text += f" ({gain['exp_after']}/{gain['exp_to_next']})"

    return text


async def gather_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if not await cooldown_guard(message, kind="gather", seconds=1.5):
        return

    result = gather_resource(player, player.location_slug)

    if not result:
        await message.answer("В этой области пока нечего собрать.")
        return
    if result.get("error"):
        await message.answer(result["error"], reply_markup=main_menu(player.location_slug))
        return

    extra = ""
    guild_completed = progress_guild_quests(message.from_user.id, "gather", result.get("amount", 1)) if not result.get("rare") else []
    if result.get("kind") == "geologist":
        guild_completed += progress_guild_quests(message.from_user.id, "geology", result.get("amount", 1))
    # Новая система гильдейских квестов
    try:
        _gq_done = _gq_progress(message.from_user.id, "gatherer", "gather", result.get("amount", 1))
        for _cq in _gq_done:
            guild_completed.append(_cq)
        if result.get("kind") == "geologist":
            _gq_done2 = _gq_progress(message.from_user.id, "geologist", "gather_resource_type",
                                      result.get("amount", 1), {"res_type": "stone"})
            for _cq in _gq_done2:
                guild_completed.append(_cq)
    except Exception:
        pass

    if result.get("rare"):
        completed = progress_extra_quests(message.from_user.id, "rare_gather", 1)
        if completed:
            reward_parts = []
            for quest in completed:
                add_player_gold(message.from_user.id, quest["reward_gold"])
                add_player_experience(message.from_user.id, quest["reward_exp"])
                reward_parts.append(
                    f"📜 Квест выполнен: {quest['title']}\n"
                    f"💰 Награда: +{quest['reward_gold']} золота\n"
                    f"✨ Награда: +{quest['reward_exp']} опыта"
                )
            extra = "\n\n" + "\n\n".join(reward_parts)

    if guild_completed:
        reward_parts = []
        for quest in guild_completed:
            add_player_gold(message.from_user.id, quest["reward_gold"])
            add_player_experience(message.from_user.id, quest["reward_exp"])
            reward_parts.append(
                f"📜 Квест выполнен: {quest['title']}\n"
                f"💰 Награда: +{quest['reward_gold']} золота\n"
                f"✨ Награда: +{quest['reward_exp']} опыта"
            )
        extra += ("\n\n" if extra else "") + "\n\n".join(reward_parts)

    rare_text = "\nРедкость: редкий ресурс!" if result.get("rare") else ""
    profession_text = _render_profession_gain(result.get("profession_gain"))

    # Показатель заполненности сумки
    from database.repositories import get_resources, get_player as _gp2
    _fresh = _gp2(message.from_user.id)
    _resources = get_resources(message.from_user.id)
    _total_items = sum(_resources.values())
    _cap = _fresh.bag_capacity if _fresh else 12
    _bag_pct = min(100, int(_total_items / _cap * 100))
    _bag_filled = _bag_pct // 10
    _bag_bar = "█" * _bag_filled + "░" * (10 - _bag_filled)
    _bag_text = f"\n🎒 Сумка: [{_bag_bar}] {_total_items}/{_cap}"

    await message.answer(
        f"🧺 Ты нашёл ресурс: {result['name']} x{result.get('amount', 1)}"
        f"{rare_text}{profession_text}{extra}{_bag_text}",
        reply_markup=main_menu(player.location_slug)
    )
    # Inline-меню после сбора
    try:
        from game.grid_exploration_service import is_dungeon_available
        _has_dng = player.location_slug in DUNGEONS and is_dungeon_available(message.from_user.id, player.location_slug)
    except Exception:
        _has_dng = False
    await message.answer(
        "Что делать:",
        reply_markup=location_actions_inline(player.location_slug, has_dungeon=_has_dng)
    )
