"""
Система эмоций — расширена с 4 до 8 эмоций (рекомендация #5).
"""
from database.repositories import add_emotions, get_player_emotions

EMOTION_LABELS = {
    "rage":        "🔥 Ярость",
    "fear":        "😱 Страх",
    "instinct":    "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение",
    "sadness":     "💧 Грусть",
    "joy":         "🌟 Радость",
    "disgust":     "🤢 Отвращение",
    "surprise":    "⚡ Удивление",
}

ALL_EMOTIONS = list(EMOTION_LABELS.keys())

# Событие → изменение эмоций
EVENT_EMOTIONS = {
    "battle_win":       {"rage": 1},
    "capture_success":  {"instinct": 1},
    "flee_success":     {"fear": 1},
    "anomaly":          {"fear": 1, "inspiration": 1},
    "dungeon_win":      {"rage": 2, "instinct": 1},
    "dungeon_boss_win": {"rage": 3, "inspiration": 2},
    "craft_success":    {"inspiration": 1},
    "gather_rare":      {"joy": 1, "surprise": 1},
    "player_defeated":  {"sadness": 2, "fear": 1},
    "pvp_win":          {"rage": 1, "joy": 2},
    "pvp_loss":         {"sadness": 1, "disgust": 1},
}

DISTRICT_MOOD_TO_EMOTION = {
    "rage":        "rage",
    "fear":        "fear",
    "instinct":    "instinct",
    "inspiration": "inspiration",
    "sadness":     "sadness",
    "joy":         "joy",
}


def render_emotions_panel(telegram_id: int) -> str:
    emotions = get_player_emotions(telegram_id)
    lines = ["Эмоции:"]
    for key in ALL_EMOTIONS:
        val = emotions.get(key, 0)
        if val > 0:
            lines.append(f"{EMOTION_LABELS[key]}: {val}")
    if len(lines) == 1:
        lines.append("Пусто")
    return "\n".join(lines)


def grant_event_emotions(telegram_id: int, event_type: str, district_mood: str | None = None) -> tuple[dict, dict]:
    changes = dict(EVENT_EMOTIONS.get(event_type, {}))
    if district_mood in DISTRICT_MOOD_TO_EMOTION and event_type in {"battle_win", "capture_success", "anomaly"}:
        mood_key = DISTRICT_MOOD_TO_EMOTION[district_mood]
        changes[mood_key] = changes.get(mood_key, 0) + 1
    if changes:
        add_emotions(telegram_id, changes)
    return get_player_emotions(telegram_id), changes


def render_emotion_changes(changes: dict) -> str:
    lines = []
    for key in ALL_EMOTIONS:
        value = changes.get(key, 0)
        if value:
            sign = "+" if value > 0 else ""
            lines.append(f"{EMOTION_LABELS[key]} {sign}{value}")
    if not lines:
        return ""
    return "Эмоции:\n" + "\n".join(lines)
