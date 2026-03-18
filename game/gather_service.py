import random
from database.repositories import add_resource, get_resources_count_total, improve_profession_from_action

RESOURCES_BY_LOCATION = {
    "dark_forest": [
        {"slug": "forest_herb", "name": "🌿 Лесная трава", "kind": "gatherer", "base_chance": 1.0, "rare": False},
        {"slug": "mushroom_cap", "name": "🍄 Шляпка гриба", "kind": "gatherer", "base_chance": 0.9, "rare": False},
        {"slug": "silver_moss", "name": "✨ Серебряный мох", "kind": "gatherer", "base_chance": 0.18, "rare": True},
    ],
    "shadow_swamp": [
        {"slug": "swamp_moss", "name": "🪴 Болотный мох", "kind": "gatherer", "base_chance": 1.0, "rare": False},
        {"slug": "toxic_spore", "name": "🧫 Токсичная спора", "kind": "gatherer", "base_chance": 0.8, "rare": False},
        {"slug": "black_pearl", "name": "⚫ Чёрная жемчужина тины", "kind": "hunter", "base_chance": 0.15, "rare": True},
    ],
    "volcano_wrath": [
        {"slug": "ember_stone", "name": "🔥 Угольный камень", "kind": "geologist", "base_chance": 1.0, "rare": False},
        {"slug": "ash_leaf", "name": "🍂 Пепельный лист", "kind": "gatherer", "base_chance": 0.8, "rare": False},
        {"slug": "magma_core", "name": "💠 Ядро магмы", "kind": "geologist", "base_chance": 0.14, "rare": True},
    ],
    "emerald_fields": [
        {"slug": "field_grass", "name": "🌾 Полевая трава", "kind": "gatherer", "base_chance": 1.0, "rare": False},
        {"slug": "sun_blossom", "name": "🌼 Солнечный цветок", "kind": "gatherer", "base_chance": 0.8, "rare": False},
        {"slug": "dew_crystal", "name": "💧 Кристалл росы", "kind": "gatherer", "base_chance": 0.16, "rare": True},
    ],
    "stone_hills": [
        {"slug": "raw_ore", "name": "⛏ Сырая руда", "kind": "geologist", "base_chance": 1.0, "rare": False},
        {"slug": "granite_shard", "name": "🪨 Осколок гранита", "kind": "geologist", "base_chance": 0.85, "rare": False},
        {"slug": "sky_crystal", "name": "💎 Небесный кристалл", "kind": "geologist", "base_chance": 0.15, "rare": True},
    ],
    "shadow_marsh": [
        {"slug": "bog_flower", "name": "🪷 Болотный цветок", "kind": "gatherer", "base_chance": 0.95, "rare": False},
        {"slug": "dark_resin", "name": "🕯 Тёмная смола", "kind": "hunter", "base_chance": 0.75, "rare": False},
        {"slug": "ghost_reed", "name": "🎐 Призрачный камыш", "kind": "hunter", "base_chance": 0.14, "rare": True},
    ],
}

def gather_resource(player, location_slug):
    current_total = get_resources_count_total(player.telegram_id)
    if current_total >= player.bag_capacity:
        return {"error": f"Сумка заполнена: {current_total}/{player.bag_capacity}. Освободи место или купи новую сумку в городе."}

    pool = RESOURCES_BY_LOCATION.get(location_slug, [])
    if not pool:
        return None

    weighted = []
    for item in pool:
        chance = item["base_chance"]
        if item["kind"] == "gatherer":
            chance += 0.05 * player.gatherer_level + 0.03 * player.intellect
        elif item["kind"] == "hunter":
            chance += 0.05 * player.hunter_level + 0.03 * player.agility
        elif item["kind"] == "geologist":
            chance += 0.05 * player.geologist_level + 0.03 * player.strength
        weighted.append((chance, item))

    total = sum(max(0.01, c) for c, _ in weighted)
    roll = random.uniform(0, total)
    cur = 0
    picked = weighted[-1][1]
    for chance, item in weighted:
        cur += max(0.01, chance)
        if roll <= cur:
            picked = item
            break

    amount = 1
    if not picked["rare"]:
        if picked["kind"] == "gatherer" and player.gatherer_level >= 3 and random.random() < 0.18:
            amount = 2
        if picked["kind"] == "geologist" and player.geologist_level >= 3 and random.random() < 0.15:
            amount = 2

        add_resource(player.telegram_id, picked["slug"], amount)

    profession_gain = improve_profession_from_action(
        player.telegram_id,
        picked["kind"],
        2 if picked["rare"] else 1,
    )

    return {
        "slug": picked["slug"],
        "name": picked["name"],
        "amount": amount,
        "rare": picked["rare"],
        "kind": picked["kind"],
        "profession_gain": profession_gain,
    }
def has_gathering_in_location(location_slug: str) -> bool:
    return bool(RESOURCES_BY_LOCATION.get(location_slug))
