"""
emotion_birth_service.py — Рождение эмоциональных монстров.

Новая механика (v3.2):
- Авторождение в поле УБРАНО — монстры не рождаются случайно при вылазке
- Рождение происходит только в специальных местах:
  * 🌌 Разлом эмоций (emotion_rift) — высший уровень, мощные монстры
  * 🏛 Алтарь Сереброграда (silver_city, craft_quarter) — базовый уровень
- Нужно накопить достаточно концентрированных эмоций (высокий порог)
- Игрок сам инициирует рождение командой /birth или кнопкой в локации
- Эмоции расходуются при рождении
- Редкость монстра зависит от места и количества накопленного
"""
import random
from database.repositories import (
    add_captured_monster, get_player, get_player_emotions,
    is_birth_done, mark_birth_done, spend_emotions, start_birth_cooldown,
)

RARITY_LABELS  = {"common":"Обычный","rare":"Редкий","epic":"Эпический","legendary":"Легендарный","mythic":"Мифический"}
MOOD_LABELS    = {
    "rage":"🔥 Ярость","fear":"😱 Страх","instinct":"🎯 Инстинкт","inspiration":"✨ Вдохновение",
    "sadness":"💧 Грусть","joy":"🌟 Радость","disgust":"🤢 Отвращение","surprise":"⚡ Удивление",
}

# ── Места рождения ─────────────────────────────────────────────────────────────
BIRTH_LOCATIONS = {
    "silver_city": {
        "name": "🏛 Алтарь Сереброграда",
        "desc": "Основное место ритуала. Рождаются обычные и редкие монстры.",
        "threshold_mult": 1.0,   # обычный порог
        "rarity_cap": "epic",    # максимальная редкость
    },
    "emotion_rift": {
        "name": "🌌 Разлом эмоций",
        "desc": "Место силы. Высокая концентрация эмоций рождает легендарных существ.",
        "threshold_mult": 1.5,   # нужно больше эмоций
        "rarity_cap": "mythic",  # нет ограничения
    },
}

# ── Пороги рождения — ВЫСОКИЕ ─────────────────────────────────────────────────
# Игрок должен реально накапливать эмоции, это не случайное событие
BIRTH_THRESHOLDS = {
    "rage":        {"threshold": 40, "base_hp": 34, "base_atk": 11},
    "fear":        {"threshold": 40, "base_hp": 38, "base_atk": 10},
    "instinct":    {"threshold": 40, "base_hp": 34, "base_atk": 11},
    "inspiration": {"threshold": 40, "base_hp": 35, "base_atk": 10},
    "sadness":     {"threshold": 50, "base_hp": 40, "base_atk": 9},
    "joy":         {"threshold": 35, "base_hp": 32, "base_atk": 10},
    "disgust":     {"threshold": 45, "base_hp": 36, "base_atk": 11},
    "surprise":    {"threshold": 30, "base_hp": 30, "base_atk": 12},
}

NAME_PARTS = {
    "rage":        (["Пламенный","Алый","Яростный","Кровавый","Беснующийся"],   ["Разрушитель","Берсерк","Искролом","Пожиратель","Тиран"]),
    "fear":        (["Теневой","Покровный","Безмолвный","Бледный","Тёмный"],    ["Наблюдатель","Страж","Призрак","Шептун","Преследователь"]),
    "instinct":    (["Первозданный","Дикий","Острый","Матёрый","Быстрый"],       ["Следопыт","Охотник","Хищник","Вожак","Зверь"]),
    "inspiration": (["Эфирный","Небесный","Светлый","Лучистый","Сияющий"],      ["Хранитель","Вестник","Пророк","Голос","Исток"]),
    "sadness":     (["Угасший","Скорбный","Туманный","Тихий","Холодный"],        ["Странник","Плакальщик","Отшельник","Молчун","Тень"]),
    "joy":         (["Золотой","Игривый","Искристый","Весёлый","Лучезарный"],    ["Плясун","Озорник","Смеющийся","Искра","Баловень"]),
    "disgust":     (["Гнилостный","Ядовитый","Мрачный","Кислый","Тухлый"],      ["Осквернитель","Гнилец","Токсин","Чумной","Растлитель"]),
    "surprise":    (["Непредсказуемый","Хаотичный","Внезапный","Мерцающий","Загадочный"], ["Призрак","Феномен","Безумец","Молния","Парадокс"]),
}


def _pick_rarity(amount: int, threshold: int, rarity_cap: str = "mythic") -> str:
    ratio = amount / threshold
    caps = ["common","rare","epic","legendary","mythic"]
    cap_idx = caps.index(rarity_cap)
    if ratio >= 3.0:  r = random.choice(["mythic","legendary"])
    elif ratio >= 2.0: r = "legendary"
    elif ratio >= 1.5: r = "epic"
    elif ratio >= 1.0: r = "rare"
    else: r = "common"
    return caps[min(caps.index(r), cap_idx)]

def _generate_name(emotion: str) -> str:
    prefixes, suffixes = NAME_PARTS.get(emotion, (["Безымянный"], ["Монстр"]))
    return f"{random.choice(prefixes)} {random.choice(suffixes)}"

def _generate_stats(emotion: str, amount: int, threshold: int) -> tuple[int, int]:
    base = BIRTH_THRESHOLDS[emotion]
    bonus_ratio = min(3.0, amount / threshold)
    hp  = base["base_hp"]  + int(bonus_ratio * random.randint(4, 10))
    atk = base["base_atk"] + int(bonus_ratio * random.randint(1, 4))
    return hp, atk


def get_birth_panel(telegram_id: int, location_slug: str) -> str:
    """Показывает панель рождения: накопленные эмоции и готовность."""
    location_cfg = BIRTH_LOCATIONS.get(location_slug)
    if not location_cfg:
        return ""
    
    emotions = get_player_emotions(telegram_id)
    lines = [
        f"🌌 {location_cfg['name']}",
        f"{location_cfg['desc']}",
        "",
        "Накопленные эмоции:",
    ]
    
    has_ready = False
    for emo, cfg in sorted(BIRTH_THRESHOLDS.items()):
        amount = emotions.get(emo, 0)
        if amount <= 0:
            continue
        effective_threshold = int(cfg["threshold"] * location_cfg["threshold_mult"])
        mood_label = MOOD_LABELS.get(emo, emo)
        if amount >= effective_threshold:
            lines.append(f"  ✅ {mood_label}: {amount}/{effective_threshold} — ГОТОВО к рождению!")
            has_ready = True
        else:
            lines.append(f"  {mood_label}: {amount}/{effective_threshold}")
    
    if not any(emotions.get(e, 0) > 0 for e in BIRTH_THRESHOLDS):
        lines.append("  Эмоции не накоплены. Исследуй локации!")
    
    if has_ready and not is_birth_done(telegram_id):
        lines.append("\nНажми /birth чтобы провести ритуал рождения.")
    elif is_birth_done(telegram_id):
        lines.append("\n⏳ Ритуал недавно проводился. Нужно время для восстановления.")
    
    return "\n".join(lines)


def try_manual_birth(telegram_id: int, location_slug: str) -> tuple[dict | None, str]:
    """
    Ручное рождение монстра по команде /birth.
    Возвращает (monster | None, error_message).
    """
    location_cfg = BIRTH_LOCATIONS.get(location_slug)
    if not location_cfg:
        return None, f"Рождение монстров возможно только в:\n" + "\n".join(
            f"• {cfg['name']}" for cfg in BIRTH_LOCATIONS.values()
        )
    
    if is_birth_done(telegram_id):
        return None, "⏳ Ритуал недавно проводился. Подожди немного."
    
    player = get_player(telegram_id)
    if not player:
        return None, "Игрок не найден."
    
    emotions = get_player_emotions(telegram_id)
    best_emotion = None
    best_amount  = 0
    
    for emo, cfg in BIRTH_THRESHOLDS.items():
        amount = emotions.get(emo, 0)
        effective_threshold = int(cfg["threshold"] * location_cfg["threshold_mult"])
        if amount >= effective_threshold and amount > best_amount:
            best_emotion = emo
            best_amount  = amount
    
    if not best_emotion:
        # Показываем что накоплено и чего не хватает
        lines = ["Недостаточно эмоций для рождения.\n\nТекущее накопление:"]
        for emo, cfg in BIRTH_THRESHOLDS.items():
            amount = emotions.get(emo, 0)
            effective_threshold = int(cfg["threshold"] * location_cfg["threshold_mult"])
            if amount > 0:
                lines.append(f"  {MOOD_LABELS.get(emo,emo)}: {amount}/{effective_threshold}")
        if len(lines) == 1:
            lines.append("  Эмоции не накоплены. Исследуй локации!")
        return None, "\n".join(lines)
    
    cfg       = BIRTH_THRESHOLDS[best_emotion]
    effective_threshold = int(cfg["threshold"] * location_cfg["threshold_mult"])
    name      = _generate_name(best_emotion)
    rarity    = _pick_rarity(best_amount, effective_threshold, location_cfg["rarity_cap"])
    hp, atk   = _generate_stats(best_emotion, best_amount, effective_threshold)
    
    spend_emotions(telegram_id, {best_emotion: effective_threshold})
    monster = add_captured_monster(
        telegram_id=telegram_id,
        name=name,
        rarity=rarity,
        mood=best_emotion,
        hp=hp,
        attack=atk,
        source_type="emotion",
    )
    mark_birth_done(telegram_id)
    start_birth_cooldown(telegram_id, actions=10)  # кулдаун 10 действий
    # Помещаем в кристалл
    try:
        from game.crystal_service import auto_store_new_monster as _crystal_store
        _ok, _msg = _crystal_store(telegram_id, monster["id"])
        if not _ok:
            return None, _msg
    except Exception:
        pass

    return monster, ""


def try_birth_emotional_monster(telegram_id: int):
    """ЗАГЛУШКА — авторождение отключено. Рождение теперь только ручное через /birth."""
    return None


def render_birth_text(monster: dict | None) -> str:
    if not monster:
        return ""
    rarity_lbl = RARITY_LABELS.get(monster["rarity"], monster["rarity"])
    mood_lbl   = MOOD_LABELS.get(monster["mood"], monster["mood"])
    return (
        f"🌌 Ритуал завершён!\n\n"
        f"✨ Родился эмоциональный монстр!\n"
        f"Имя: {monster['name']}\n"
        f"Редкость: {rarity_lbl}\n"
        f"Эмоция: {mood_lbl}\n"
        f"HP: {monster['max_hp']} | Атака: {monster['attack']}\n\n"
        f"Следующий ритуал доступен через 10 действий."
    )
