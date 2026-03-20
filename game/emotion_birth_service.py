"""
Процедурная генерация монстров при рождении (рекомендация #7).
Вместо 4 фиксированных рецептов — динамические имена, статы и способности.
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

# Пороги рождения по эмоции → минимальное накопление
BIRTH_THRESHOLDS = {
    "rage":        {"threshold": 8,  "base_hp": 34, "base_atk": 11},
    "fear":        {"threshold": 8,  "base_hp": 38, "base_atk": 10},
    "instinct":    {"threshold": 8,  "base_hp": 34, "base_atk": 11},
    "inspiration": {"threshold": 8,  "base_hp": 35, "base_atk": 10},
    "sadness":     {"threshold": 10, "base_hp": 40, "base_atk": 9},
    "joy":         {"threshold": 7,  "base_hp": 32, "base_atk": 10},
    "disgust":     {"threshold": 9,  "base_hp": 36, "base_atk": 11},
    "surprise":    {"threshold": 6,  "base_hp": 30, "base_atk": 12},
}

# Процедурные части имён по эмоции
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

# Редкость зависит от накопленного количества
def _pick_rarity(amount: int, threshold: int) -> str:
    ratio = amount / threshold
    if ratio >= 3.0:  return random.choice(["mythic","legendary"])
    if ratio >= 2.0:  return "legendary"
    if ratio >= 1.5:  return "epic"
    return "epic"   # базово всегда epic при рождении

def _generate_name(emotion: str) -> str:
    prefixes, suffixes = NAME_PARTS.get(emotion, (["Безымянный"], ["Монстр"]))
    return f"{random.choice(prefixes)} {random.choice(suffixes)}"

def _generate_stats(emotion: str, amount: int, threshold: int) -> tuple[int, int]:
    base = BIRTH_THRESHOLDS[emotion]
    bonus_ratio = min(2.0, amount / threshold)
    hp  = base["base_hp"]  + int(bonus_ratio * random.randint(4, 10))
    atk = base["base_atk"] + int(bonus_ratio * random.randint(1,  4))
    return hp, atk


def try_birth_emotional_monster(telegram_id: int) -> dict | None:
    if is_birth_done(telegram_id):
        return None
    player = get_player(telegram_id)
    if player and getattr(player, "birth_cooldown_actions", 0) > 0:
        return None

    emotions = get_player_emotions(telegram_id)

    # Ищем эмоцию, которая достигла порога (берём самую высокую)
    best_emotion = None
    best_amount  = 0
    for emo, cfg in BIRTH_THRESHOLDS.items():
        amount = emotions.get(emo, 0)
        if amount >= cfg["threshold"] and amount > best_amount:
            best_emotion = emo
            best_amount  = amount

    if not best_emotion:
        return None

    cfg      = BIRTH_THRESHOLDS[best_emotion]
    name     = _generate_name(best_emotion)
    rarity   = _pick_rarity(best_amount, cfg["threshold"])
    hp, atk  = _generate_stats(best_emotion, best_amount, cfg["threshold"])

    spend_emotions(telegram_id, {best_emotion: cfg["threshold"]})
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
    start_birth_cooldown(telegram_id, actions=3)
    return monster


def render_birth_text(monster: dict) -> str:
    if not monster:
        return ""
    rarity_lbl = RARITY_LABELS.get(monster["rarity"], monster["rarity"])
    mood_lbl   = MOOD_LABELS.get(monster["mood"], monster["mood"])
    return (
        f"🌌 Твои эмоции сгущаются и обретают форму...\n\n"
        f"✨ Родился эмоциональный монстр!\n"
        f"Имя: {monster['name']}\n"
        f"Редкость: {rarity_lbl}\n"
        f"Эмоция: {mood_lbl}\n"
        f"HP: {monster['max_hp']} | Атака: {monster['attack']}\n\n"
        f"Следующее рождение будет доступно через несколько действий."
    )
