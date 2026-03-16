from database.repositories import STORY_QUESTS, add_player_experience, add_player_gold, get_current_story_quest, get_player_story

def render_story_screen(telegram_id: int):
    story = get_player_story(telegram_id)
    current = get_current_story_quest(telegram_id)
    lines = ["🧾 Сюжет стартового региона", ""]
    if current:
        state = story[current["id"]]
        lines += [
            f"Текущая глава: {current['title']}",
            current["description"],
            f"Локация: {current['requirements']['location_slug']}",
            f"Исследования: {state['explore_count']}/{current['requirements'].get('explore_count', 0)}",
            f"Победы: {state['win_count']}/{current['requirements'].get('win_count', 0)}",
            "",
            "Завершённые главы:",
        ]
    else:
        lines += ["Все главы стартового акта пройдены.", "", "Завершённые главы:"]
    for quest in STORY_QUESTS:
        marker = "✅" if quest["id"] in story["completed_ids"] else "▫️"
        lines.append(f"{marker} {quest['title']}")
    return "\n".join(lines)

def apply_story_reward(telegram_id: int, quest: dict):
    add_player_gold(telegram_id, quest["reward_gold"])
    player = add_player_experience(telegram_id, quest["reward_exp"])
    lines = [
        f"🧾 Сюжетная глава завершена: {quest['title']}",
        f"💰 Золото: +{quest['reward_gold']}",
        f"✨ Опыт: +{quest['reward_exp']}",
        quest["reward_text"],
    ]
    if player:
        lines.append(f"📈 Уровень игрока: {player.level}")
    return "\n".join(lines)
