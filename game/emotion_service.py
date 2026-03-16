from database.repositories import add_emotions, get_player_emotions

EMOTION_LABELS = {
    "rage": "🔥 Ярость",
    "fear": "😱 Страх",
    "instinct": "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение",
}

EVENT_EMOTIONS = {
    "battle_win": {"rage": 1},
    "capture_success": {"instinct": 1},
    "flee_success": {"fear": 0},
    "anomaly": {"fear": 1, "inspiration": 1},
}

DISTRICT_MOOD_TO_EMOTION = {
    "rage": "rage",
    "fear": "fear",
    "instinct": "instinct",
    "inspiration": "inspiration",
}

def render_emotions_panel(telegram_id: int):
    emotions = get_player_emotions(telegram_id)
    lines = ["Эмоции:"]
    for key in ["rage", "fear", "instinct", "inspiration"]:
        lines.append(f"{EMOTION_LABELS[key]}: {emotions.get(key, 0)}")
    return "\n".join(lines)

def grant_event_emotions(telegram_id: int, event_type: str, district_mood: str | None = None):
    changes = dict(EVENT_EMOTIONS.get(event_type, {}))
    if district_mood in DISTRICT_MOOD_TO_EMOTION and event_type in {"battle_win", "capture_success", "anomaly"}:
        mood_key = DISTRICT_MOOD_TO_EMOTION[district_mood]
        changes[mood_key] = changes.get(mood_key, 0) + 1
    add_emotions(telegram_id, changes)
    return get_player_emotions(telegram_id), changes

def render_emotion_changes(changes: dict):
    lines = []
    for key in ["rage", "fear", "instinct", "inspiration"]:
        value = changes.get(key, 0)
        if value:
            lines.append(f"{EMOTION_LABELS[key]} +{value}")
    if not lines:
        return ""
    return "Эмоции:\n" + "\n".join(lines)
