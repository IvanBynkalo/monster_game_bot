import random
from game.type_service import get_damage_multiplier

SKILL_LABELS = {
    "rage": "Вспышка ярости",
    "fear": "Покров тени",
    "instinct": "Охотничья метка",
    "inspiration": "Импульс искры",
}

def get_active_skill(monster: dict):
    if not monster:
        return None
    return monster.get("infection_type") or monster.get("mood")

def get_active_skill_label(monster: dict):
    skill_key = get_active_skill(monster)
    return SKILL_LABELS.get(skill_key, "Навык")

def resolve_skill_use(encounter: dict, monster: dict):
    if encounter["type"] != "monster":
        return {"ok": False, "text": "Сейчас навык использовать не на ком."}
    skill_key = get_active_skill(monster)
    atk = monster.get("attack", 6)
    multiplier = get_damage_multiplier(monster.get("monster_type"), encounter.get("monster_type"))

    if skill_key == "rage":
        dmg = max(1, int(round(random.randint(atk + 2, atk + 6) * multiplier)))
        encounter["hp"] -= dmg
        if encounter["hp"] <= 0:
            return {"ok": True, "finished": True, "player_damage": 0, "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
                    "text": f"{SKILL_LABELS['rage']}! {monster['name']} наносит {dmg} урона и сокрушает {encounter['monster_name']}!"}
        enemy = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
        return {"ok": True, "finished": False, "player_damage": enemy,
                "text": f"{SKILL_LABELS['rage']}! {monster['name']} наносит {dmg} урона.\nОсталось HP врага: {encounter['hp']}/{encounter['max_hp']}\nВраг отвечает на {enemy}."}

    if skill_key == "fear":
        dmg = max(1, int(round(random.randint(max(3, atk - 3), max(5, atk - 1)) * multiplier)))
        encounter["hp"] -= dmg
        encounter["counter_multiplier"] = 0.5
        enemy = max(0, int(random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2) * encounter["counter_multiplier"]))
        encounter["counter_multiplier"] = 1.0
        if encounter["hp"] <= 0:
            return {"ok": True, "finished": True, "player_damage": 0, "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
                    "text": f"{SKILL_LABELS['fear']}! Враг теряется в тенях и падает."}
        return {"ok": True, "finished": False, "player_damage": enemy,
                "text": f"{SKILL_LABELS['fear']}! {monster['name']} скрывает команду тенью и наносит {dmg} урона.\nКонтратака ослаблена до {enemy}."}

    if skill_key == "instinct":
        dmg = max(1, int(round(random.randint(max(4, atk - 1), atk + 2) * multiplier)))
        encounter["hp"] -= dmg
        encounter["bonus_capture"] = min(0.30, encounter.get("bonus_capture", 0.0) + 0.15)
        enemy = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
        if encounter["hp"] <= 0:
            return {"ok": True, "finished": True, "player_damage": 0, "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
                    "text": f"{SKILL_LABELS['instinct']}! Удар оказался смертельным."}
        return {"ok": True, "finished": False, "player_damage": enemy,
                "text": f"{SKILL_LABELS['instinct']}! {monster['name']} наносит {dmg} урона и отмечает цель.\nШанс поимки увеличен."}

    heal = min(monster.get("max_hp", monster.get("hp", 1)), monster.get("current_hp", monster.get("hp", 1)) + 6)
    healed = heal - monster.get("current_hp", monster.get("hp", 1))
    monster["current_hp"] = heal
    dmg = max(1, int(round(random.randint(max(2, atk - 4), max(4, atk - 2)) * multiplier)))
    encounter["hp"] -= dmg
    enemy = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    if encounter["hp"] <= 0:
        return {"ok": True, "finished": True, "player_damage": 0, "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
                "text": f"{SKILL_LABELS['inspiration']}! {monster['name']} исцеляется на {healed} и завершает бой вспышкой."}
    return {"ok": True, "finished": False, "player_damage": enemy,
            "text": f"{SKILL_LABELS['inspiration']}! {monster['name']} восстанавливает {healed} HP и наносит {dmg} урона.\nВраг отвечает на {enemy}."}


# Алиас для совместимости с bot.py
def apply_skill(encounter: dict, monster: dict, player=None) -> dict | None:
    """Обёртка над resolve_skill_use для вызова из fight_inline_callback."""
    return resolve_skill_use(encounter, monster)
