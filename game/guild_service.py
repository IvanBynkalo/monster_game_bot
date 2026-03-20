"""
Система игровых гильдий (рекомендация #10).
Игроки создают и вступают в гильдии, проводят совместные рейды.
"""
import random
from database.repositories import (
    create_guild, get_guild_by_id, get_player_guild, join_guild, leave_guild,
    get_guild_members, add_guild_treasury, list_guilds, get_player, get_active_monster,
    add_player_gold, add_player_experience, track, get_damage_multiplier,
)

MAX_GUILD_MEMBERS = 20
GUILD_CREATION_COST = 200  # золото

GUILD_BOSSES = [
    {"slug":"rage_titan",    "name":"🔥 Титан Ярости",     "hp":500, "attack":18, "reward_gold":150, "reward_exp":60},
    {"slug":"shadow_lord",   "name":"🌑 Повелитель теней", "hp":600, "attack":20, "reward_gold":180, "reward_exp":75},
    {"slug":"storm_colossus","name":"⚡ Колосс бурь",      "hp":700, "attack":22, "reward_gold":200, "reward_exp":90},
]


def try_create_guild(telegram_id: int, name: str, description: str = "") -> tuple[dict | None, str]:
    p = get_player(telegram_id)
    if not p:
        return None, "Игрок не найден."
    if p.level < 5:
        return None, f"Для создания гильдии нужен 5-й уровень. У тебя: {p.level}."
    if p.gold < GUILD_CREATION_COST:
        return None, f"Нужно {GUILD_CREATION_COST} золота. У тебя: {p.gold}."
    if get_player_guild(telegram_id):
        return None, "Ты уже состоишь в гильдии. Сначала выйди из неё."
    if not name or len(name) > 30:
        return None, "Название гильдии должно быть от 1 до 30 символов."

    from database.repositories import _update_player_field
    _update_player_field(telegram_id, gold=p.gold - GUILD_CREATION_COST)

    guild = create_guild(name=name, leader_id=telegram_id, description=description)
    if not guild:
        return None, "Гильдия с таким именем уже существует."
    track(telegram_id, "guild_created", {"guild_id": guild["id"]})
    return guild, ""


def try_join_guild(telegram_id: int, guild_id: int) -> tuple[bool, str]:
    if get_player_guild(telegram_id):
        return False, "Ты уже состоишь в гильдии."
    guild = get_guild_by_id(guild_id)
    if not guild:
        return False, "Гильдия не найдена."
    members = get_guild_members(guild_id)
    if len(members) >= MAX_GUILD_MEMBERS:
        return False, f"Гильдия полна ({MAX_GUILD_MEMBERS} участников)."
    ok = join_guild(guild_id, telegram_id)
    if ok:
        track(telegram_id, "guild_joined", {"guild_id": guild_id})
    return ok, "" if ok else "Не удалось вступить в гильдию."


def try_leave_guild(telegram_id: int) -> tuple[bool, str]:
    guild = get_player_guild(telegram_id)
    if not guild:
        return False, "Ты не состоишь ни в одной гильдии."
    if guild["leader_id"] == telegram_id:
        return False, "Лидер не может покинуть гильдию. Сначала передай лидерство."
    leave_guild(telegram_id)
    return True, ""


def simulate_guild_raid(guild_id: int, boss_slug: str) -> dict:
    """Коллективный рейд: все участники атакуют босса совместно."""
    boss = next((b for b in GUILD_BOSSES if b["slug"] == boss_slug), None)
    if not boss:
        return {"error": "Босс не найден."}

    members = get_guild_members(guild_id)
    if not members:
        return {"error": "В гильдии нет участников."}

    boss_hp  = boss["hp"]
    log      = []
    total_dmg = 0
    participants = []

    for m in members:
        monster = get_active_monster(m["telegram_id"])
        if not monster:
            continue
        player = get_player(m["telegram_id"])
        if not player:
            continue

        atk      = monster.get("attack", 3) + player.strength
        mult     = get_damage_multiplier(monster.get("monster_type"), "void")
        dmg      = max(1, int(atk * mult * random.uniform(0.9, 1.1)))
        total_dmg += dmg
        participants.append({"id": m["telegram_id"], "name": player.name, "dmg": dmg})
        log.append(f"⚔️ {player.name} ({monster['name']}): {dmg} урона")

    boss_hp -= total_dmg
    victory  = boss_hp <= 0

    reward_gold = boss["reward_gold"] if victory else boss["reward_gold"] // 4
    reward_exp  = boss["reward_exp"]  if victory else boss["reward_exp"] // 4
    split_gold  = max(1, reward_gold // max(1, len(participants))) if participants else 0
    split_exp   = max(1, reward_exp  // max(1, len(participants))) if participants else 0

    for p_info in participants:
        add_player_gold(p_info["id"], split_gold)
        add_player_experience(p_info["id"], split_exp)

    if victory:
        add_guild_treasury(guild_id, reward_gold // 5)  # 20% в казну

    return {
        "boss_name":    boss["name"],
        "victory":      victory,
        "total_damage": total_dmg,
        "boss_hp_left": max(0, boss_hp),
        "participants": len(participants),
        "split_gold":   split_gold,
        "split_exp":    split_exp,
        "log":          log,
    }


def render_guild_info(guild: dict, members: list[dict]) -> str:
    lines = [
        f"🏰 {guild['name']}",
        f"Участников: {len(members)}/{MAX_GUILD_MEMBERS}",
        f"Казна: {guild.get('treasury_gold',0)} золота",
    ]
    if guild.get("description"):
        lines.append(f"«{guild['description']}»")
    lines.append("\nУчастники:")
    for m in members[:10]:
        role_icon = "👑" if m["role"] == "leader" else "⚔️"
        lines.append(f"  {role_icon} {m['name']} (ур. {m['level']})")
    if len(members) > 10:
        lines.append(f"  ... и ещё {len(members)-10}")
    return "\n".join(lines)


def render_guild_list(guilds: list[dict]) -> str:
    if not guilds:
        return "Гильдий пока нет. Создай первую!"
    lines = ["🏰 Список гильдий\n"]
    for g in guilds:
        lines.append(f"• {g['name']} — {g.get('member_count',0)} чел. | Казна: {g.get('treasury_gold',0)}з")
    return "\n".join(lines)


# ── Групповые рейды на редких зверей ──────────────────────────────────────────

RARE_WILDLIFE_BOSSES = [
    {"slug": "forest_giant",   "name": "🌲 Лесной великан",       "location": "dark_forest",
     "hp": 180, "attack": 18, "reward_gold": 200, "reward_exp": 60,
     "trophy": "forest_giant_claw", "min_exploration": 50},
    {"slug": "golden_eagle",   "name": "🦅 Золотой орёл",         "location": "emerald_fields",
     "hp": 140, "attack": 15, "reward_gold": 180, "reward_exp": 55,
     "trophy": "golden_eagle_feather", "min_exploration": 40},
    {"slug": "mountain_lion",  "name": "🦁 Горный лев",           "location": "stone_hills",
     "hp": 200, "attack": 20, "reward_gold": 220, "reward_exp": 65,
     "trophy": "mountain_lion_fang", "min_exploration": 60},
    {"slug": "magma_boar",     "name": "🔥 Магматический кабан",  "location": "volcano_wrath",
     "hp": 240, "attack": 22, "reward_gold": 260, "reward_exp": 75,
     "trophy": "magma_tusk", "min_exploration": 70},
    {"slug": "swamp_croc",     "name": "🐊 Болотный крокодил",    "location": "shadow_swamp",
     "hp": 220, "attack": 20, "reward_gold": 240, "reward_exp": 70,
     "trophy": "swamp_croc_scale", "min_exploration": 55},
]


def simulate_wildlife_raid(guild_id: int, boss_slug: str) -> dict:
    """Групповой рейд на редкого зверя. Логика аналогична рейду на гильдейского босса."""
    import random
    from database.repositories import get_guild_members, get_player, add_player_gold, add_player_experience, add_resource
    from game.exploration_service import get_exploration

    boss = next((b for b in RARE_WILDLIFE_BOSSES if b["slug"] == boss_slug), None)
    if not boss:
        return {"error": f"Зверь '{boss_slug}' не найден."}

    members = get_guild_members(guild_id)
    if not members:
        return {"error": "В гильдии нет участников."}

    # Фильтруем участников по уровню исследования локации
    eligible = []
    for m in members:
        p = get_player(m["telegram_id"])
        if p:
            expl = get_exploration(m["telegram_id"], boss["location"])
            if expl >= boss["min_exploration"]:
                eligible.append(p)

    if not eligible:
        return {"error": f"Нужно исследовать {boss['location']} минимум на {boss['min_exploration']}% чтобы участвовать."}

    # Симуляция боя
    boss_hp    = boss["hp"]
    total_dmg  = 0
    log        = []
    for p in eligible:
        from database.repositories import get_active_monster
        m_obj = get_active_monster(p.telegram_id)
        atk   = (m_obj.get("attack", 5) if m_obj else 5) + p.strength
        dmg   = random.randint(max(3, atk - 3), atk + 5)
        boss_hp  -= dmg
        total_dmg += dmg
        log.append(f"⚔️ {p.name}: -{dmg}")

    victory      = boss_hp <= 0
    split_gold   = (boss["reward_gold"] * len(eligible) // max(1, len(eligible))) if victory else boss["reward_gold"] // 4
    split_exp    = boss["reward_exp"] if victory else boss["reward_exp"] // 3
    trophy_winner = None

    if victory:
        winner = random.choice(eligible)
        trophy_winner = winner.telegram_id
        for p in eligible:
            add_player_gold(p.telegram_id, split_gold)
            add_player_experience(p.telegram_id, split_exp)
        # Трофей одному случайному участнику
        add_resource(trophy_winner, boss["trophy"], 1)
    else:
        for p in eligible:
            add_player_gold(p.telegram_id, split_gold)

    return {
        "victory":       victory,
        "boss_name":     boss["name"],
        "boss_hp_left":  max(0, boss_hp),
        "total_damage":  total_dmg,
        "participants":  len(eligible),
        "split_gold":    split_gold,
        "split_exp":     split_exp,
        "trophy_winner": trophy_winner,
        "trophy_item":   boss["trophy"],
        "log":           log,
    }
