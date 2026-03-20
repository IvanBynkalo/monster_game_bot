"""
Ежедневные задания, streak-система и таблица лидеров (рекомендации #12, #13).
"""
from database.repositories import (
    get_today_tasks, progress_daily_tasks as _progress_daily,
    check_and_update_daily_streak, get_streak_reward,
    add_player_gold, get_leaderboard, get_pvp_leaderboard, track,
)

MEDALS = ["🥇","🥈","🥉","4.","5.","6.","7.","8.","9.","10."]


# ── Ежедневные задания ────────────────────────────────────────────────────────

def get_daily_panel(telegram_id: int) -> str:
    tasks = get_today_tasks(telegram_id)
    if not tasks:
        return "Ежедневных заданий нет."
    lines = ["📋 Ежедневные задания\n"]
    for t in tasks:
        check = "✅" if t["completed"] else "◻️"
        lines.append(f"{check} {t['description']}")
        lines.append(f"   Прогресс: {t['progress']}/{t['target']} | Награда: {t['reward_gold']}з")
    all_done = all(t["completed"] for t in tasks)
    if all_done:
        lines.append("\n🎉 Все задания выполнены! Возвращайся завтра.")
    return "\n".join(lines)


def progress_daily_tasks(telegram_id: int, action_type: str, amount: int = 1) -> list[dict]:
    completed = _progress_daily(telegram_id, action_type, amount)
    for t in completed:
        add_player_gold(telegram_id, t["reward_gold"])
        track(telegram_id, "daily_task_complete", {"task_id": t["task_id"]})
    return completed


def render_daily_completions(completed: list[dict]) -> str:
    if not completed:
        return ""
    lines = []
    for t in completed:
        lines.append(f"✅ Задание выполнено: {t['description']}\n   +{t['reward_gold']} золота")
    return "\n".join(lines)


# ── Streak ────────────────────────────────────────────────────────────────────

def handle_login_streak(telegram_id: int) -> str:
    """Вызывается при каждом /start. Возвращает строку с наградой или ''."""
    streak, is_new_day = check_and_update_daily_streak(telegram_id)
    if not is_new_day:
        return ""

    reward = get_streak_reward(streak)
    add_player_gold(telegram_id, reward)
    track(telegram_id, "daily_login", {"streak": streak, "reward": reward})

    streak_bar = "🔥" * min(streak, 7)
    lines = [
        f"🌅 Добро пожаловать! День {streak} подряд!",
        f"{streak_bar}",
        f"+{reward} золота за ежедневный вход",
    ]
    if streak % 7 == 0:
        lines.append("🎊 Серия 7 дней! Бонусная награда получена!")
    return "\n".join(lines)


# ── Таблица лидеров ───────────────────────────────────────────────────────────

def render_leaderboard(limit: int = 10) -> str:
    rows = get_leaderboard(limit)
    if not rows:
        return "Таблица лидеров пуста."
    lines = ["🏆 Топ игроков\n"]
    for i, r in enumerate(rows):
        medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
        lines.append(
            f"{medal} {r['name']} — ур. {r['level']} | "
            f"монстров: {r.get('monster_count',0)} | "
            f"золото: {r.get('gold',0)}"
        )
    return "\n".join(lines)


def render_pvp_leaderboard_text(limit: int = 10) -> str:
    rows = get_pvp_leaderboard(limit)
    if not rows:
        return "PvP-рейтинг пуст."
    lines = ["⚔️ PvP-рейтинг\n"]
    for i, r in enumerate(rows):
        medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
        lines.append(
            f"{medal} {r['name']} — рейтинг {r['rating']} "
            f"({r.get('wins',0)}W/{r.get('losses',0)}L)"
        )
    return "\n".join(lines)
