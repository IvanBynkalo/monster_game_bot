"""
hunting_recipes.py — Рецепты крафта из охотничьего лута.
Привязаны к уровню игрока.
"""

HUNTING_RECIPES = [
    # ── Уровень 1-2 ──────────────────────────────────────────────────────────
    {
        "id": "simple_amulet",
        "name": "🪬 Простой амулет",
        "description": "+2 к атаке монстра в бою",
        "min_level": 1,
        "ingredients": [("fox_fur", 2), ("silver_moss", 1)],
        "gold_cost": 20,
        "result_item": "simple_amulet",
        "result_count": 1,
        "effect": {"atk_bonus": 2},
    },
    {
        "id": "travel_bag_patch",
        "name": "🎒 Заплатка для сумки",
        "description": "+2 места в инвентаре",
        "min_level": 1,
        "ingredients": [("rabbit_pelt", 3), ("wolf_hide", 1)],
        "gold_cost": 30,
        "result_item": "bag_patch",
        "result_count": 1,
        "effect": {"bag_bonus": 2},
    },
    # ── Уровень 3-4 ──────────────────────────────────────────────────────────
    {
        "id": "fang_necklace",
        "name": "🦷 Клыковое ожерелье",
        "description": "+5 к атаке монстра. Носится в бою.",
        "min_level": 3,
        "ingredients": [("wolf_fang", 2), ("deer_antler", 1), ("fox_fur", 1)],
        "gold_cost": 60,
        "result_item": "fang_necklace",
        "result_count": 1,
        "effect": {"atk_bonus": 5},
    },
    {
        "id": "venom_trap",
        "name": "🐍 Ядовитая ловушка (улучш.)",
        "description": "Наносит 18 урона + замедление",
        "min_level": 3,
        "ingredients": [("snake_venom", 2), ("frog_slime", 2)],
        "gold_cost": 45,
        "result_item": "poison_trap",
        "result_count": 2,
        "effect": {},
    },
    # ── Уровень 5-6 ──────────────────────────────────────────────────────────
    {
        "id": "hunters_cloak",
        "name": "🧥 Охотничий плащ",
        "description": "+20% к шансу побега от зверей",
        "min_level": 5,
        "ingredients": [("wolf_hide", 2), ("bear_hide", 1), ("eagle_feather", 1)],
        "gold_cost": 120,
        "result_item": "hunters_cloak",
        "result_count": 1,
        "effect": {"flee_bonus": 0.20},
    },
    {
        "id": "beast_trap",
        "name": "🪤 Звериная ловушка",
        "description": "Наносит 25 урона зверям",
        "min_level": 5,
        "ingredients": [("boar_tusk", 2), ("lynx_claw", 1), ("goat_horn", 1)],
        "gold_cost": 80,
        "result_item": "beast_trap",
        "result_count": 2,
        "effect": {},
    },
    # ── Уровень 8+ ───────────────────────────────────────────────────────────
    {
        "id": "fur_armor",
        "name": "🛡 Броня из шкур",
        "description": "Снижает урон от зверей на 30%",
        "min_level": 8,
        "ingredients": [("bear_hide", 2), ("mountain_lion_pelt", 1), ("giant_bark", 1)],
        "gold_cost": 200,
        "result_item": "fur_armor",
        "result_count": 1,
        "effect": {"beast_def": 0.30},
    },
    {
        "id": "fire_amulet_advanced",
        "name": "🔥 Огненный амулет (улучш.)",
        "description": "+10 к атаке, иммунитет к огненным эффектам",
        "min_level": 8,
        "ingredients": [("fire_lizard_skin", 2), ("magma_boar_tusk", 1), ("lava_wolf_fang", 1)],
        "gold_cost": 300,
        "result_item": "fire_amulet_advanced",
        "result_count": 1,
        "effect": {"atk_bonus": 10, "fire_immune": True},
    },
    {
        "id": "master_hunters_kit",
        "name": "🎯 Набор мастера охоты",
        "description": "+15% к шансу поимки любого существа",
        "min_level": 10,
        "ingredients": [
            ("eagle_feather", 2), ("mountain_lion_pelt", 1),
            ("croc_scale", 2), ("giant_bark", 1),
        ],
        "gold_cost": 500,
        "result_item": "master_hunters_kit",
        "result_count": 1,
        "effect": {"capture_bonus": 0.15},
    },
]


def get_available_recipes(player_level: int) -> list[dict]:
    """Возвращает рецепты доступные игроку по уровню."""
    return [r for r in HUNTING_RECIPES if r["min_level"] <= player_level]


def get_recipe(recipe_id: str) -> dict | None:
    return next((r for r in HUNTING_RECIPES if r["id"] == recipe_id), None)


def can_craft(recipe: dict, resources: dict, gold: int) -> tuple[bool, str]:
    """Проверяет может ли игрок скрафтить предмет."""
    for slug, amount in recipe["ingredients"]:
        if resources.get(slug, 0) < amount:
            from game.wildlife_loot import WILDLIFE_LOOT_ITEMS
            item_name = WILDLIFE_LOOT_ITEMS.get(slug, {}).get("name", slug)
            have = resources.get(slug, 0)
            return False, f"Нужно {item_name}: {amount} (у тебя {have})"
    if gold < recipe["gold_cost"]:
        return False, f"Нужно {recipe['gold_cost']} золота (у тебя {gold})"
    return True, ""
