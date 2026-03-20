"""
trap_service.py — Мастер ловушек.

Крафт охотничьего снаряжения:
- Ловушки (базовые, ядовитые, усиленные)
- Приманки для редких зверей
- Снаряжение для монстров (пассивные бонусы в бою)
- Специальные предметы охотника

Рецепты доступны по уровню профессии Ловец.
"""

# ── Рецепты ────────────────────────────────────────────────────────────────────
TRAP_RECIPES: dict[str, dict] = {
    # Ловушки
    "basic_trap": {
        "name": "🪤 Простая ловушка",
        "desc": "−8 HP врагу, снижает контратаку на 50%. Крафт: 2 шт.",
        "ingredients": {"granite_shard": 2, "forest_herb": 1},
        "result_item": "basic_trap",
        "result_amount": 2,
        "hunter_level": 1,
        "gold_cost": 5,
        "category": "trap",
    },
    "poison_trap": {
        "name": "☠️ Ядовитая ловушка",
        "desc": "−14 HP врагу, минимальная контратака. Крафт: 1 шт.",
        "ingredients": {"swamp_moss": 1, "toxic_spore": 2},
        "result_item": "poison_trap",
        "result_amount": 1,
        "hunter_level": 2,
        "gold_cost": 10,
        "category": "trap",
    },
    "frost_trap": {
        "name": "❄️ Морозная ловушка",
        "desc": "−10 HP + враг не атакует в следующий ход.",
        "ingredients": {"dew_crystal": 1, "raw_ore": 1},
        "result_item": "frost_trap",
        "result_amount": 1,
        "hunter_level": 3,
        "gold_cost": 15,
        "category": "trap",
    },
    "blast_trap": {
        "name": "💥 Взрывная ловушка",
        "desc": "−20 HP врагу. Только для сильных зверей.",
        "ingredients": {"ember_stone": 2, "magma_core": 1},
        "result_item": "blast_trap",
        "result_amount": 1,
        "hunter_level": 5,
        "gold_cost": 25,
        "category": "trap",
    },

    # Приманки
    "forest_bait": {
        "name": "🌿 Лесная приманка",
        "desc": "+15% шанс встретить лесного зверя в следующей вылазке.",
        "ingredients": {"forest_herb": 3, "mushroom_cap": 1},
        "result_item": "forest_bait",
        "result_amount": 1,
        "hunter_level": 2,
        "gold_cost": 8,
        "category": "bait",
    },
    "rare_bait": {
        "name": "✨ Редкая приманка",
        "desc": "+25% шанс встретить редкого зверя в следующей вылазке.",
        "ingredients": {"silver_moss": 1, "dew_crystal": 1, "sky_crystal": 1},
        "result_item": "rare_bait",
        "result_amount": 1,
        "hunter_level": 4,
        "gold_cost": 30,
        "category": "bait",
    },

    # Снаряжение для монстров
    "hunter_collar": {
        "name": "🎯 Ошейник охотника",
        "desc": "+3 ATK активному монстру на 5 боёв.",
        "ingredients": {"dark_resin": 2, "granite_shard": 1},
        "result_item": "hunter_collar",
        "result_amount": 1,
        "hunter_level": 3,
        "gold_cost": 20,
        "category": "gear",
    },
    "shadow_cloak": {
        "name": "🌑 Теневой плащ",
        "desc": "+20% к поимке теневых и пустотных монстров.",
        "ingredients": {"ghost_reed": 1, "dark_resin": 2, "black_pearl": 1},
        "result_item": "shadow_cloak",
        "result_amount": 1,
        "hunter_level": 5,
        "gold_cost": 40,
        "category": "gear",
    },
    "flame_charm": {
        "name": "🔥 Огненный амулет",
        "desc": "+3 ATK против природных и костяных монстров.",
        "ingredients": {"ember_stone": 3, "magma_core": 1},
        "result_item": "flame_charm",
        "result_amount": 1,
        "hunter_level": 4,
        "gold_cost": 30,
        "category": "gear",
    },
}

CATEGORY_LABELS = {
    "trap": "🪤 Ловушки",
    "bait": "🎣 Приманки",
    "gear": "⚔️ Снаряжение",
}

ITEM_EFFECTS: dict[str, dict] = {
    "frost_trap":     {"hp_damage": 10, "skip_counter": True},
    "blast_trap":     {"hp_damage": 20},
    "forest_bait":    {"wildlife_encounter_bonus": 0.15},
    "rare_bait":      {"rare_wildlife_bonus": 0.25},
    "hunter_collar":  {"atk_bonus": 3, "duration_fights": 5},
    "shadow_cloak":   {"capture_bonus_types": ["shadow", "void"], "bonus": 0.20},
    "flame_charm":    {"atk_bonus_types": ["nature", "bone"], "bonus": 3},
}


def get_trap_recipes_for_level(hunter_level: int) -> list[dict]:
    """Рецепты доступные для уровня ловца."""
    return [
        {"slug": slug, **recipe}
        for slug, recipe in TRAP_RECIPES.items()
        if recipe["hunter_level"] <= hunter_level
    ]


def render_trap_shop(player, resources: dict) -> str:
    """Текст магазина Мастера ловушек."""
    hunter_level = getattr(player, "hunter_level", 1)
    lines = [
        "🪤 Мастер ловушек\n",
        f"💰 Твоё золото: {player.gold}",
        f"🎯 Уровень Ловца: {hunter_level}\n",
        "Выбери категорию или предмет для крафта:",
    ]

    current_cat = None
    for slug, recipe in TRAP_RECIPES.items():
        if recipe["hunter_level"] > hunter_level:
            continue
        cat = recipe["category"]
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n{CATEGORY_LABELS.get(cat, cat)}")

        can_afford = player.gold >= recipe["gold_cost"]
        has_mats = all(resources.get(r, 0) >= qty for r, qty in recipe["ingredients"].items())
        status = "✅" if (can_afford and has_mats) else "❌"
        lines.append(f"  {status} {recipe['name']} — {recipe['gold_cost']}з")
        lines.append(f"     {recipe['desc']}")

    if not any(r["hunter_level"] <= hunter_level for r in TRAP_RECIPES.values()):
        lines.append("\nПока нет доступных рецептов. Прокачай уровень Ловца!")

    return "\n".join(lines)


def craft_trap_item(player, resources: dict, slug: str) -> dict:
    """
    Пробует скрафтить предмет. 
    Возвращает {"ok": bool, "msg": str, "item": str, "amount": int}
    """
    recipe = TRAP_RECIPES.get(slug)
    if not recipe:
        return {"ok": False, "msg": "Рецепт не найден."}

    hunter_level = getattr(player, "hunter_level", 1)
    if recipe["hunter_level"] > hunter_level:
        return {"ok": False, "msg": f"Нужен уровень Ловца: {recipe['hunter_level']}."}

    if player.gold < recipe["gold_cost"]:
        return {"ok": False, "msg": f"Нужно {recipe['gold_cost']} золота."}

    for res_slug, qty in recipe["ingredients"].items():
        if resources.get(res_slug, 0) < qty:
            from game.craft_service import RESOURCE_LABELS
            res_name = RESOURCE_LABELS.get(res_slug, res_slug)
            return {"ok": False, "msg": f"Не хватает: {res_name} x{qty}."}

    return {
        "ok": True,
        "msg": f"✅ {recipe['name']} создан!",
        "item": recipe["result_item"],
        "amount": recipe["result_amount"],
        "gold_cost": recipe["gold_cost"],
        "ingredients": recipe["ingredients"],
    }
