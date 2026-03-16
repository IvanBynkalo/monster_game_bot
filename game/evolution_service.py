from game.monster_abilities import MONSTER_ABILITIES

EVOLUTIONS = {
    "Лесной спрайт": {"level": 5, "evolves_to": "Древний спрайт", "hp_bonus": 8, "attack_bonus": 2, "new_abilities": ["focus", "regeneration"]},
    "Болотный охотник": {"level": 6, "evolves_to": "Болотный хищник", "hp_bonus": 10, "attack_bonus": 3, "new_abilities": ["hunter_instinct", "shadow_step"]},
    "Угольный клык": {"level": 7, "evolves_to": "Пламенный клык", "hp_bonus": 12, "attack_bonus": 4, "new_abilities": ["fury", "hunter_instinct"]},
}

def check_evolution(monster):
    evo = EVOLUTIONS.get(monster["name"])
    if not evo:
        return None
    if monster.get("level", 1) >= evo["level"]:
        return evo["evolves_to"]
    return None

def try_evolve_monster(monster: dict):
    evo = EVOLUTIONS.get(monster.get("name"))
    if not evo:
        return None
    if monster.get("evolution_stage", 0) > 0:
        return None
    if monster.get("level", 1) < evo["level"]:
        return None
    old_name = monster["name"]
    monster["name"] = evo["evolves_to"]
    monster["evolution_stage"] = monster.get("evolution_stage", 0) + 1
    monster["max_hp"] = monster.get("max_hp", monster.get("hp", 1)) + evo.get("hp_bonus", 0)
    monster["attack"] = monster.get("attack", 1) + evo.get("attack_bonus", 0)
    monster["current_hp"] = monster["max_hp"]
    monster["abilities"] = list(dict.fromkeys(evo.get("new_abilities", []) + MONSTER_ABILITIES.get(monster["name"], [])))
    monster["evolution_from"] = old_name
    return monster

def try_evolve_active_monster(telegram_id: int):
    from database.repositories import get_active_monster
    monster = get_active_monster(telegram_id)
    if not monster:
        return None
    return try_evolve_monster(monster)

def render_evolution_text(monster: dict | None):
    if not monster:
        return ""
    old_name = monster.get("evolution_from", "Предыдущая форма")
    return (
        f"🦋 Эволюция!\n"
        f"{old_name} → {monster['name']}\n"
        f"HP: {monster['current_hp']}/{monster['max_hp']}\n"
        f"Атака: {monster['attack']}"
    )
