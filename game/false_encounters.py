"""
false_encounters.py — Ложные встречи при исследовании.

Типы:
- fake_tracks     — подделка следов редкого монстра
- bait            — приманка, за которой скрывается ловушка
- aggressive_pack — агрессивная стая (сложный бой с несколькими врагами)
- hunter_trap     — ловушка охотников (дебафф)

Шанс: 8% от всех событий при исследовании.
"""
import random

FALSE_ENCOUNTERS = [
    {
        "type": "fake_tracks",
        "title": "👣 Ложные следы",
        "text": (
            "Ты заметил свежие следы редкого монстра — крупные, глубокие.\n"
            "Ты осторожно двинулся по следу... но они обрываются у ручья.\n\n"
            "Кто-то специально нарисовал их. Ловушка для охотников.\n"
            "Настоящий зверь давно ушёл."
        ),
        "effect": "none",
    },
    {
        "type": "bait",
        "title": "🍖 Приманка",
        "text": (
            "В кустах лежит свежее мясо — явная приманка.\n"
            "Ты делаешь шаг вперёд... и слышишь щелчок.\n\n"
            "🪤 Ловушка! Верёвка захлёстывает ногу.\n"
            "Ты выбираешься с трудом, потеряв немного энергии."
        ),
        "effect": "energy_loss",
        "effect_value": 1,
    },
    {
        "type": "aggressive_pack",
        "title": "🐺 Агрессивная стая",
        "text": (
            "Тишина... а потом — вой с трёх сторон.\n"
            "Стая окружила тебя. Их слишком много для боя.\n\n"
            "Ты медленно отступаешь, не поворачиваясь спиной.\n"
            "Стая провожает тебя до края территории и отступает."
        ),
        "effect": "forced_retreat",
    },
    {
        "type": "hunter_trap",
        "title": "🏹 Ловушка охотников",
        "text": (
            "Браконьеры! Сеть накрыла тебя сверху.\n"
            "Пока ты выбирался, они ушли — видимо испугались твоего монстра.\n\n"
            "Среди верёвок ты нашёл монету — видно обронили в спешке."
        ),
        "effect": "small_gold",
        "effect_value": random.randint(5, 15),
    },
    {
        "type": "mirage",
        "title": "🌫 Мираж",
        "text": (
            "Вдалеке — силуэт легендарного монстра.\n"
            "Ты бросился к нему, но чем ближе подходил — тем больше он таял.\n\n"
            "Болотные испарения. Опытные следопыты знают этот трюк природы.\n"
            "Ты потратил время, но зато видел что-то красивое."
        ),
        "effect": "none",
    },
    {
        "type": "decoy_nest",
        "title": "🪹 Ложное гнездо",
        "text": (
            "Гнездо редкого зверя! Яйца ещё тёплые...\n"
            "Ты потянулся к ним — и чуть не попал под удар крыла.\n\n"
            "Подсадная птица! Настоящее гнездо в другом месте.\n"
            "Хищник прогнал тебя, но не преследовал далеко."
        ),
        "effect": "none",
    },
]


def roll_false_encounter() -> dict | None:
    """8% шанс ложной встречи."""
    if random.random() > 0.08:
        return None
    enc = random.choice(FALSE_ENCOUNTERS)
    return {**enc, "is_false": True}


def apply_false_encounter_effect(telegram_id: int, encounter: dict) -> str:
    """Применяет эффект ложной встречи и возвращает дополнение к тексту."""
    effect = encounter.get("effect", "none")
    if effect == "energy_loss":
        try:
            from database.repositories import get_player, _update_player_field
            p = get_player(telegram_id)
            if p:
                _update_player_field(telegram_id, energy=max(0, p.energy - encounter.get("effect_value", 1)))
        except Exception:
            pass
        return f"\n⚡ Потеряно {encounter.get('effect_value', 1)} энергии."
    elif effect == "small_gold":
        try:
            from database.repositories import add_player_gold
            gold = encounter.get("effect_value", 10)
            add_player_gold(telegram_id, gold)
            return f"\n💰 Найдено {gold} золота среди верёвок!"
        except Exception:
            return ""
    elif effect == "forced_retreat":
        return "\n📍 Ты вернулся на шаг назад."
    return ""
