def render_player_status(player):
    status = "☠️ Повержен" if player.is_defeated else "✅ В строю"
    injury = f"\n🩹 Травмы: {player.injury_turns} действий" if getattr(player, "injury_turns", 0) > 0 else ""
    return (
        f"❤️ HP героя: {player.hp}/{player.max_hp}\n"
        f"Состояние героя: {status}"
        f"{injury}"
    )

def defeat_player(player, gold_loss: int = 0):
    player.is_defeated = True
    player.hp = 1
    player.injury_turns = max(getattr(player, "injury_turns", 0), 5)
    if gold_loss > 0:
        player.gold = max(0, player.gold - gold_loss)
    player.location_slug = "silver_city"
    player.current_district_slug = "market_square"
    return player

def heal_player(player, amount: int):
    player.hp = min(player.max_hp, player.hp + amount)
    if player.hp > 1:
        player.is_defeated = False
    return player

def full_heal_player(player):
    player.hp = player.max_hp
    player.is_defeated = False
    player.injury_turns = 0
    return player

def damage_player(player, amount: int):
    if amount <= 0:
        return player
    player.hp = max(0, player.hp - amount)
    if player.hp <= 0:
        player.is_defeated = True
        player.injury_turns = max(getattr(player, "injury_turns", 0), 5)
    return player

def can_do_hard_activity(player):
    return not player.is_defeated and getattr(player, "injury_turns", 0) <= 0

def tick_injuries(player, amount: int = 1):
    if getattr(player, "injury_turns", 0) > 0:
        player.injury_turns = max(0, player.injury_turns - amount)
    return player.injury_turns

def render_injury_warning(player):
    if getattr(player, "injury_turns", 0) <= 0:
        return ""
    return f"🩹 Герой ещё не оправился после поражения. Осталось ограничений: {player.injury_turns} действий."
