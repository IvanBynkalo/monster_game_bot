import random

DISTRICT_POOLS = {
    "mushroom_path": {
        "monsters": [
            {"name": "Споровый слизень", "rarity": "common", "mood": "fear", "weight": 40},
            {"name": "Лесной глазун", "rarity": "common", "mood": "fear", "weight": 30},
            {"name": "Моховой шептун", "rarity": "rare", "mood": "inspiration", "weight": 15},
            {"name": "Грибной сторож", "rarity": "rare", "mood": "fear", "weight": 10},
            {"name": "Сумеречный плодник", "rarity": "epic", "mood": "fear", "weight": 5},
        ],
        "events": [
            {"type": "anomaly", "text": "Ты замечаешь грибной круг. Воздух внутри него дрожит от страха.", "weight": 20},
            {"type": "trail", "text": "На земле видны следы маленьких лап. Кто-то наблюдает за тобой.", "weight": 15},
        ],
    },
    "wet_thicket": {
        "monsters": [
            {"name": "Корнехват", "rarity": "common", "mood": "fear", "weight": 35},
            {"name": "Тенелист", "rarity": "rare", "mood": "fear", "weight": 25},
            {"name": "Сырой охотник", "rarity": "rare", "mood": "instinct", "weight": 20},
            {"name": "Влажный дух", "rarity": "epic", "mood": "inspiration", "weight": 10},
            {"name": "Страж чащи", "rarity": "epic", "mood": "fear", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Чаща на миг сжимается вокруг тебя, будто реагирует на твои эмоции.", "weight": 18},
            {"type": "cache", "text": "Под корнями спрятано старое гнездо. Возможно, здесь кто-то линял.", "weight": 12},
        ],
    },
    "whisper_den": {
        "monsters": [
            {"name": "Шепчущий зрачок", "rarity": "rare", "mood": "fear", "weight": 30},
            {"name": "Корневой пророк", "rarity": "epic", "mood": "inspiration", "weight": 20},
            {"name": "Тревожный скользень", "rarity": "rare", "mood": "fear", "weight": 25},
            {"name": "Безликий слухач", "rarity": "epic", "mood": "fear", "weight": 15},
            {"name": "Сердце Шёпота", "rarity": "legendary", "mood": "fear", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Шёпот становится слишком понятным. Он произносит имя твоего активного монстра.", "weight": 24},
            {"type": "rift", "text": "Среди корней мерцает трещина. Кажется, эмоции здесь могут обрести форму.", "weight": 10},
        ],
    },
    "black_water": {
        "monsters": [
            {"name": "Зеркальный пиявец", "rarity": "common", "mood": "fear", "weight": 35},
            {"name": "Илистый наблюдатель", "rarity": "rare", "mood": "fear", "weight": 25},
            {"name": "Болотный двойник", "rarity": "epic", "mood": "fear", "weight": 15},
            {"name": "Чёрный сомнамбул", "rarity": "rare", "mood": "inspiration", "weight": 15},
            {"name": "Топкий хранитель", "rarity": "epic", "mood": "fear", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Вода показывает не твоё отражение, а неизвестного монстра.", "weight": 20},
            {"type": "echo", "text": "Ты слышишь плеск далеко в стороне. Возможно, это кто-то большой.", "weight": 14},
        ],
    },
    "fog_trail": {
        "monsters": [
            {"name": "Туманник", "rarity": "common", "mood": "fear", "weight": 35},
            {"name": "Скользящий силуэт", "rarity": "rare", "mood": "fear", "weight": 25},
            {"name": "Слепой следопыт", "rarity": "rare", "mood": "instinct", "weight": 20},
            {"name": "Дымчатый оракул", "rarity": "epic", "mood": "inspiration", "weight": 10},
            {"name": "Туманная пасть", "rarity": "epic", "mood": "fear", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Туман уплотняется в фигуру и тут же распадается. Район резонирует со страхом.", "weight": 18},
            {"type": "trail", "text": "На грязи отпечатки когтей. Они внезапно обрываются.", "weight": 16},
        ],
    },
    "grave_of_voices": {
        "monsters": [
            {"name": "Курганный эхонид", "rarity": "rare", "mood": "fear", "weight": 30},
            {"name": "Погребальный мотылёк", "rarity": "rare", "mood": "inspiration", "weight": 20},
            {"name": "Голос из ила", "rarity": "epic", "mood": "fear", "weight": 20},
            {"name": "Собиратель имён", "rarity": "epic", "mood": "fear", "weight": 15},
            {"name": "Хор молчания", "rarity": "legendary", "mood": "fear", "weight": 15},
        ],
        "events": [
            {"type": "anomaly", "text": "Голоса зовут тебя ближе. На миг кажется, что один из них принадлежит тебе.", "weight": 24},
            {"type": "altar", "text": "В иле торчит старый каменный знак. Такие места любят эмоциональные сущности.", "weight": 12},
        ],
    },
    "ash_slope": {
        "monsters": [
            {"name": "Пепельный ползун", "rarity": "common", "mood": "rage", "weight": 40},
            {"name": "Искровой шакал", "rarity": "rare", "mood": "rage", "weight": 25},
            {"name": "Шлакобой", "rarity": "rare", "mood": "instinct", "weight": 20},
            {"name": "Жаровой клык", "rarity": "epic", "mood": "rage", "weight": 10},
            {"name": "Магматический крикун", "rarity": "epic", "mood": "rage", "weight": 5},
        ],
        "events": [
            {"type": "anomaly", "text": "Пепел поднимается вихрем. Ярость локации словно ищет тело.", "weight": 18},
            {"type": "cache", "text": "Среди шлака виднеется осколок панциря. Похоже, кто-то пережил мутацию.", "weight": 12},
        ],
    },
    "lava_bridge": {
        "monsters": [
            {"name": "Лавовый гончий", "rarity": "rare", "mood": "rage", "weight": 30},
            {"name": "Кипящий сторож", "rarity": "rare", "mood": "rage", "weight": 25},
            {"name": "Огнехребет", "rarity": "epic", "mood": "rage", "weight": 20},
            {"name": "Мостовой ревун", "rarity": "epic", "mood": "instinct", "weight": 15},
            {"name": "Расплавленный каратель", "rarity": "legendary", "mood": "rage", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Лава под мостом вспыхивает ярче обычного. Кажется, она реагирует на любое колебание ярости.", "weight": 20},
            {"type": "boss_sign", "text": "На краю моста следы огромных когтей. Кто-то господствует здесь.", "weight": 14},
        ],
    },
    "heart_of_magma": {
        "monsters": [
            {"name": "Ядро пламени", "rarity": "epic", "mood": "rage", "weight": 25},
            {"name": "Магмовый берсерк", "rarity": "epic", "mood": "rage", "weight": 25},
            {"name": "Кровь кратера", "rarity": "legendary", "mood": "rage", "weight": 20},
            {"name": "Фениксовый осколок", "rarity": "legendary", "mood": "inspiration", "weight": 15},
            {"name": "Сердце магмы", "rarity": "mythic", "mood": "rage", "weight": 15},
        ],
        "events": [
            {"type": "anomaly", "text": "Ядро вулкана пульсирует. Это место может усилить агрессивные мутации.", "weight": 24},
            {"type": "rift", "text": "В жарком мареве открывается разлом. В нём видно силуэт несуществующего монстра.", "weight": 12},
        ],
    },
}

RARITY_LABELS = {
    "common": "Обычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
    "mythic": "Мифический",
}

MOOD_LABELS = {
    "rage": "🔥 Ярость",
    "fear": "😱 Страх",
    "instinct": "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение",
}

RARITY_STATS = {
    "common": {"hp": 20, "attack": 5, "capture": 0.72, "gold": 5, "exp": 4},
    "rare": {"hp": 30, "attack": 7, "capture": 0.52, "gold": 9, "exp": 6},
    "epic": {"hp": 42, "attack": 10, "capture": 0.30, "gold": 14, "exp": 8},
    "legendary": {"hp": 58, "attack": 13, "capture": 0.18, "gold": 20, "exp": 12},
    "mythic": {"hp": 80, "attack": 16, "capture": 0.10, "gold": 30, "exp": 18},
}

def _weighted_choice(items):
    total = sum(item["weight"] for item in items)
    roll = random.uniform(0, total)
    current = 0
    for item in items:
        current += item["weight"]
        if roll <= current:
            return item
    return items[-1]

def generate_district_encounter(district_slug: str):
    pool = DISTRICT_POOLS.get(district_slug)
    if not pool:
        return {"type": "empty", "text": "В этом районе пока нет настроенных встреч."}

    monster = _weighted_choice(pool["monsters"])
    event = _weighted_choice(pool["events"])

    if random.random() < 0.18:
        return {
            "type": "anomaly",
            "title": "⚠️ Эмоциональная аномалия",
            "text": event["text"],
            "hint": f"Эмоция района усиливается: {MOOD_LABELS.get(monster['mood'], monster['mood'])}",
        }

    if random.random() < 0.72:
        stats = RARITY_STATS[monster["rarity"]]
        return {
            "type": "monster",
            "title": "🐾 Встреча",
            "monster_name": monster["name"],
            "rarity": monster["rarity"],
            "rarity_label": RARITY_LABELS.get(monster["rarity"], monster["rarity"]),
            "mood": monster["mood"],
            "mood_label": MOOD_LABELS.get(monster["mood"], monster["mood"]),
            "hp": stats["hp"],
            "max_hp": stats["hp"],
            "attack": stats["attack"],
            "capture_chance": stats["capture"],
            "reward_gold": stats["gold"],
            "reward_exp": stats["exp"],
            "text": f"Ты встречаешь существо: {monster['name']}",
        }

    return {
        "type": "event",
        "title": "✨ Событие района",
        "text": event["text"],
        "hint": "Здесь может скрываться особая эмоциональная реакция или редкая форма.",
    }

def render_encounter_text(encounter: dict):
    if encounter["type"] == "monster":
        return "\n".join([
            encounter["title"], "", encounter["text"],
            f"Редкость: {encounter['rarity_label']}",
            f"Эмоциональный след: {encounter['mood_label']}",
            f"HP: {encounter['hp']}/{encounter.get('max_hp', encounter['hp'])}",
            f"ATK: {encounter['attack']}", "",
            "Выбери действие: ⚔️ Атаковать / 🎯 Поймать / 🏃 Убежать",
        ])
    if encounter["type"] in {"anomaly", "event"}:
        lines = [encounter["title"], "", encounter["text"]]
        if encounter.get("hint"):
            lines.extend(["", encounter["hint"]])
        return "\n".join(lines)
    return encounter["text"]

def resolve_attack(encounter: dict, active_monster_attack: int = 10):
    if encounter["type"] != "monster":
        return {"ok": False, "text": "Здесь не на кого нападать."}
    player_attack = random.randint(max(4, active_monster_attack - 2), active_monster_attack + 3)
    encounter["hp"] -= player_attack
    if encounter["hp"] <= 0:
        return {"ok": True, "finished": True, "victory": True, "monster_defeated": True, "player_damage": 0,
                "text": f"⚔️ Ты наносишь {player_attack} урона и побеждаешь {encounter['monster_name']}!",
                "gold": encounter["reward_gold"], "exp": encounter["reward_exp"]}
    enemy_attack = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    return {"ok": True, "finished": False, "victory": False, "monster_defeated": False, "player_damage": enemy_attack,
            "text": f"⚔️ Ты наносишь {player_attack} урона.\n{encounter['monster_name']} ещё держится. Осталось HP: {encounter['hp']}/{encounter.get('max_hp', encounter['hp'])}\nВ ответ монстр атакует на {enemy_attack}."}

def resolve_capture(encounter: dict):
    if encounter["type"] != "monster":
        return {"ok": False, "text": "Здесь нечего ловить."}
    base_hp = encounter.get("max_hp", encounter["hp"])
    bonus = 0.15 if encounter["hp"] <= max(1, base_hp // 2) else 0
    chance = min(0.95, encounter["capture_chance"] + bonus)
    success = random.random() <= chance
    if success:
        return {"ok": True, "finished": True, "captured": True, "player_damage": 0,
                "text": f"🎯 Ты успешно ловишь {encounter['monster_name']}!",
                "gold": encounter["reward_gold"] // 2, "exp": encounter["reward_exp"] + 1}
    enemy_attack = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    return {"ok": True, "finished": False, "captured": False, "player_damage": enemy_attack,
            "text": f"🎯 Попытка поимки провалилась. {encounter['monster_name']} вырывается!\nВ ответ монстр атакует на {enemy_attack}."}

def resolve_flee(encounter: dict):
    if encounter["type"] != "monster":
        return {"ok": True, "finished": True, "player_damage": 0, "text": "Ты покидаешь это место."}
    success = random.random() <= 0.8
    if success:
        return {"ok": True, "finished": True, "player_damage": 0, "text": f"🏃 Ты успешно сбегаешь от {encounter['monster_name']}."}
    enemy_attack = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    return {"ok": True, "finished": False, "player_damage": enemy_attack,
            "text": f"🏃 Побег не удался. {encounter['monster_name']} успевает атаковать на {enemy_attack}."}
