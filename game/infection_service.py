from database.repositories import get_active_monster

INFECTION_STAGE_LABELS = {
    0: "нет",
    1: "След",
    2: "Искажение",
    3: "Мутация",
    4: "Критическая форма",
}

INFECTION_TYPE_LABELS = {
    "rage": "Ярость",
    "fear": "Страх",
    "instinct": "Инстинкт",
    "inspiration": "Вдохновение",
}

def _dominant_emotion_key(emotions: dict):
    if not emotions:
        return None
    best_key = None
    best_value = 0
    for key, value in emotions.items():
        if value > best_value:
            best_key = key
            best_value = value
    return best_key if best_value > 0 else None

def _stage_from_distortion(distortion: int) -> int:
    if distortion >= 80:
        return 4
    if distortion >= 50:
        return 3
    if distortion >= 25:
        return 2
    if distortion >= 10:
        return 1
    return 0

def apply_dominant_emotion_infection(telegram_id: int):
    from database.repositories import get_player_emotions
    monster = get_active_monster(telegram_id)
    if not monster:
        return None
    emotions = get_player_emotions(telegram_id)
    dominant = _dominant_emotion_key(emotions)
    if not dominant:
        return None

    previous_type = monster.get("infection_type")
    previous_stage = monster.get("infection_stage", 0)

    if previous_type and previous_type != dominant:
        monster["distortion"] = max(10, monster.get("distortion", 0) // 2)

    monster["infection_type"] = dominant
    monster["distortion"] = min(100, monster.get("distortion", 0) + 5)
    monster["infection_stage"] = _stage_from_distortion(monster["distortion"])

    return {
        "monster_name": monster["name"],
        "infection_type": monster["infection_type"],
        "infection_stage": monster["infection_stage"],
        "distortion": monster["distortion"],
        "previous_stage": previous_stage,
        "type_changed": previous_type is not None and previous_type != dominant,
    }

def render_monster_infection(monster: dict | None):
    if not monster or not monster.get("infection_type"):
        return "Искажение: нет"
    stage = INFECTION_STAGE_LABELS.get(monster.get("infection_stage", 0), str(monster.get("infection_stage", 0)))
    type_label = INFECTION_TYPE_LABELS.get(monster["infection_type"], monster["infection_type"])
    return f"Искажение: {type_label} | Стадия: {stage} | Сила искажения: {monster.get('distortion', 0)}/100"

def render_infection_update(update: dict | None):
    if not update:
        return ""
    stage = INFECTION_STAGE_LABELS.get(update["infection_stage"], str(update["infection_stage"]))
    type_label = INFECTION_TYPE_LABELS.get(update["infection_type"], update["infection_type"])
    lines = [
        f"🌀 {update['monster_name']} меняется под влиянием эмоций.",
        f"Тип искажения: {type_label}",
        f"Стадия: {stage}",
        f"Сила искажения: {update['distortion']}/100",
    ]
    if update.get("type_changed"):
        lines.append("Тип искажения сменился, часть силы рассеялась.")
    return "\n".join(lines)
