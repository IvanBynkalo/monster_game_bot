from aiogram.types import Message

from database.repositories import (
    add_captured_monster,
    add_player_experience,
    add_player_gold,
    clear_pending_encounter,
    damage_active_monster,
    get_active_monster,
    get_pending_encounter,
    get_player,
    progress_quests,
    save_pending_encounter,
)
from game.district_service import get_district
from game.emotion_birth_service import render_birth_text, try_birth_emotional_monster
from game.emotion_service import grant_event_emotions, render_emotion_changes
from game.encounter_service import resolve_attack, resolve_capture, resolve_flee
from game.infection_service import apply_dominant_emotion_infection, render_infection_update
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
    hp_text = f"❤️ Твой активный монстр получает {damage} урона. Текущее HP: {monster['current_hp']}/{monster['max_hp']}"
    if monster["current_hp"] <= 0:
        hp_text += "\n☠️ Активный монстр повержен. Лечи его перед следующими тяжёлыми боями."
    return monster, hp_text

def _append_progression(player_id, base_text, reward_result, district_mood, emotion_key):
    parts = [base_text]

    gold = reward_result.get("gold", 0)
    exp = reward_result.get("exp", 0)

    if gold:
        add_player_gold(player_id, gold)
        parts.append(f"💰 Золото: +{gold}")

    if exp:
        player = add_player_experience(player_id, exp)
        parts.append(f"✨ Опыт: +{exp}")
        if player:
            parts.append(f"📈 Уровень: {player.level}")

    _, changes = grant_event_emotions(player_id, emotion_key, district_mood=district_mood)
    emotion_text = render_emotion_changes(changes)
    if emotion_text:
        parts.append(emotion_text)

    infection_update = apply_dominant_emotion_infection(player_id)
    infection_text = render_infection_update(infection_update)
    if infection_text:
        parts.append(infection_text)

    born = try_birth_emotional_monster(player_id)
    birth_text = render_birth_text(born)
    if birth_text:
        log_event("emotion_birth", player_id, born["name"])
        parts.append(birth_text)

    return "\n\n".join(parts)

def _render_completed_quests(player_id: int, completed_now):
    parts = []
    for _, quest in completed_now:
        add_player_gold(player_id, quest["reward_gold"])
        add_player_experience(player_id, quest["reward_exp"])
        parts.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )
    return parts

async def attack_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра.")
        return
    if active.get("current_hp", active.get("hp", 1)) <= 0:
        await message.answer("☠️ Активный монстр повержен. Используй ❤️ Лечить монстра.")
        return

    encounter = get_pending_encounter(message.from_user.id)
    if not encounter:
        await message.answer("Сейчас нет активной встречи.")
        return

    result = resolve_attack(encounter, active_monster_attack=active.get("attack", 8))
    damaged_monster, damage_text = _apply_enemy_damage(message.from_user.id, result)

    if damaged_monster and damaged_monster["current_hp"] <= 0 and not result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        log_event("battle_lost_monster_down", message.from_user.id, encounter.get("monster_name", "unknown"))
        await message.answer(
            result["text"] + "\n\n" + damage_text + "\n\nБой прерван: твой монстр больше не может продолжать.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        log_event("battle_win", message.from_user.id, encounter.get("monster_name", "unknown"))
        text = _append_progression(
            message.from_user.id, result["text"], result, _district_mood_from_player(player), "battle_win"
        )
        quest_parts = _render_completed_quests(message.from_user.id, progress_quests(message.from_user.id, "win"))
        if damage_text:
            text += "\n\n" + damage_text
        if quest_parts:
            text += "\n\n" + "\n\n".join(quest_parts)
        await message.answer(text, reply_markup=main_menu(player.location_slug))
        return

    save_pending_encounter(message.from_user.id, encounter)
    text = result["text"]
    if damage_text:
        text += "\n\n" + damage_text
    await message.answer(text, reply_markup=encounter_menu())

async def capture_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра.")
        return
    if active.get("current_hp", active.get("hp", 1)) <= 0:
        await message.answer("☠️ Активный монстр повержен. Используй ❤️ Лечить монстра.")
        return

    encounter = get_pending_encounter(message.from_user.id)
    if not encounter:
        await message.answer("Сейчас нет активной встречи.")
        return

    result = resolve_capture(encounter)
    damaged_monster, damage_text = _apply_enemy_damage(message.from_user.id, result)

    if damaged_monster and damaged_monster["current_hp"] <= 0 and not result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        log_event("capture_failed_monster_down", message.from_user.id, encounter.get("monster_name", "unknown"))
        await message.answer(
            result["text"] + "\n\n" + damage_text + "\n\nПопытка сорвалась: твой монстр не может продолжать.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        captured_monster = add_captured_monster(
            telegram_id=message.from_user.id,
            name=encounter["monster_name"],
            rarity=encounter["rarity"],
            mood=encounter["mood"],
            hp=max(1, encounter["hp"]),
            attack=encounter["attack"],
        )
        log_event("capture_success", message.from_user.id, captured_monster["name"])
        text = _append_progression(
            message.from_user.id, result["text"], result, _district_mood_from_player(player), "capture_success"
        )
        text += f"\n\n🐲 Монстр добавлен в коллекцию: {captured_monster['name']}\nID: {captured_monster['id']}"
        quest_parts = _render_completed_quests(message.from_user.id, progress_quests(message.from_user.id, "capture"))
        if damage_text:
            text += "\n\n" + damage_text
        if quest_parts:
            text += "\n\n" + "\n\n".join(quest_parts)
        await message.answer(text, reply_markup=main_menu(player.location_slug))
        return

    save_pending_encounter(message.from_user.id, encounter)
    text = result["text"]
    if damage_text:
        text += "\n\n" + damage_text
    await message.answer(text, reply_markup=encounter_menu())

async def flee_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра.")
        return

    encounter = get_pending_encounter(message.from_user.id)
    if not encounter:
        await message.answer("Сейчас нет активной встречи.")
        return

    result = resolve_flee(encounter)
    damaged_monster, damage_text = _apply_enemy_damage(message.from_user.id, result)

    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        log_event("flee", message.from_user.id, encounter.get("monster_name", "unknown"))
        text = _append_progression(
            message.from_user.id, result["text"], result, _district_mood_from_player(player), "flee_success"
        )
        if damage_text:
            text += "\n\n" + damage_text
        await message.answer(text, reply_markup=main_menu(player.location_slug))
        return

    if damaged_monster and damaged_monster["current_hp"] <= 0:
        clear_pending_encounter(message.from_user.id)
        log_event("flee_monster_down", message.from_user.id, encounter.get("monster_name", "unknown"))
        await message.answer(
            result["text"] + "\n\n" + damage_text + "\n\nТебе удалось вырваться, но активный монстр повержен.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    save_pending_encounter(message.from_user.id, encounter)
    text = result["text"]
    if damage_text:
        text += "\n\n" + damage_text
    await message.answer(text, reply_markup=encounter_menu())
