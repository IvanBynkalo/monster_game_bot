import random

ABILITIES = {
    "regeneration": {"name": "Регенерация", "description": "После действия монстр иногда восстанавливает немного здоровья."},
    "fury": {"name": "Ярость", "description": "Монстр наносит больше урона обычными атаками."},
    "focus": {"name": "Фокус", "description": "Повышает шанс поимки врага."},
    "shadow_step": {"name": "Теневой шаг", "description": "Иногда позволяет полностью избежать входящего удара."},
    "crystal_skin": {"name": "Кристальная кожа", "description": "Часть входящего урона поглощается."},
    "hunter_instinct": {"name": "Инстинкт охотника", "description": "Усиливает преследование и атаку по редким целям."},
}

MONSTER_ABILITIES = {
    "Златорогий олень": ["focus"],
    "Каменный великан": ["regeneration", "crystal_skin"],
    "Луговой титан": ["fury"],
    "Живой монолит": ["regeneration", "crystal_skin"],
    "Лесной спрайт": ["focus"],
    "Древний спрайт": ["focus", "regeneration"],
    "Болотный охотник": ["hunter_instinct"],
    "Болотный хищник": ["hunter_instinct", "shadow_step"],
    "Угольный клык": ["fury"],
    "Пламенный клык": ["fury", "hunter_instinct"],
    "Теневой слизень": ["shadow_step"],
    "Кристальный дух": ["crystal_skin"],
}

def get_monster_abilities(monster: dict) -> list[str]:
    if not monster:
        return []
    abilities = list(monster.get("abilities", []))
    if not abilities:
        abilities = MONSTER_ABILITIES.get(monster.get("name", ""), []).copy()
        monster["abilities"] = abilities
    return abilities

def render_abilities(monster: dict) -> str:
    abilities = get_monster_abilities(monster)
    if not abilities:
        return "Способности: нет"
    labels = [ABILITIES.get(key, {}).get("name", key) for key in abilities]
    return "Способности: " + ", ".join(labels)

def get_attack_bonus(monster: dict, encounter: dict | None = None) -> int:
    abilities = get_monster_abilities(monster)
    bonus = 0
    if "fury" in abilities:
        bonus += 3
    if "hunter_instinct" in abilities and encounter and encounter.get("rarity") in {"epic", "legendary"}:
        bonus += 2
    return bonus

def get_capture_bonus(monster: dict) -> float:
    abilities = get_monster_abilities(monster)
    bonus = 0.0
    if "focus" in abilities:
        bonus += 0.12
    if "hunter_instinct" in abilities:
        bonus += 0.08
    return bonus

def mitigate_incoming_damage(monster: dict, damage: int):
    abilities = get_monster_abilities(monster)
    text_parts = []
    final_damage = damage
    if "shadow_step" in abilities and random.random() < 0.20:
        final_damage = 0
        text_parts.append("🌫 Теневой шаг: монстр полностью уклоняется от удара.")
    else:
        if "crystal_skin" in abilities and final_damage > 0:
            reduced = min(2, final_damage)
            final_damage -= reduced
            text_parts.append(f"💎 Кристальная кожа снижает урон на {reduced}.")
    return final_damage, "\n".join(text_parts)

def try_regeneration(monster: dict):
    abilities = get_monster_abilities(monster)
    if "regeneration" not in abilities:
        return 0
    if random.random() < 0.35:
        before = monster.get("current_hp", monster.get("hp", 1))
        max_hp = monster.get("max_hp", monster.get("hp", 1))
        after = min(max_hp, before + 4)
        healed = after - before
        monster["current_hp"] = after
        return healed
    return 0
