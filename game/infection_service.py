"""
Система заражения эмоциями + комбо-мутации (рекомендации #5, #6).
"""
import random
from database.repositories import get_active_monster, save_monster, get_player_emotions

INFECTION_STAGE_LABELS = {
    0: "нет",
    1: "След",
    2: "Искажение",
    3: "Мутация",
    4: "Критическая форма",
}

INFECTION_TYPE_LABELS = {
    "rage":        "🔥 Ярость",
    "fear":        "😱 Страх",
    "instinct":    "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение",
    "sadness":     "💧 Грусть",
    "joy":         "🌟 Радость",
    "disgust":     "🤢 Отвращение",
    "surprise":    "⚡ Удивление",
}

# ── Комбо-мутации (рекомендация #6) ──────────────────────────────────────────
# Ключ: frozenset двух доминирующих эмоций → эффекты
COMBO_MUTATIONS: dict[frozenset, dict] = {
    frozenset({"rage",        "fear"}):        {"name": "Берсерк-параноик",       "atk_bonus": 5,  "def_bonus": -2, "special": None},
    frozenset({"rage",        "sadness"}):     {"name": "Мрачный разрушитель",    "atk_bonus": 4,  "def_bonus":  0, "special": "lifesteal"},
    frozenset({"rage",        "joy"}):         {"name": "Неистовый ликующий",     "atk_bonus": 6,  "def_bonus": -3, "special": None},
    frozenset({"inspiration", "sadness"}):     {"name": "Меланхоличный пророк",   "atk_bonus": 0,  "def_bonus":  3, "special": "prophecy"},
    frozenset({"inspiration", "joy"}):         {"name": "Сияющий вдохновитель",   "atk_bonus": 2,  "def_bonus":  2, "special": "aura"},
    frozenset({"fear",        "sadness"}):     {"name": "Потерянная душа",         "atk_bonus": -1, "def_bonus":  5, "special": "ghost"},
    frozenset({"instinct",    "rage"}):        {"name": "Первобытный хищник",      "atk_bonus": 4,  "def_bonus":  1, "special": "frenzy"},
    frozenset({"instinct",    "joy"}):         {"name": "Удачливый следопыт",      "atk_bonus": 2,  "def_bonus":  0, "special": "luck"},
    frozenset({"disgust",     "rage"}):        {"name": "Ядовитый берсерк",        "atk_bonus": 3,  "def_bonus": -1, "special": "poison"},
    frozenset({"disgust",     "fear"}):        {"name": "Осквернённый страж",      "atk_bonus": 0,  "def_bonus":  4, "special": "corrosion"},
    frozenset({"surprise",    "inspiration"}): {"name": "Хаотичный гений",         "atk_bonus": 1,  "def_bonus":  1, "special": "chaos"},
    frozenset({"surprise",    "fear"}):        {"name": "Непредсказуемый ужас",    "atk_bonus": 2,  "def_bonus":  0, "special": "confusion"},
}

SPECIAL_LABELS = {
    "lifesteal":  "🩸 Кражу жизни",
    "prophecy":   "🔮 Предвидение",
    "aura":       "✨ Ауру силы",
    "ghost":      "👻 Фазовый сдвиг",
    "frenzy":     "⚡ Бешенство",
    "luck":       "🍀 Удачу",
    "poison":     "☠️ Яд",
    "corrosion":  "🧪 Коррозию",
    "chaos":      "🎲 Хаос",
    "confusion":  "💫 Замешательство",
}


def _dominant_emotions_top2(emotions: dict) -> list[str]:
    """Возвращает две самые сильные эмоции (или одну если вторая 0)."""
    sorted_emo = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
    return [k for k, v in sorted_emo if v > 0][:2]


def _stage_from_distortion(distortion: int) -> int:
    if distortion >= 80: return 4
    if distortion >= 50: return 3
    if distortion >= 25: return 2
    if distortion >= 10: return 1
    return 0


def _get_combo(emotions: dict) -> dict | None:
    top2 = _dominant_emotions_top2(emotions)
    if len(top2) < 2:
        return None
    key = frozenset(top2)
    return COMBO_MUTATIONS.get(key)


def apply_dominant_emotion_infection(telegram_id: int) -> dict | None:
    monster = get_active_monster(telegram_id)
    if not monster:
        return None
    emotions = get_player_emotions(telegram_id)
    top2 = _dominant_emotions_top2(emotions)
    if not top2:
        return None

    dominant = top2[0]
    previous_type  = monster.get("infection_type")
    previous_stage = monster.get("infection_stage", 0)

    # Смена доминирующей эмоции рассеивает часть силы
    if previous_type and previous_type != dominant:
        monster["distortion"] = max(10, monster.get("distortion", 0) // 2)

    monster["infection_type"]  = dominant
    monster["distortion"]      = min(100, monster.get("distortion", 0) + 5)
    monster["infection_stage"] = _stage_from_distortion(monster["distortion"])

    # Проверяем и применяем комбо-мутацию
    combo = _get_combo(emotions)
    old_combo = monster.get("combo_mutation")
    if combo and monster["infection_stage"] >= 3:
        monster["combo_mutation"] = combo["name"]
    else:
        monster["combo_mutation"] = None

    save_monster(monster)

    return {
        "monster_name":   monster["name"],
        "infection_type": monster["infection_type"],
        "infection_stage": monster["infection_stage"],
        "distortion":     monster["distortion"],
        "previous_stage": previous_stage,
        "type_changed":   previous_type is not None and previous_type != dominant,
        "combo":          combo if monster.get("combo_mutation") else None,
        "combo_changed":  monster.get("combo_mutation") != old_combo,
    }


def get_combo_bonuses(monster: dict) -> dict:
    """Возвращает активные бонусы от комбо-мутации для расчётов в бою."""
    combo_name = monster.get("combo_mutation")
    if not combo_name:
        return {}
    for combo in COMBO_MUTATIONS.values():
        if combo["name"] == combo_name:
            return combo
    return {}


def render_monster_infection(monster: dict | None) -> str:
    if not monster or not monster.get("infection_type"):
        return "Искажение: нет"
    stage     = INFECTION_STAGE_LABELS.get(monster.get("infection_stage", 0), "?")
    type_lbl  = INFECTION_TYPE_LABELS.get(monster["infection_type"], monster["infection_type"])
    combo     = monster.get("combo_mutation")
    lines = [f"Искажение: {type_lbl} | Стадия: {stage} | {monster.get('distortion',0)}/100"]
    if combo:
        lines.append(f"🌀 Комбо-мутация: {combo}")
    return "\n".join(lines)


def render_infection_update(update: dict | None) -> str:
    if not update:
        return ""
    stage    = INFECTION_STAGE_LABELS.get(update["infection_stage"], str(update["infection_stage"]))
    type_lbl = INFECTION_TYPE_LABELS.get(update["infection_type"], update["infection_type"])
    lines = [
        f"🌀 {update['monster_name']} меняется под влиянием эмоций.",
        f"Тип искажения: {type_lbl}",
        f"Стадия: {stage} | Сила: {update['distortion']}/100",
    ]
    if update.get("type_changed"):
        lines.append("Тип сменился — часть силы рассеялась.")
    if update.get("combo") and update.get("combo_changed"):
        combo = update["combo"]
        lines.append(f"\n⚡ Новая комбо-мутация: {combo['name']}!")
        special = combo.get("special")
        if special and special in SPECIAL_LABELS:
            lines.append(f"Способность: {SPECIAL_LABELS[special]}")
    return "\n".join(lines)
