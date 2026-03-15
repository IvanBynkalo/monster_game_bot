from database.repositories import add_captured_monster, get_active_monster

STARTER_MONSTER = {
    "name": "Эхо-Лис",
    "rarity": "rare",
    "mood": "inspiration",
    "hp": 28,
    "attack": 7,
}

def ensure_starter_monster(telegram_id: int):
    active = get_active_monster(telegram_id)
    if active:
        return active, False

    monster = add_captured_monster(
        telegram_id=telegram_id,
        name=STARTER_MONSTER["name"],
        rarity=STARTER_MONSTER["rarity"],
        mood=STARTER_MONSTER["mood"],
        hp=STARTER_MONSTER["hp"],
        attack=STARTER_MONSTER["attack"],
    )
    return monster, True
