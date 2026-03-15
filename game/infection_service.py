from database.repositories import get_active_monster
from game.emotion_service import dominant_emotion

INFECTION_LABELS = {
    "rage": "Гнев",
    "fear": "Тень",
    "instinct": "Охота",
    "inspiration": "Искра",
}

STAGE_LABELS = {
    0: "Нет",
    1: "След",
    2: "Искажение",
    3: "Мутация",
}

def apply_dominant_emotion_infection(telegram_id: int):
    monster = get_active_monster(telegram_id)
    if not monster:
        return None
    dominant = dominant_emotion(telegram_id)
    if not dominant:
        return None

    if not monster.get("infection_type"):
        monster["infection_type"] = dominant
        monster["infection_stage"] = 1
        monster["corruption"] = 20
    elif monster["infection_type"] == dominant:
        monster["corruption"] = min(100, monster.get("corruption", 0) + 15)
        c = monster["corruption"]
        if c >= 70:
            monster["infection_stage"] = 3
        elif c >= 35:
            monster["infection_stage"] = 2
        else:
            monster["infection_stage"] = 1

    return {
        "monster_name": monster["name"],
        "infection_type": monster["infection_type"],
        "infection_stage": monster["infection_stage"],
        "corruption": monster["corruption"],
    }

def render_infection_update(update):
    if not update:
        return ""
    return (
        f"🧬 {update['monster_name']} впитывает эмоции.\n"
        f"Заражение: {INFECTION_LABELS.get(update['infection_type'], update['infection_type'])}\n"
        f"Стадия: {STAGE_LABELS.get(update['infection_stage'], update['infection_stage'])}\n"
        f"Коррупция: {update['corruption']}/100"
    )

def render_monster_infection(monster):
    if not monster or not monster.get("infection_type"):
        return "Заражение: нет"
    return (
        f"Заражение: {INFECTION_LABELS.get(monster['infection_type'], monster['infection_type'])} | "
        f"Стадия: {STAGE_LABELS.get(monster.get('infection_stage', 0), monster.get('infection_stage', 0))} | "
        f"Коррупция: {monster.get('corruption', 0)}/100"
    )
