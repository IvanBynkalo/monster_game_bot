import random

TREASURE_TABLE = [
    {
        "id": "gold_cache",
        "title": "💰 Кошель путешественника",
        "text": "Ты находишь старый кошель с монетами.",
        "type": "gold",
        "gold": 18,
        "weight": 30,
    },
    {
        "id": "supply_box",
        "title": "📦 Ящик припасов",
        "text": "Под корнями спрятан ящик с полезными расходниками.",
        "type": "items",
        "items": {"small_potion": 1, "basic_trap": 1},
        "weight": 24,
    },
    {
        "id": "energy_satchel",
        "title": "⚡ Сумка странника",
        "text": "Внутри лежат энергетические припасы и заметки об опасных тропах.",
        "type": "items",
        "items": {"energy_capsule": 1, "spark_tonic": 1},
        "weight": 18,
    },
    {
        "id": "field_relic",
        "title": "🏺 Древний тайник",
        "text": "Ты открываешь древний тайник. Внутри — реликвия.",
        "type": "relic",
        "relic_slug": "hunter_talisman",
        "weight": 10,
    },
    {
        "id": "forest_relic",
        "title": "🌿 Сердце чащи",
        "text": "Среди мха и корней ты находишь древний лесной артефакт.",
        "type": "relic",
        "relic_slug": "forest_heart",
        "weight": 8,
    },
    {
        "id": "crystal_relic",
        "title": "💎 Хрустальный ларец",
        "text": "Внутри ларца лежит фрагмент древнего кристалла.",
        "type": "relic",
        "relic_slug": "ancient_crystal",
        "weight": 6,
    },
]

def roll_treasure():
    if random.random() > 0.22:
        return None
    total = sum(item["weight"] for item in TREASURE_TABLE)
    roll = random.randint(1, total)
    current = 0
    for item in TREASURE_TABLE:
        current += item["weight"]
        if roll <= current:
            return item.copy()
    return TREASURE_TABLE[0].copy()
