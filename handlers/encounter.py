from aiogram.types import Message
from database.repositories import (
    add_active_monster_experience, add_captured_monster, add_player_experience, add_player_gold,
    clear_pending_encounter, damage_active_monster, get_active_monster, get_pending_encounter,
    get_player, progress_quests, save_pending_encounter, update_story_progress,
)
from game.district_service import get_district
from game.emotion_birth_service import render_birth_text, try_birth_emotional_monster
from game.emotion_service import grant_event_emotions, render_emotion_changes
from game.encounter_service import resolve_attack, resolve_capture, resolve_flee
from game.evolution_service import render_evolution_text, try_evolve_active_monster
from game.infection_service import apply_dominant_emotion_infection, render_infection_update
from game.skill_service import resolve_skill_use, get_active_skill_label
from game.story_service import apply_story_reward
from keyboards.encounter_menu import encounter_menu
from keyboards.main_menu import main_menu
from utils.logger import log_event

def _district_mood_from_player(player):
    district = get_district(player.location_slug, player.current_district_slug)
    return district["mood"] if district else None

def _apply_enemy_damage(player_id: int, result: dict):
    damage = result.get("player_damage", 0)
    if damage <= 0:
        return None, ""
    monster = damage_active_monster(player_id, damage)
    if not monster:
        return None, ""
    text = f"❤️ Твой активный монстр получает {damage} урона. Текущее HP: {monster['current_hp']}/{monster['max_hp']}"
    if monster["current_hp"] <= 0:
        text += "\n☠️ Активный монстр повержен. Лечи его перед следующими тяжёлыми боями."
    return monster, text

def _monster_progress_text(player_id: int, exp_amount: int):
    if exp_amount <= 0:
        return "", None
    monster, level_ups = add_active_monster_experience(player_id, exp_amount)
    if not monster:
        return "", None
    parts = [f"🐲 {monster['name']} получает +{exp_amount} опыта монстра."]
    for up in level_ups:
        parts.append(f"⬆️ Уровень монстра повышен до {up['level']}\nHP: {up['max_hp']} | ATK: {up['attack']}")
    if not level_ups:
        parts.append(f"Прогресс: {monster['experience']}/{monster['level'] * 5}")
    evolved = try_evolve_active_monster(player_id)
    return "\n".join(parts), evolved

def _append_progression(player_id, base_text, reward_result, district_mood, emotion_key):
    parts = [base_text]
    gold = reward_result.get("gold", 0)
    exp = reward_result.get("exp", 0)
    if gold:
        add_player_gold(player_id, gold)
        parts.append(f"💰 Золото: +{gold}")
    if exp:
        player = add_player_experience(player_id, exp)
        parts.append(f"✨ Опыт игрока: +{exp}")
        if player:
            parts.append(f"📈 Уровень игрока: {player.level}")
        mt, evolved = _monster_progress_text(player_id, exp)
        if mt:
            parts.append(mt)
        et = render_evolution_text(evolved)
        if et:
            log_event("monster_evolved", player_id, evolved["name"])
            parts.append(et)
    _, changes = grant_event_emotions(player_id, emotion_key, district_mood=district_mood)
    emo = render_emotion_changes(changes)
    if emo:
        parts.append(emo)
    inf = render_infection_update(apply_dominant_emotion_infection(player_id))
    if inf:
        parts.append(inf)
    evolved2 = try_evolve_active_monster(player_id)
    et2 = render_evolution_text(evolved2)
    if et2:
        log_event("monster_evolved", player_id, evolved2["name"])
        parts.append(et2)
    born = try_birth_emotional_monster(player_id)
    bt = render_birth_text(born)
    if bt:
        log_event("emotion_birth", player_id, born["name"])
        parts.append(bt)
    return "\n\n".join(parts)

def _render_completed_quests(player_id: int, completed_now):
    parts = []
    for _, quest in completed_now:
        add_player_gold(player_id, quest["reward_gold"])
        add_player_experience(player_id, quest["reward_exp"])
        mt, evolved = _monster_progress_text(player_id, quest["reward_exp"])
        text = f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта"
        if mt:
            text += "\n" + mt
        et = render_evolution_text(evolved)
        if et:
            text += "\n" + et
            log_event("monster_evolved", player_id, evolved["name"])
        parts.append(text)
    return parts

async def _handle_finished_result(message: Message, player, result: dict, emotion_key: str, damage_text: str = ""):
    text = _append_progression(message.from_user.id, result["text"], result, _district_mood_from_player(player), emotion_key)
    if emotion_key == "battle_win":
        extras = _render_completed_quests(message.from_user.id, progress_quests(message.from_user.id, "win"))
        story_done = update_story_progress(message.from_user.id, "win", player.location_slug)
        if extras:
            text += "\n\n" + "\n\n".join(extras)
        if story_done:
            text += "\n\n" + apply_story_reward(message.from_user.id, story_done)
    elif emotion_key == "capture_success":
        extras = _render_completed_quests(message.from_user.id, progress_quests(message.from_user.id, "capture"))
        if extras:
            text += "\n\n" + "\n\n".join(extras)
    if damage_text:
        text += "\n\n" + damage_text
    await message.answer(text, reply_markup=main_menu(player.location_slug))

async def attack_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start"); return
    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра."); return
    if active.get("current_hp", active.get("hp", 1)) <= 0:
        await message.answer("☠️ Активный монстр повержен. Используй ❤️ Лечить монстра."); return
    encounter = get_pending_encounter(message.from_user.id)
    if not encounter:
        await message.answer("Сейчас нет активной встречи."); return

    result = resolve_attack(encounter, active_monster_attack=active.get("attack", 8))
    damaged, damage_text = _apply_enemy_damage(message.from_user.id, result)
    if damaged and damaged["current_hp"] <= 0 and not result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        await message.answer(result["text"] + "\n\n" + damage_text + "\n\nБой прерван: твой монстр больше не может продолжать.", reply_markup=main_menu(player.location_slug))
        return
    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        await _handle_finished_result(message, player, result, "battle_win", damage_text)
        return
    save_pending_encounter(message.from_user.id, encounter)
    await message.answer(result["text"] + (("\n\n" + damage_text) if damage_text else ""), reply_markup=encounter_menu())

async def skill_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start"); return
    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра."); return
    if active.get("current_hp", active.get("hp", 1)) <= 0:
        await message.answer("☠️ Активный монстр повержен. Используй ❤️ Лечить монстра."); return
    encounter = get_pending_encounter(message.from_user.id)
    if not encounter:
        await message.answer("Сейчас нет активной встречи."); return

    result = resolve_skill_use(encounter, active)
    if not result.get("ok"):
        await message.answer(result["text"], reply_markup=encounter_menu()); return

    damaged, damage_text = _apply_enemy_damage(message.from_user.id, result)
    skill_name = get_active_skill_label(active)

    if damaged and damaged["current_hp"] <= 0 and not result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        await message.answer(result["text"] + "\n\n" + damage_text + f"\n\nНавык «{skill_name}» не спасает от поражения.", reply_markup=main_menu(player.location_slug))
        return
    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        await _handle_finished_result(message, player, result, "battle_win", damage_text)
        return

    save_pending_encounter(message.from_user.id, encounter)
    await message.answer(result["text"] + (("\n\n" + damage_text) if damage_text else ""), reply_markup=encounter_menu())

async def capture_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start"); return
    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра."); return
    if active.get("current_hp", active.get("hp", 1)) <= 0:
        await message.answer("☠️ Активный монстр повержен. Используй ❤️ Лечить монстра."); return
    encounter = get_pending_encounter(message.from_user.id)
    if not encounter:
        await message.answer("Сейчас нет активной встречи."); return

    result = resolve_capture(encounter)
    damaged, damage_text = _apply_enemy_damage(message.from_user.id, result)
    if damaged and damaged["current_hp"] <= 0 and not result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        await message.answer(result["text"] + "\n\n" + damage_text + "\n\nПопытка сорвалась: твой монстр не может продолжать.", reply_markup=main_menu(player.location_slug))
        return
    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        captured = add_captured_monster(message.from_user.id, encounter["monster_name"], encounter["rarity"], encounter["mood"], max(1, encounter["hp"]), encounter["attack"])
        text = _append_progression(message.from_user.id, result["text"], result, _district_mood_from_player(player), "capture_success")
        text += f"\n\n🐲 Монстр добавлен в коллекцию: {captured['name']}\nID: {captured['id']}"
        extras = _render_completed_quests(message.from_user.id, progress_quests(message.from_user.id, "capture"))
        if extras:
            text += "\n\n" + "\n\n".join(extras)
        if damage_text:
            text += "\n\n" + damage_text
        await message.answer(text, reply_markup=main_menu(player.location_slug))
        return
    save_pending_encounter(message.from_user.id, encounter)
    await message.answer(result["text"] + (("\n\n" + damage_text) if damage_text else ""), reply_markup=encounter_menu())

async def flee_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start"); return
    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра."); return
    encounter = get_pending_encounter(message.from_user.id)
    if not encounter:
        await message.answer("Сейчас нет активной встречи."); return

    result = resolve_flee(encounter)
    damaged, damage_text = _apply_enemy_damage(message.from_user.id, result)
    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        text = _append_progression(message.from_user.id, result["text"], result, _district_mood_from_player(player), "flee_success")
        if damage_text:
            text += "\n\n" + damage_text
        await message.answer(text, reply_markup=main_menu(player.location_slug))
        return
    if damaged and damaged["current_hp"] <= 0:
        clear_pending_encounter(message.from_user.id)
        await message.answer(result["text"] + "\n\n" + damage_text + "\n\nТебе удалось вырваться, но активный монстр повержен.", reply_markup=main_menu(player.location_slug))
        return
    save_pending_encounter(message.from_user.id, encounter)
    await message.answer(result["text"] + (("\n\n" + damage_text) if damage_text else ""), reply_markup=encounter_menu())
