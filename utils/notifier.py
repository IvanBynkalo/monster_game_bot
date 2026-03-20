"""
Пуш-уведомления игрокам (рекомендация #19).
Отправляет асинхронные сообщения об игровых событиях.
"""
import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

logger = logging.getLogger(__name__)

# Глобальный bot instance — устанавливается при старте в bot.py
_bot: Bot | None = None


def set_bot(bot: Bot):
    global _bot
    _bot = bot


async def notify(user_id: int, text: str) -> bool:
    """Отправляет уведомление игроку. Возвращает True при успехе."""
    if not _bot:
        return False
    try:
        await _bot.send_message(user_id, text)
        return True
    except TelegramForbiddenError:
        # Бот заблокирован пользователем — молча игнорируем
        return False
    except TelegramBadRequest as e:
        logger.warning("notify BadRequest user=%s: %s", user_id, e)
        return False
    except Exception as e:
        logger.error("notify error user=%s: %s", user_id, e)
        return False


def notify_async(user_id: int, text: str):
    """Fire-and-forget уведомление. Использовать из sync-контекста."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(notify(user_id, text))
        else:
            loop.run_until_complete(notify(user_id, text))
    except Exception as e:
        logger.debug("notify_async error: %s", e)


# ── Шаблоны уведомлений ──────────────────────────────────────────────────────

async def notify_mutation_stage(user_id: int, monster_name: str, stage: int, combo: str | None = None):
    stage_labels = {2: "🌀 Искажение", 3: "🔮 Мутация", 4: "💀 Критическая форма"}
    if stage not in stage_labels:
        return
    text = f"{stage_labels[stage]}!\n{monster_name} достиг новой стадии заражения."
    if combo:
        text += f"\n⚡ Комбо-мутация: {combo}"
    await notify(user_id, text)


async def notify_evolution(user_id: int, old_name: str, new_name: str):
    await notify(user_id, f"🦋 Эволюция!\n{old_name} превратился в {new_name}!")


async def notify_pvp_challenge(user_id: int, challenger_name: str, challenge_id: int):
    await notify(
        user_id,
        f"⚔️ {challenger_name} вызывает тебя на PvP-бой!\n"
        f"Отправь /accept_pvp {challenge_id} чтобы принять\n"
        f"или /decline_pvp {challenge_id} чтобы отказаться."
    )


async def notify_pvp_result(user_id: int, result: dict, is_winner: bool):
    if is_winner:
        text = (f"🏆 Победа в PvP!\n"
                f"Ты победил {result['loser_name']}!\n"
                f"+{result['gold_reward']} золота, +{result['exp_reward']} опыта")
    else:
        text = f"💀 Поражение в PvP.\nТебя победил {result['winner_name']}. Тренируйся!"
    await notify(user_id, text)


async def notify_guild_raid_result(user_id: int, result: dict):
    if result.get("error"):
        return
    if result["victory"]:
        text = (f"🏰 Рейд гильдии: ПОБЕДА!\n"
                f"Босс {result['boss_name']} повержен!\n"
                f"+{result['split_gold']} золота, +{result['split_exp']} опыта")
    else:
        text = (f"🏰 Рейд гильдии: провал.\n"
                f"Босс {result['boss_name']} устоял.\n"
                f"Нанесено урона: {result['total_damage']}")
    await notify(user_id, text)


async def notify_daily_streak(user_id: int, streak: int, reward: int):
    await notify(
        user_id,
        f"🌅 День {streak} подряд!\n"
        f"🔥 {'🔥' * min(streak, 7)}\n"
        f"+{reward} золота за верность!"
    )


async def notify_level_up(user_id: int, new_level: int):
    await notify(user_id, f"⬆️ Уровень {new_level}!\nПолучено 2 очка характеристик.")


async def notify_season_task_complete(user_id: int, task_desc: str, gold: int):
    await notify(user_id, f"🎫 Сезонное задание выполнено!\n{task_desc}\n+{gold} золота")
