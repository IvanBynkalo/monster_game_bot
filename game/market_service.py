RESOURCE_PRICES = {
    "forest_herb": 6,
    "mushroom_cap": 7,
    "silver_moss": 24,
    "swamp_moss": 8,
    "toxic_spore": 11,
    "black_pearl": 28,
    "ember_stone": 10,
    "ash_leaf": 9,
    "magma_core": 35,
    "field_grass": 6,
    "sun_blossom": 9,
    "dew_crystal": 26,
    "raw_ore": 10,
    "granite_shard": 8,
    "sky_crystal": 30,
    "bog_flower": 9,
    "dark_resin": 11,
    "ghost_reed": 32,
}

def get_resource_sell_price(slug: str, merchant_level: int = 1, amount: int = 1) -> int:
    base = RESOURCE_PRICES.get(slug, 5) * amount
    bonus = 1 + max(0, merchant_level - 1) * 0.05
    return max(1, int(round(base * bonus)))
