"""
skill_service.py — Активные навыки монстра в бою.

v3: Интегрирован с combat_skills.py и полной матрицей типов.
Каждый монстр получает навык на основе типа/эмоции через generate_monster_skills().
"""
import random
from game.type_service import get_damage_multiplier, EMOTION_COMBAT_MODIFIERS
from game.combat_skills import SKILLS_POOL, generate_monster_skills, get_skill_info

SKILL_LABELS = {
    "rage":        "Вспышка ярости",
    "fear":        "Покров тени",
    "instinct":    "Охотничья метка",
    "inspiration": "Импульс искры",
    "sadness":     "Теневой распад",
    "joy":         "Радостный порыв",
    "disgust":     "Ядовитое касание",
    "surprise":    "Хаотичный взрыв",
}


def get_active_skill(monster: dict):
    if not monster:
        return None
    return monster.get("infection_type") or monster.get("mood")


def get_active_skill_label(monster: dict) -> str:
    skill_key = get_active_skill(monster)
    return SKILL_LABELS.get(skill_key, "Навык")


def _apply_active_skill(encounter: dict, monster: dict, skill_id: str) -> dict:
    """Применяет конкретный скилл из пула к encounter."""
    skill = get_skill_info(skill_id)
    atk = monster.get("attack", 6)
    mtype = monster.get("monster_type")
    emotion = monster.get("mood")
    enemy_type = encounter.get("monster_type")

    mult, hint = get_damage_multiplier(mtype, enemy_type, emotion)
    power = skill.get("power", 1.0)
    rand_factor = random.uniform(0.9, 1.1)
    raw_dmg = random.randint(max(3, atk - 2), atk + 4)
    dmg = max(1, int(round(raw_dmg * power * mult * rand_factor)))

    encounter["hp"] -= dmg
    effect = skill.get("effect")

    # Применяем эффекты скилла
    effect_text = ""
    if effect == "heal_25pct":
        heal = max(1, int(monster.get("max_hp", monster.get("hp", 10)) * 0.25))
        monster["current_hp"] = min(monster.get("max_hp", 999), monster.get("current_hp", 0) + heal)
        effect_text = f"\n💚 {monster['name']} восстанавливает {heal} HP."
    elif effect == "regen_3":
        monster["regen_turns"] = 3
        effect_text = "\n🌿 Регенерация активирована на 3 хода."
    elif effect == "burn_2" or effect == "burn_3":
        turns = 3 if effect == "burn_3" else 2
        encounter["dot"] = {"type": "burn", "turns": turns, "value": max(1, atk // 4)}
        effect_text = f"\n🔥 Враг горит ({turns} хода)."
    elif effect == "poison_3":
        encounter["dot"] = {"type": "poison", "turns": 3, "value": max(1, atk // 5)}
        effect_text = f"\n☠️ Враг отравлен (3 хода)."
    elif effect == "decay_3":
        max_hp = encounter.get("max_hp", encounter["hp"] + dmg)
        decay_val = max(1, int(max_hp * 0.05))
        encounter["dot"] = {"type": "decay", "turns": 3, "value": decay_val}
        effect_text = "\n🖤 Враг разрушается (3 хода, 5% HP)."
    elif effect == "stun_chance":
        if random.random() < 0.4:
            encounter["skip_turn"] = True
            effect_text = "\n😵 Враг оглушён на 1 ход!"
    elif effect == "slow_1":
        encounter["counter_multiplier"] = max(0.0, encounter.get("counter_multiplier", 1.0) - 0.3)
        effect_text = "\n🐌 Враг замедлен."
    elif effect == "break_defense_2":
        encounter["defense_broken"] = True
        effect_text = "\n💥 Защита врага сломана на 2 хода."
    elif effect == "weaken_2":
        encounter["attack"] = max(1, int(encounter.get("attack", 5) * 0.8))
        effect_text = "\n⬇️ Атака врага снижена."
    elif effect == "no_heal_2":
        encounter["no_heal"] = 2
        effect_text = "\n🚫 Враг не может лечиться 2 хода."
    elif effect == "double_hit_25":
        if random.random() < 0.25:
            bonus_dmg = max(1, dmg // 2)
            encounter["hp"] -= bonus_dmg
            dmg += bonus_dmg
            effect_text = f"\n⚡ Двойной удар! +{bonus_dmg} урона."
    elif effect == "lifesteal":
        steal = max(1, dmg // 4)
        monster["current_hp"] = min(monster.get("max_hp", 999), monster.get("current_hp", 0) + steal)
        effect_text = f"\n🩸 Кража жизни: +{steal} HP."
    elif effect == "extra_action_25":
        if random.random() < 0.25:
            bonus = max(1, int(atk * 0.8))
            encounter["hp"] -= bonus
            dmg += bonus
            effect_text = f"\n🌟 Второе действие! +{bonus} урона."
    elif effect == "finisher_30pct":
        max_hp = encounter.get("max_hp", 100)
        if encounter["hp"] + dmg <= max_hp * 0.3:
            bonus = int(dmg * 0.8)
            encounter["hp"] -= bonus
            dmg += bonus
            effect_text = f"\n💀 Добивание: +{bonus} урона!"
    elif effect == "chaos_random":
        roll = random.random()
        if roll < 0.25:
            bonus = max(1, int(atk * 0.5))
            encounter["hp"] -= bonus
            effect_text = f"\n🌀 Хаос: взрыв +{bonus} урона."
        elif roll < 0.5:
            encounter["dot"] = {"type": "poison", "turns": 2, "value": max(1, atk // 5)}
            effect_text = "\n🌀 Хаос: яд!"
        elif roll < 0.75:
            heal = max(1, int(monster.get("max_hp", 10) * 0.1))
            monster["current_hp"] = min(monster.get("max_hp", 999), monster.get("current_hp", 0) + heal)
            effect_text = f"\n🌀 Хаос: лечение +{heal}."
        else:
            encounter["attack"] = max(1, int(encounter.get("attack", 5) * 0.75))
            effect_text = "\n🌀 Хаос: атака врага снижена."

    skill_name = skill.get("name", "Навык")

    if encounter["hp"] <= 0:
        return {
            "ok": True, "finished": True, "victory": True,
            "monster_defeated": True, "player_damage": 0,
            "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
            "text": f"✨ {skill_name}! {monster['name']} наносит {dmg} урона и побеждает {encounter['monster_name']}!{effect_text}",
        }

    enemy = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    if encounter.get("skip_turn"):
        enemy = 0
        encounter["skip_turn"] = False
        enemy_text = "Враг оглушён и пропускает ход."
    elif enemy > 0:
        enemy_text = f"Враг отвечает на {enemy}."
    else:
        enemy_text = "Враг не может атаковать!"

    return {
        "ok": True, "finished": False, "player_damage": enemy,
        "text": (
            f"✨ {skill_name}! {monster['name']} наносит {dmg} урона.{effect_text}\n"
            f"HP врага: {max(0, encounter['hp'])}/{encounter.get('max_hp', encounter['hp'])}\n"
            f"{enemy_text}"
        ),
    }


def resolve_skill_use(encounter: dict, monster: dict) -> dict:
    """
    Определяет и применяет активный навык монстра.
    v3: сначала пробуем сгенерированный скилл из combat_skills,
    иначе — legacy логика по эмоции.
    """
    if encounter.get("type") not in ("monster", "wildlife"):
        return {"ok": False, "text": "Сейчас навык использовать не на ком."}

    # Нормализуем wildlife
    if encounter.get("type") == "wildlife":
        if "monster_name" not in encounter:
            encounter["monster_name"] = encounter.get("name", "Зверь")
        if "monster_type" not in encounter:
            encounter["monster_type"] = "nature"

    # Пробуем v3 скилл из профиля монстра
    try:
        mtype = monster.get("monster_type", "void")
        emotion = monster.get("mood", "instinct")
        rarity = monster.get("rarity", "common")
        skills = generate_monster_skills(mtype, emotion, rarity, rarity)
        active_list = skills.get("active_skills", [])
        if active_list:
            skill_id = active_list[0]
            return _apply_active_skill(encounter, monster, skill_id)
    except Exception:
        pass

    # Legacy fallback — по эмоции
    return _legacy_skill(encounter, monster)


def _legacy_skill(encounter: dict, monster: dict) -> dict:
    """Legacy навыки по эмоции — сохранены для совместимости."""
    skill_key = get_active_skill(monster)
    atk = monster.get("attack", 6)
    mtype = monster.get("monster_type")
    emotion = monster.get("mood")
    multiplier, hint = get_damage_multiplier(mtype, encounter.get("monster_type"), emotion)

    if skill_key == "rage":
        dmg = max(1, int(round(random.randint(atk + 2, atk + 6) * multiplier)))
        encounter["hp"] -= dmg
        if encounter["hp"] <= 0:
            return {"ok": True, "finished": True, "player_damage": 0,
                    "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
                    "text": f"🔥 Вспышка ярости! {monster['name']} наносит {dmg} урона и сокрушает {encounter['monster_name']}!"}
        enemy = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
        return {"ok": True, "finished": False, "player_damage": enemy,
                "text": f"🔥 Вспышка ярости! {monster['name']} наносит {dmg} урона.\nHP врага: {encounter['hp']}/{encounter.get('max_hp', encounter['hp'])}\nВраг отвечает на {enemy}."}

    if skill_key == "fear":
        dmg = max(1, int(round(random.randint(max(3, atk - 3), max(5, atk - 1)) * multiplier)))
        encounter["hp"] -= dmg
        encounter["counter_multiplier"] = 0.5
        enemy = max(0, int(random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2) * 0.5))
        if encounter["hp"] <= 0:
            return {"ok": True, "finished": True, "player_damage": 0,
                    "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
                    "text": f"🌑 Покров тени! Враг теряется в темноте."}
        return {"ok": True, "finished": False, "player_damage": enemy,
                "text": f"🌑 Покров тени! {monster['name']} наносит {dmg} урона. Контратака ослаблена до {enemy}."}

    if skill_key == "instinct":
        dmg = max(1, int(round(random.randint(max(4, atk - 1), atk + 2) * multiplier)))
        encounter["hp"] -= dmg
        encounter["bonus_capture"] = min(0.30, encounter.get("bonus_capture", 0.0) + 0.15)
        enemy = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
        if encounter["hp"] <= 0:
            return {"ok": True, "finished": True, "player_damage": 0,
                    "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
                    "text": f"🎯 Охотничья метка! Удар оказался смертельным."}
        return {"ok": True, "finished": False, "player_damage": enemy,
                "text": f"🎯 Охотничья метка! {monster['name']} наносит {dmg} урона. Шанс поимки увеличен.\nВраг отвечает на {enemy}."}

    # inspiration — лечение + удар
    heal_val = min(monster.get("max_hp", monster.get("hp", 1)),
                   monster.get("current_hp", monster.get("hp", 1)) + 6)
    healed = heal_val - monster.get("current_hp", monster.get("hp", 1))
    monster["current_hp"] = heal_val
    dmg = max(1, int(round(random.randint(max(2, atk - 4), max(4, atk - 2)) * multiplier)))
    encounter["hp"] -= dmg
    enemy = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    if encounter["hp"] <= 0:
        return {"ok": True, "finished": True, "player_damage": 0,
                "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
                "text": f"✨ Импульс искры! {monster['name']} исцеляется на {healed} и завершает бой."}
    return {"ok": True, "finished": False, "player_damage": enemy,
            "text": f"✨ Импульс искры! {monster['name']} восстанавливает {healed} HP и наносит {dmg} урона.\nВраг отвечает на {enemy}."}


def apply_skill(encounter: dict, monster: dict, player=None) -> dict | None:
    """Алиас для совместимости с bot.py."""
    return resolve_skill_use(encounter, monster)


def apply_dot_effects(encounter: dict) -> str:
    """
    Применяет DoT эффекты в конце хода (burn, poison, decay).
    Возвращает текст для лога боя.
    """
    dot = encounter.get("dot")
    if not dot or dot.get("turns", 0) <= 0:
        return ""

    dmg = dot.get("value", 1)
    dot_type = dot.get("type", "burn")
    encounter["hp"] = max(0, encounter["hp"] - dmg)
    dot["turns"] -= 1

    if dot["turns"] <= 0:
        del encounter["dot"]

    icons = {"burn": "🔥", "poison": "☠️", "decay": "🖤"}
    icon = icons.get(dot_type, "💫")
    return f"{icon} {dot_type.capitalize()}: {dmg} урона. HP врага: {max(0, encounter['hp'])}"
