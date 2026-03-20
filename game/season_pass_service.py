"""
Сезонный пасс — Battle Pass механика (рекомендация #15).
Бесплатный и премиум треки с нарастающими наградами.
"""
from database.repositories import (
    get_player, get_season_tasks, progress_season_tasks as _progress,
    add_player_gold, add_player_experience, track, get_today_tasks,
)

SEASON_NUMBER = 1
SEASON_NAME   = "Сезон 1: Пробуждение Эмоций"
SEASON_PASS_STARS_COST = 300  # Stars (Telegram)


def get_season_panel(telegram_id: int) -> str:
    p     = get_player(telegram_id)
    tasks = get_season_tasks(telegram_id)

    has_pass = bool(p and p.season_pass_active)
    lines = [
        f"🎫 {SEASON_NAME}\n",
        f"Пасс: {'✅ Активен' if has_pass else '❌ Не активен'} | "
        f"Стоимость: {SEASON_PASS_STARS_COST} ⭐\n",
        "Задания сезона:",
    ]

    for t in tasks:
        check   = "✅" if t["completed"] else f"{t['progress']}/{t['target']}"
        free_r  = t["reward_gold"]
        prem_r  = t.get("premium_reward", free_r * 2)
        lock    = "" if has_pass else " 🔒"
        lines.append(
            f"{'✔' if t['completed'] else '◻'} {t['description']}"
            f" [{check}]"
        )
        lines.append(f"   Бесплатно: {free_r}з | Премиум{lock}: {prem_r}з")

    completed = sum(1 for t in tasks if t["completed"])
    lines.append(f"\nВыполнено: {completed}/{len(tasks)}")

    if not has_pass:
        lines.append(f"\nПремиум-пасс: /buy_season_pass ({SEASON_PASS_STARS_COST} ⭐)")

    return "\n".join(lines)


def progress_season(telegram_id: int, action_type: str, amount: int = 1) -> list[dict]:
    """Продвигает сезонные задания и выдаёт награды."""
    p         = get_player(telegram_id)
    has_pass  = bool(p and p.season_pass_active)
    completed = _progress(telegram_id, action_type, amount)

    rewards_given = []
    for t in completed:
        # Бесплатная награда — всегда
        add_player_gold(telegram_id, t["reward_gold"])
        add_player_experience(telegram_id, 15)

        # Премиум-награда — только при активном пасе
        if has_pass:
            prem = t.get("premium_reward", t["reward_gold"] * 2)
            add_player_gold(telegram_id, prem)

        track(telegram_id, "season_task_complete", {
            "task_id": t["task_id"],
            "has_pass": has_pass,
        })
        rewards_given.append(t)

    return rewards_given


def render_season_completions(completed: list[dict], has_pass: bool) -> str:
    if not completed:
        return ""
    lines = []
    for t in completed:
        free_r = t["reward_gold"]
        prem_r = t.get("premium_reward", free_r * 2) if has_pass else 0
        total  = free_r + prem_r
        lines.append(
            f"🎫 Сезонное задание: {t['description']}\n"
            f"   +{total}з"
            + (" (включая премиум-бонус)" if has_pass and prem_r else "")
        )
    return "\n".join(lines)
