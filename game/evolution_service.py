"""
Эволюция монстров — теперь сохраняет изменения в БД (рек. #4).
"""
from game.monster_abilities import MONSTER_ABILITIES

EVOLUTIONS = {
    "Лесной спрайт":   {"level": 5, "evolves_to": "Древний спрайт",   "hp_bonus": 8,  "attack_bonus": 2, "new_abilities": ["focus", "regeneration"]},
    "Болотный охотник": {"level": 6, "evolves_to": "Болотный хищник",  "hp_bonus": 10, "attack_bonus": 3, "new_abilities": ["hunter_instinct", "shadow_step"]},
    "Угольный клык":   {"level": 7, "evolves_to": "Пламенный клык",   "hp_bonus": 12, "attack_bonus": 4, "new_abilities": ["fury", "hunter_instinct"]},
    # Эмоциональные рождения тоже могут эволюционировать
    "Багровый Искролом":         {"level": 8, "evolves_to": "Пламенный Повелитель",    "hp_bonus": 15, "attack_bonus": 5, "new_abilities": ["fury", "crystal_skin"]},
    "Покровный Наблюдатель":     {"level": 8, "evolves_to": "Теневой Страж",           "hp_bonus": 14, "attack_bonus": 4, "new_abilities": ["shadow_step", "regeneration"]},
    "Первозданный Следопыт":     {"level": 8, "evolves_to": "Матёрый Следопыт",        "hp_bonus": 13, "attack_bonus": 5, "new_abilities": ["hunter_instinct", "focus"]},
    "Эфирный Хранитель Искры":   {"level": 8, "evolves_to": "Небесный Хранитель",      "hp_bonus": 12, "attack_bonus": 4, "new_abilities": ["focus", "regeneration"]},
}


def check_evolution(monster: dict) -> str | None:
    evo = EVOLUTIONS.get(monster.get("name",""))
    if not evo:
        return None
    if monster.get("level", 1) >= evo["level"] and monster.get("evolution_stage", 0) == 0:
        return evo["evolves_to"]
    return None


def try_evolve_monster(monster: dict) -> dict | None:
    evo = EVOLUTIONS.get(monster.get("name",""))
    if not evo:
        return None
    if monster.get("evolution_stage", 0) > 0:
        return None
    if monster.get("level", 1) < evo["level"]:
        return None

    old_name = monster["name"]
    monster["name"]            = evo["evolves_to"]
    monster["evolution_stage"] = monster.get("evolution_stage", 0) + 1
    monster["evolution_from"]  = old_name
    monster["max_hp"]          = monster.get("max_hp", monster.get("hp", 1)) + evo.get("hp_bonus", 0)
    monster["attack"]          = monster.get("attack", 1) + evo.get("attack_bonus", 0)
    monster["current_hp"]      = monster["max_hp"]
    monster["abilities"]       = list(dict.fromkeys(
        evo.get("new_abilities", []) + MONSTER_ABILITIES.get(monster["name"], [])
    ))

    # Сохраняем в БД
    from database.repositories import save_monster
    save_monster(monster)
    return monster


def try_evolve_active_monster(telegram_id: int) -> dict | None:
    from database.repositories import get_active_monster
    monster = get_active_monster(telegram_id)
    if not monster:
        return None
    return try_evolve_monster(monster)


def render_evolution_text(monster: dict | None) -> str:
    if not monster:
        return ""
    old_name = monster.get("evolution_from", "Предыдущая форма")
    abilities_list = monster.get("abilities", [])
    from game.monster_abilities import ABILITIES
    ability_names = [ABILITIES.get(a, {}).get("name", a) for a in abilities_list]
    lines = [
        f"🦋 Эволюция!",
        f"{old_name} → {monster['name']}",
        f"HP: {monster['current_hp']}/{monster['max_hp']}",
        f"Атака: {monster['attack']}",
    ]
    if ability_names:
        lines.append(f"Способности: {', '.join(ability_names)}")
    return "\n".join(lines)
