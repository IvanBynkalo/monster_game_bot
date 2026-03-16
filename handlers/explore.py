from aiogram.types import Message
from database.repositories import add_player_experience, add_player_gold, begin_action_scope, get_player, get_active_monster, progress_quests, save_pending_encounter, spend_player_energy, tick_birth_cooldown, update_story_progress
from game.district_service import get_district, get_district_explore_text
from game.emotion_birth_service import render_birth_text, try_birth_emotional_monster
from game.emotion_service import grant_event_emotions, render_emotion_changes
from game.encounter_service import generate_district_encounter, render_encounter_text
from game.infection_service import apply_dominant_emotion_infection, render_infection_update
from game.map_service import get_location_explore_text
from game.story_service import apply_story_reward
from keyboards.encounter_menu import encounter_menu
from utils.logger import log_event

def _render_completed_quests(player_id: int, completed_now):
    parts = []
    for _, quest in completed_now:
        add_player_gold(player_id, quest["reward_gold"])
        add_player_experience(player_id, quest["reward_exp"])
        parts.append(f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта")
    return parts

async def explore_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    begin_action_scope(message.from_user.id, "explore")
    tick_birth_cooldown(message.from_user.id)
    if not spend_player_energy(message.from_user.id, 1):
        log_event("explore_failed_no_energy", message.from_user.id)
        await message.answer("⚡ Недостаточно энергии для исследования.")
        return

    completed_now = progress_quests(message.from_user.id, "explore")
    story_done = update_story_progress(message.from_user.id, "explore", player.location_slug)

    if player.current_district_slug:
        district = get_district(player.location_slug, player.current_district_slug)
        district_mood = district["mood"] if district else None
        intro = get_district_explore_text(player.location_slug, player.current_district_slug)
        encounter = generate_district_encounter(player.current_district_slug)
        active = get_active_monster(message.from_user.id)
        attacker_type = active.get("monster_type") if active else None
        log_event("explore", message.from_user.id, f"district={player.current_district_slug} type={encounter['type']}")

        if encounter["type"] == "monster":
            save_pending_encounter(message.from_user.id, encounter)
            text = f"{intro}\n\n---\n\n{render_encounter_text(encounter, attacker_type=attacker_type)}"
            extras = _render_completed_quests(message.from_user.id, completed_now)
            if story_done:
                extras.append(apply_story_reward(message.from_user.id, story_done))
            if extras:
                text += "\n\n" + "\n\n".join(extras)
            await message.answer(text, reply_markup=encounter_menu())
            return

        _, changes = grant_event_emotions(message.from_user.id, "anomaly", district_mood=district_mood)
        infection_update = apply_dominant_emotion_infection(message.from_user.id)
        born = try_birth_emotional_monster(message.from_user.id)
        parts = [f"{intro}\n\n---\n\n{render_encounter_text(encounter)}"]
        et = render_emotion_changes(changes)
        if et:
            parts.append(et)
        it = render_infection_update(infection_update)
        if it:
            parts.append(it)
        bt = render_birth_text(born)
        if bt:
            log_event("emotion_birth", message.from_user.id, born["name"])
            parts.append(bt)
        parts.extend(_render_completed_quests(message.from_user.id, completed_now))
        if story_done:
            parts.append(apply_story_reward(message.from_user.id, story_done))
        await message.answer("\n\n".join(parts))
        return

    await message.answer(get_location_explore_text(player.location_slug))
