EVOLUTION_RECIPES = {
    ("stone_beetle", "rage", 3): "crimson_beetle",
}

def try_evolution(player_monster: dict):
    key = (
        player_monster.get("monster_slug"),
        player_monster.get("infection_type"),
        player_monster.get("infection_stage"),
    )
    return EVOLUTION_RECIPES.get(key)
