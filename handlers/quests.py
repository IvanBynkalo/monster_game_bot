"""
handlers/quests.py

Единый экран квестов с inline-пагинацией.
Каждый квест показывается отдельно, переключение стрелками ◀️ / ▶️.
"""

from __future__ import annotations

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

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


# ── Сборка всех квестов в плоский список карточек ─────────────────────────────

def _collect_all_quest_cards(user_id: int, location_slug: str) -> list[dict]:
    cards: list[dict] = []

    # 1. Основные (starter) квесты
    try:
        starter_quests = get_active_player_quests(user_id)
        for quest in (starter_quests or {}).values():
            progress = min(int(quest.get("progress", 0)), int(quest.get("target_value", 0) or 0))
            target = int(quest.get("target_value", 0) or 0)
            done = progress >= target if target > 0 else False
            bar_pct = int(progress / max(1, target) * 10)
            bar = "█" * bar_pct + "░" * (10 - bar_pct)
            body_lines = [
                quest.get("description", "Описание отсутствует."),
                "",
                f"Прогресс: [{bar}] {progress}/{target}",
                f"💰 {quest.get('reward_gold', 0)} золота   ✨ {quest.get('reward_exp', 0)} опыта",
                f"Статус: {'✅ Выполнено' if done else '🕒 В процессе'}",
            ]
            cards.append({
                "category": "📜 Основное задание",
                "title": quest.get("title", "Без названия"),
                "body": "\n".join(body_lines),
                "status": "✅" if done else "🕒",
            })
    except Exception:
        pass

    # 2. Сюжетный квест
    try:
        story = get_current_story_quest(user_id)
        if story:
            req = story.get("requirements", {})
            req_parts = []
            if req.get("location_slug"):
                req_parts.append(f"Локация: {req['location_slug']}")
            if req.get("explore_count"):
                req_parts.append(f"Исследовать клеток: {req['explore_count']}")
            if req.get("win_count"):
                req_parts.append(f"Побед в бою: {req['win_count']}")
            body_lines = [story.get("description", "Описание отсутствует."), ""]
            if req_parts:
                body_lines.append("🎯 Цель:")
                body_lines.extend(f"  • {p}" for p in req_parts)
            else:
                body_lines.append("🎯 Следуй по сюжету")
            cards.append({
                "category": "🧾 Сюжет",
                "title": story.get("title", "Сюжетный этап"),
                "body": "\n".join(body_lines),
                "status": "🧾",
            })
    except Exception:
        pass

    # 3. Гильдейские поручения
    GUILD_LABELS = {
        "hunter":    "🎯 Гильдия ловцов",
        "gatherer":  "🌿 Гильдия собирателей",
        "geologist": "⛏ Гильдия геологов",
        "alchemist": "⚗ Гильдия алхимиков",
    }
    quest_desc_map: dict = {}
    try:
        from game.guild_quests import GUILD_QUEST_POOL, WEEKLY_GUILD_QUESTS
        for guild, pool in GUILD_QUEST_POOL.items():
            for q in pool:
                quest_desc_map[q["id"]] = q.get("desc", "")
        for guild, wq in WEEKLY_GUILD_QUESTS.items():
            quest_desc_map[wq["id"]] = wq.get("desc", "")
    except Exception:
        pass

    try:
        guild_quests_raw = get_player_guild_quests(user_id)
        for quest in (guild_quests_raw or {}).values():
            progress = int(quest.get("progress", 0) or 0)
            target = int(quest.get("count", 0) or 0)
            pct = int(progress / max(1, target) * 10)
            bar = "█" * pct + "░" * (10 - pct)
            qid = quest.get("quest_id", "")
            desc = quest_desc_map.get(qid, "")
            is_weekly = qid.startswith("wh_")
            gk = quest.get("guild_key", "")
            guild_label = GUILD_LABELS.get(gk, "🏛 Гильдия")

            if quest.get("completed"):
                status_icon = "✅"
                status_line = "✅ Выполнено — сдай в гильдии!"
            else:
                status_icon = "🌟" if is_weekly else "🕒"
                status_line = f"[{bar}] {progress}/{target}"

            body_lines = []
            if desc:
                body_lines += [f"📋 {desc}", ""]
            body_lines += [
                f"Прогресс: {status_line}",
                f"💰 {quest.get('reward_gold', 0)} золота   ✨ {quest.get('reward_exp', 0)} опыта",
            ]
            if is_weekly:
                body_lines.append("🌟 Еженедельное поручение")

            title = ("🌟 " if is_weekly else "") + quest.get("title", "Поручение")
            cards.append({
                "category": guild_label,
                "title": title,
                "body": "\n".join(body_lines),
                "status": status_icon,
            })
    except Exception:
        pass

    # 4. Квесты охоты
    try:
        from game.hunting_quests import get_active_hunting_quests
        for q in (get_active_hunting_quests(user_id) or []):
            prog = q.get("progress", 0)
            total = q.get("count", 1)
            pct = int(prog / max(1, total) * 10)
            bar = "█" * pct + "░" * (10 - pct)
            target_name = q.get("target", "?")
            if prog >= total:
                status_icon, status_line = "✅", "✅ Выполнено — сдай в гильдии охотников"
            else:
                status_icon, status_line = "🏹", f"[{bar}] {prog}/{total} — цель: {target_name}"
            cards.append({
                "category": "🏹 Квест охоты",
                "title": q.get("title", "Охота"),
                "body": f"Прогресс: {status_line}",
                "status": status_icon,
            })
    except Exception:
        pass

    # 5. Ежедневные задания
    try:
        if get_today_tasks(user_id):
            cards.append({
                "category": "📅 Ежедневные задания",
                "title": "Задания на сегодня",
                "body": get_daily_panel(user_id),
                "status": "📅",
            })
    except Exception:
        pass

    # 6. Недельная цель региона
    try:
        weekly = get_active_weekly_quest(user_id, location_slug)
        if weekly:
            cards.append({
                "category": "🎯 Недельная цель региона",
                "title": weekly.get("title", "Недельная цель"),
                "body": render_weekly_quest(weekly),
                "status": "🎯",
            })
    except Exception:
        pass

    return cards


# ── Рендер одной карточки ─────────────────────────────────────────────────────

def _render_quest_card(card: dict, index: int, total: int) -> str:
    return (
        f"{card['category']}\n"
        f"{'─' * 30}\n"
        f"{card['status']}  {card['title']}\n"
        f"\n"
        f"{card['body']}\n"
        f"\n"
        f"{'─' * 30}\n"
        f"Задание {index + 1} из {total}"
    )


def _empty_quests_text() -> str:
    return (
        "📜 Активных заданий нет\n\n"
        "Возьми поручение в гильдии или у торговцев.\n"
        "Квесты охоты появляются автоматически после побед над зверями."
    )


# ── Inline-клавиатура пагинации ───────────────────────────────────────────────

def _quest_nav_keyboard(index: int, total: int) -> InlineKeyboardMarkup:
    if total <= 1:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"1 / {total}", callback_data="quests:noop")
        ]])
    prev_idx = (index - 1) % total
    next_idx = (index + 1) % total
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data=f"quests:page:{prev_idx}"),
        InlineKeyboardButton(text=f"{index + 1} / {total}", callback_data="quests:noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"quests:page:{next_idx}"),
    ]])


# ── Хэндлеры ─────────────────────────────────────────────────────────────────

async def quests_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    set_ui_screen(message.from_user.id, "quests")
    cards = _collect_all_quest_cards(message.from_user.id, player.location_slug)

    if not cards:
        await message.answer(
            _empty_quests_text(),
            reply_markup=_main_menu_for(player, message.from_user.id),
        )
        return

    # Reply-клавиатура основного меню
    await message.answer(
        "📜 Задания",
        reply_markup=_main_menu_for(player, message.from_user.id),
    )
    # Первая карточка с inline-пагинацией
    await message.answer(
        _render_quest_card(cards[0], 0, len(cards)),
        reply_markup=_quest_nav_keyboard(0, len(cards)),
    )


async def quests_page_callback(callback: CallbackQuery):
    """Переключение страниц ◀️ / ▶️."""
    if callback.data == "quests:noop":
        await callback.answer()
        return

    await callback.answer()
    parts = callback.data.split(":")
    if len(parts) < 3:
        return

    try:
        index = int(parts[2])
    except ValueError:
        return

    player = get_player(callback.from_user.id)
    if not player:
        return

    cards = _collect_all_quest_cards(callback.from_user.id, player.location_slug)
    if not cards:
        try:
            await callback.message.edit_text(_empty_quests_text())
        except Exception:
            pass
        return

    index = max(0, min(index, len(cards) - 1))
    try:
        await callback.message.edit_text(
            _render_quest_card(cards[index], index, len(cards)),
            reply_markup=_quest_nav_keyboard(index, len(cards)),
        )
    except Exception:
        pass
