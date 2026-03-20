"""
PvP-система (рекомендация #8).
Асинхронные вызовы: challenger вызывает target, оба получают уведомление,
бой рассчитывается автоматически на стороне сервера.
"""
import random
from database.repositories import (
    get_player, get_active_monster, get_pvp_stats,
    create_pvp_challenge, get_pending_challenge, resolve_pvp_challenge,
    record_pvp_result, add_player_gold, add_player_experience, track,
    get_damage_multiplier,
)

MEDALS = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]


def calculate_pvp_battle(challenger_id: int, target_id: int) -> dict:
    """
    Симулирует PvP-бой между двумя игроками.
    Возвращает словарь с результатами и логом боя.
    """
    c_player  = get_player(challenger_id)
    t_player  = get_player(target_id)
    c_monster = get_active_monster(challenger_id)
    t_monster = get_active_monster(target_id)

    if not c_player or not t_player or not c_monster or not t_monster:
        return {"error": "Один из участников не имеет активного монстра."}

    c_hp  = c_monster.get("current_hp", c_monster.get("max_hp", 10))
    t_hp  = t_monster.get("current_hp", t_monster.get("max_hp", 10))
    log   = []
    round_n = 0

    while c_hp > 0 and t_hp > 0 and round_n < 20:
        round_n += 1

        # Удар чаллнеджера по цели
        base_c = c_monster.get("attack", 3) + c_player.strength
        mult_c = get_damage_multiplier(
            c_monster.get("monster_type"), t_monster.get("monster_type")
        )
        dmg_c  = max(1, int(base_c * mult_c * random.uniform(0.85, 1.15)))
        t_hp  -= dmg_c
        log.append(f"🗡 {c_monster['name']} наносит {dmg_c} урона {t_monster['name']}")

        if t_hp <= 0:
            break

        # Удар цели по чаллнеджеру
        base_t = t_monster.get("attack", 3) + t_player.strength
        mult_t = get_damage_multiplier(
            t_monster.get("monster_type"), c_monster.get("monster_type")
        )
        dmg_t  = max(1, int(base_t * mult_t * random.uniform(0.85, 1.15)))
        c_hp  -= dmg_t
        log.append(f"🗡 {t_monster['name']} наносит {dmg_t} урона {c_monster['name']}")

    winner_id = challenger_id if c_hp > t_hp else target_id
    loser_id  = target_id if winner_id == challenger_id else challenger_id

    # Записываем результат
    record_pvp_result(winner_id, loser_id)

    # Награды
    gold_reward = 40 + random.randint(0, 30)
    exp_reward  = 20
    add_player_gold(winner_id, gold_reward)
    add_player_experience(winner_id, exp_reward)

    # Аналитика
    track(challenger_id, "pvp_battle", {"vs": target_id, "winner": winner_id})

    winner_name = c_player.name if winner_id == challenger_id else t_player.name
    loser_name  = t_player.name if winner_id == challenger_id else c_player.name

    return {
        "winner_id":    winner_id,
        "loser_id":     loser_id,
        "winner_name":  winner_name,
        "loser_name":   loser_name,
        "gold_reward":  gold_reward,
        "exp_reward":   exp_reward,
        "log":          log[-6:],  # последние 6 строк лога
        "rounds":       round_n,
    }


def render_pvp_result(result: dict, viewer_id: int) -> str:
    if "error" in result:
        return f"❌ {result['error']}"
    is_winner = viewer_id == result["winner_id"]
    lines = [
        "⚔️ Результаты PvP-боя",
        f"Раундов: {result['rounds']}",
        "",
    ]
    lines.extend(result["log"])
    lines.append("")
    if is_winner:
        lines.append(f"🏆 Ты победил! +{result['gold_reward']} золота, +{result['exp_reward']} опыта")
    else:
        lines.append("💀 Ты проиграл. Тренируйся и попробуй снова!")
    return "\n".join(lines)


def render_pvp_stats(telegram_id: int) -> str:
    stats = get_pvp_stats(telegram_id)
    total = stats["wins"] + stats["losses"]
    wr    = int(stats["wins"] / total * 100) if total > 0 else 0
    return (
        f"⚔️ PvP-статистика\n"
        f"Рейтинг: {stats['rating']}\n"
        f"Победы: {stats['wins']} | Поражения: {stats['losses']}\n"
        f"Процент побед: {wr}%"
    )


def render_pvp_leaderboard(rows: list[dict]) -> str:
    if not rows:
        return "Таблица PvP пуста."
    lines = ["🏆 Топ PvP-бойцов\n"]
    for i, r in enumerate(rows):
        medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
        lines.append(f"{medal} {r['name']} — рейтинг {r['rating']} ({r['wins']}W/{r['losses']}L)")
    return "\n".join(lines)
