from database.repositories import add_emotions, get_player_emotions

EMOTION_LABELS = {
    "rage": "🔥 Ярость",
    "fear": "😱 Страх",
    "instinct": "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение",
}

EMOTION_REWARDS = {
    "battle_win": {"rage": 1},
    "capture_success": {"instinct": 2},
    "flee_success": {"fear": 1},
    "anomaly": {"inspiration": 1},
}

def grant_event_emotions(telegram_id: int, event_key: str, district_mood: str | None = None):
    changes = {}
    for key, value in EMOTION_REWARDS.get(event_key, {}).items():
        changes[key] = changes.get(key, 0) + value
    if district_mood:
        changes[district_mood] = changes.get(district_mood, 0) + 1
    if not changes:
        return get_player_emotions(telegram_id), {}
    emotions = add_emotions(telegram_id, changes)
    return emotions, changes

def dominant_emotion(telegram_id: int):
    emotions = get_player_emotions(telegram_id)
    top_key = None
    top_val = -1
    tied = False
    for key, value in emotions.items():
        if value > top_val:
            top_key = key
            top_val = value
            tied = False
        elif value == top_val:
            tied = True
    if top_val <= 0 or tied:
        return None
    return top_key

def render_emotion_changes(changes: dict):
    if not changes:
        return ""
    lines = ["Эмоции:"]
    for key, value in changes.items():
        lines.append(f"{EMOTION_LABELS.get(key, key)} +{value}")
    return "\n".join(lines)

def render_emotions_panel(telegram_id: int):
    emotions = get_player_emotions(telegram_id)
    lines = ["Эмоциональный след:"]
    for key in ["rage", "fear", "instinct", "inspiration"]:
        lines.append(f"{EMOTION_LABELS[key]}: {emotions.get(key, 0)}")
    return "\n".join(lines)
