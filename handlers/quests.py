"""
handlers/quests.py

Единый экран квестов.

Задачи файла:
- показать активные сюжетные / стартовые / гильдейские задания в одном месте;
- встроить экран в новую схему ui_screen;
- не ломать текущую маршрутизацию bot.py;
- оставить reply-клавиатуру корневого меню, а детали показать одним читаемым экраном.
"""

from __future__ import annotations

from aiogram.types import Message

from database.repositories import (
    get_active_player_quests,
    get_current_story_quest,
    get_player,
    get_player_guild_quests,
    get_today_tasks,
    set_ui_screen,
)
from game.daily_service import get_daily_panel
from game.weekly_quest_service import get_active_weekly_quest, render_weekly_quest
from keyboards.main_menu import main_menu


def _is_traveling_now(user_id: int) -> bool:
    try:
        from game.travel_service import is_traveling as _is_traveling
        return _is_traveling(user_id)
    except Exception:
        return False


def _main_menu_for(player, user_id: int):
    return main_menu(
        player.location_slug,
        getattr(player, "current_district_slug", None),
        is_traveling=_is_traveling_now(user_id),
        telegram_id=user_id,
    )


def _render_starter_quests(quests: dict) -> list[str]:
    lines: list[str] = ["📜 Основные задания", ""]

    if not quests:
        lines.append("Сейчас активных основных заданий нет.")
        return lines

    for quest in quests.values():
        progress = min(int(quest.get("progress", 0)), int(quest.get("target_value", 0) or 0))
        target = int(quest.get("target_value", 0) or 0)
        done = progress >= target if target > 0 else False
        status = "✅ Готово" if done else "🕒 В процессе"

        lines.extend(
            [
                f"• {quest.get('title', 'Без названия')}",
                f"  {quest.get('description', 'Описание отсутствует.')}",
                f"  Прогресс: {progress}/{target}",
                f"  Награда: 💰 {quest.get('reward_gold', 0)} | ✨ {quest.get('reward_exp', 0)}",
                f"  Статус: {status}",
                "",
            ]
        )

    return lines


def _render_story_quest(user_id: int) -> list[str]:
    lines: list[str] = ["🧾 Сюжет", ""]

    quest = get_current_story_quest(user_id)
    if not quest:
        lines.append("Текущих сюжетных задач нет.")
        return lines

    req = quest.get("requirements", {})
    req_parts: list[str] = []
    if req.get("location_slug"):
        req_parts.append(f"локация: {req['location_slug']}")
    if req.get("explore_count"):
        req_parts.append(f"исследовать: {req['explore_count']}")
    if req.get("win_count"):
        req_parts.append(f"побед: {req['win_count']}")

    lines.extend(
        [
            f"• {quest.get('title', 'Сюжетный этап')}",
            quest.get("description", "Описание отсутствует."),
            f"Цель: {', '.join(req_parts) if req_parts else 'следуй сюжету'}",
        ]
    )
    return lines


def _render_guild_quests(user_id: int) -> list[str]:
    lines: list[str] = ["🏛 Гильдейские поручения", ""]

    quests = get_player_guild_quests(user_id)
    active = [q for q in quests.values() if not q.get("completed")]

    if not active:
        lines.append("Активных гильдейских поручений нет.")
        return lines

    guild_labels = {
        "hunter": "🎯 Ловцы",
        "gatherer": "🌿 Собиратели",
        "geologist": "⛏ Геологи",
        "alchemist": "⚗ Алхимики",
    }

    for quest in sorted(active, key=lambda x: (x.get("guild_key") or "", x.get("title") or "")):
        progress = int(quest.get("progress", 0) or 0)
        target = int(quest.get("count", 0) or 0)
        guild_name = guild_labels.get(quest.get("guild_key"), quest.get("guild_key") or "Гильдия")
        lines.extend(
            [
                f"• {quest.get('title', 'Поручение')} — {guild_name}",
                f"  Прогресс: {progress}/{target}",
                f"  Награда: 💰 {quest.get('reward_gold', 0)} | ✨ {quest.get('reward_exp', 0)}",
                "",
            ]
        )

    return lines


def _render_hunting_quests(user_id: int) -> list[str]:
    lines: list[str] = ["🏹 Квесты охоты", ""]
    try:
        from game.hunting_quests import get_active_hunting_quests
        import time
        active = get_active_hunting_quests(user_id)
        if not active:
            lines.append("Нет активных квестов охоты.")
            lines.append("Выдаются автоматически при победе над зверями.")
            return lines
        for q in active:
            prog = q.get("progress", 0)
            total = q.get("count", 1)
            pct = int(prog / max(1, total) * 10)
            bar = "█" * pct + "░" * (10 - pct)
            target_name = q.get("target", "?")
            if prog >= total:
                status = "✅ Выполнено! Сдай в гильдии."
            else:
                status = f"[{bar}] {prog}/{total} — цель: {target_name}"
            lines.append(f"• {q['title']}: {status}")
    except Exception:
        lines.append("Информация о квестах охоты недоступна.")
    return lines
    lines: list[str] = ["📅 Сегодня", ""]

    try:
        tasks = get_today_tasks(user_id)
    except Exception:
        tasks = []

    if not tasks:
        lines.append("Сегодняшние задания пока недоступны.")
        return lines

    # daily_service уже красиво рендерит блок — используем его целиком
    lines.append(get_daily_panel(user_id))
    return lines


def _render_weekly_task(user_id: int, location_slug: str) -> list[str]:
    lines: list[str] = ["🎯 Недельная цель региона", ""]

    try:
        quest = get_active_weekly_quest(user_id, location_slug)
    except Exception:
        quest = None

    if not quest:
        lines.append("Для этой локации сейчас нет активного недельного задания.")
        return lines

    lines.append(render_weekly_quest(quest))
    return lines


def _render_quests_screen(user_id: int, location_slug: str) -> str:
    sections: list[list[str]] = [
        _render_starter_quests(get_active_player_quests(user_id)),
        _render_story_quest(user_id),
        _render_guild_quests(user_id),
        _render_hunting_quests(user_id),
        _render_today_tasks(user_id),
        _render_weekly_task(user_id, location_slug),
    ]

    flat: list[str] = []
    for index, section in enumerate(sections):
        if index > 0:
            flat.append("──────────")
        flat.extend(section)

    return "\n".join(flat).strip()


async def quests_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    set_ui_screen(message.from_user.id, "quests")

    await message.answer(
        _render_quests_screen(message.from_user.id, player.location_slug),
        reply_markup=_main_menu_for(player, message.from_user.id),
    )
