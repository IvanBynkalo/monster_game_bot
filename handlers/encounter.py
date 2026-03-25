from aiogram.types import Message
from database.repositories import (
    add_active_monster_experience, add_captured_monster, add_player_experience, add_player_gold,
    begin_action_scope, clear_pending_encounter, damage_active_monster, get_active_monster, get_item_count, get_pending_encounter,
    get_player, progress_guild_quests, progress_quests, save_pending_encounter, spend_item, tick_birth_cooldown, update_story_progress, improve_profession_from_action,
)
from game.district_service import get_district
from game.emotion_birth_service import render_birth_text, try_birth_emotional_monster
from game.emotion_service import grant_event_emotions, render_emotion_changes
from game.encounter_service import resolve_attack, resolve_capture, resolve_flee
from game.evolution_service import render_evolution_text, try_evolve_active_monster
from game.monster_abilities import get_attack_bonus, get_capture_bonus, mitigate_incoming_damage, try_regeneration
from game.infection_service import apply_dominant_emotion_infection, render_infection_update
from game.skill_service import resolve_skill_use, get_active_skill_label
from game.story_service import apply_story_reward
from game.dungeon_service import DUNGEONS
from keyboards.encounter_menu import encounter_menu, encounter_inline_menu
from keyboards.main_menu import main_menu
from keyboards.location_menu import location_actions_inline
from utils.logger import log_event
from utils.cooldown import cooldown_guard
from utils.analytics import track_battle_win, track_capture
from game.daily_service import progress_daily_tasks
from game.season_pass_service import progress_season
from game.guild_quests import progress_quest as _gq_progress

def _district_mood_from_player(player):
    district = get_district(player.location_slug, player.current_district_slug)
    return district["mood"] if district else None


def _can_store_encounter_monster(player_id: int, encounter: dict):
    """Проверяет, есть ли свободный кристалл до попытки поимки."""
    try:
        from game.crystal_service import can_receive_monster
        preview_monster = {
            "name": encounter.get("monster_name", "Неизвестный монстр"),
            "rarity": encounter.get("rarity", "common"),
            "level": encounter.get("level", 1),
            "hp": encounter.get("hp", 1),
            "max_hp": encounter.get("hp", 1),
            "attack": encounter.get("attack", 1),
            "mood": encounter.get("mood", "instinct"),
        }
        return can_receive_monster(player_id, monster=preview_monster)
    except Exception:
        return True, "", None

def _apply_enemy_damage(player_id: int, result: dict):
    damage = result.get("player_damage", 0)
    if damage <= 0:
        return None, ""
    active_before = get_active_monster(player_id)
    final_damage, ability_text = mitigate_incoming_damage(active_before, damage) if active_before else (damage, "")
    monster = damage_active_monster(player_id, final_damage)
    if not monster:
        return None, ""
    text = f"❤️ Твой активный монстр получает {final_damage} урона. Текущее HP: {monster['current_hp']}/{monster['max_hp']}"
    if ability_text:
        text += "\n" + ability_text
    healed = try_regeneration(monster)
    if healed > 0:
        text += f"\n💚 Регенерация восстанавливает {healed} HP. Теперь HP: {monster['current_hp']}/{monster['max_hp']}"
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
    # Daily/season progress for capture (рек. #12, #15)
    from game.daily_service import progress_daily_tasks as _pdt2
    from game.season_pass_service import progress_season as _ps2
    from utils.analytics import track_capture as _tc
    _pdt2(player_id, "capture")
    _ps2(player_id, "capture")
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
        monster_exp = max(1, quest["reward_exp"] // 2)
        mt, evolved = _monster_progress_text(player_id, monster_exp)
        text = f"📜 Квест выполнен: {quest['title']}\n💰 Награда: +{quest['reward_gold']} золота\n✨ Награда: +{quest['reward_exp']} опыта\n🐲 Опыт монстра за квест: +{monster_exp}"
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
        guild_done = progress_guild_quests(message.from_user.id, "capture", 1)
        try:
            guild_done += _gq_progress(
                message.from_user.id,
                "hunter",
                "capture",
                1,
                {"rarity": encounter.get("rarity"), "location": player.location_slug},
            )
            guild_done += _gq_progress(
                message.from_user.id,
                "hunter",
                "capture_rare",
                1,
                {"rarity": encounter.get("rarity"), "location": player.location_slug},
            )
            guild_done += _gq_progress(
                message.from_user.id,
                "hunter",
                "capture_rarity_exact",
                1,
                {"rarity": encounter.get("rarity"), "location": player.location_slug},
            )
        except Exception:
            pass
        if guild_done:
            extras.extend([f"📜 Квест выполнен: {q['title']}\n💰 Награда: +{q['reward_gold']} золота\n✨ Награда: +{q['reward_exp']} опыта" for q in guild_done])
            for q in guild_done:
                add_player_gold(message.from_user.id, q["reward_gold"])
                add_player_experience(message.from_user.id, q["reward_exp"])
        if extras:
            text += "\n\n" + "\n\n".join(extras)
    if damage_text:
        text += "\n\n" + damage_text
    await message.answer(text, reply_markup=main_menu(player.location_slug))

async def poison_trap_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    encounter = get_pending_encounter(message.from_user.id)
    active_monster = get_active_monster(message.from_user.id)
    if not encounter or encounter.get("type") != "monster":
        await message.answer("🪤 Ловушку можно использовать только во время встречи с монстром.", reply_markup=main_menu(player.location_slug))
        return
    if get_item_count(message.from_user.id, "poison_trap") <= 0:
        await message.answer("🪤 У тебя нет ядовитой ловушки.", reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))
        return
    spend_item(message.from_user.id, "poison_trap", 1)
    encounter["bonus_capture"] = min(0.60, encounter.get("bonus_capture", 0.0) + 0.25)
    encounter["counter_multiplier"] = 0.7
    save_pending_encounter(message.from_user.id, encounter)
    await message.answer("🪤 Ты ставишь ядовитую ловушку.\nШанс поимки повышен на 25%.\nСила ответа врага немного снижена.", reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))

async def trap_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    encounter = get_pending_encounter(message.from_user.id)
    if not encounter or encounter.get("type") != "monster":
        await message.answer("🪤 Ловушку можно использовать только во время встречи с монстром.", reply_markup=main_menu(player.location_slug))
        return
    if get_item_count(message.from_user.id, "basic_trap") <= 0:
        await message.answer("🪤 У тебя нет простой ловушки.", reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))
        return
    spend_item(message.from_user.id, "basic_trap", 1)
    encounter["bonus_capture"] = min(0.45, encounter.get("bonus_capture", 0.0) + 0.15)
    save_pending_encounter(message.from_user.id, encounter)
    await message.answer(f"🪤 Ты активируешь простую ловушку.\nШанс поимки повышен на 15%.\nТекущий бонус: +{int(encounter['bonus_capture'] * 100)}%", reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))

async def attack_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    # Антиспам (рек. #2)
    if not await cooldown_guard(message, kind="combat", seconds=1.0):
        return
    begin_action_scope(message.from_user.id, "battle_attack")
    tick_birth_cooldown(message.from_user.id)
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
    attack_bonus = get_attack_bonus(active, encounter)
    result = resolve_attack(encounter, active_monster_attack=active.get("attack", 8) + attack_bonus, attacker_type=active.get("monster_type"))
    if attack_bonus > 0:
        result["text"] += f"\n🔥 Способность усиливает атаку на {attack_bonus}."
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
    await message.answer(result["text"] + (("\n\n" + damage_text) if damage_text else ""), reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))

async def skill_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    begin_action_scope(message.from_user.id, "battle_skill")
    tick_birth_cooldown(message.from_user.id)
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
    skill_bonus = get_attack_bonus(active, encounter)
    temp_active = dict(active)
    temp_active["attack"] = temp_active.get("attack", 0) + skill_bonus
    result = resolve_skill_use(encounter, temp_active)
    if skill_bonus > 0 and result.get("ok"):
        result["text"] += f"\n🔥 Способность усиливает эффект навыка на {skill_bonus} атаки."
    if not result.get("ok"):
        await message.answer(result["text"], reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))
        return
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
    await message.answer(result["text"] + (("\n\n" + damage_text) if damage_text else ""), reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))

async def capture_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    begin_action_scope(message.from_user.id, "battle_capture")
    tick_birth_cooldown(message.from_user.id)

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

    can_store, store_msg, target_crystal = _can_store_encounter_monster(message.from_user.id, encounter)
    if not can_store:
        await message.answer(
            store_msg + "

💎 Сначала освободи место в кристаллах или купи новый кристалл в городе.",
            reply_markup=encounter_inline_menu(
                has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
                has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
            ),
        )
        return

    encounter["bonus_capture"] = encounter.get("bonus_capture", 0.0) + min(
        0.20,
        0.03 * max(0, player.hunter_level - 1) + 0.02 * max(0, player.agility - 1),
    )

    ability_capture = get_capture_bonus(active)
    encounter["bonus_capture"] += ability_capture

    result = resolve_capture(encounter)

    if ability_capture > 0:
        result["text"] += (
            f"\n🎯 Способность повышает шанс поимки ещё на {int(ability_capture * 100)}%."
        )

    damaged, damage_text = _apply_enemy_damage(message.from_user.id, result)

    if damaged and damaged["current_hp"] <= 0 and not result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        await message.answer(
            result["text"]
            + "\n\n"
            + damage_text
            + "\n\nПопытка сорвалась: твой монстр не может продолжать.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)

        # ✅ СНАЧАЛА СОЗДАЁМ
captured = add_captured_monster(
    message.from_user.id,
    encounter["monster_name"],
    encounter["rarity"],
    encounter["mood"],
    max(1, encounter["hp"]),
    encounter["attack"],
)

# ❗ СРАЗУ КЛАДЁМ В КРИСТАЛЛ (без fallback'ов)
from game.crystal_service import store_monster_in_crystal

ok, msg = store_monster_in_crystal(
    message.from_user.id,
    captured["id"],
    target_crystal["id"] if target_crystal else None
)

# ❌ ЕСЛИ НЕ УДАЛОСЬ — ОТКАТ
if not ok:
    from database.repositories import remove_player_monster
    remove_player_monster(message.from_user.id, captured["id"])

    await message.answer(
        "❌ Ошибка хранения монстра:\n" + msg
    )
    return

crystal_success = f"\n💎 Монстр помещён в кристалл: {target_crystal['name'] if target_crystal else 'кристалл'}"
crystal_warn = ""

        rarity_xp = {
            "common": 1,
            "rare": 2,
            "epic": 3,
            "legendary": 4,
        }

        hunter_gain = improve_profession_from_action(
            message.from_user.id,
            "hunter",
            rarity_xp.get(encounter.get("rarity"), 1),
        )

        text = _append_progression(
            message.from_user.id,
            result["text"],
            result,
            _district_mood_from_player(player),
            "capture_success",
        )

        text += f"\n\n🐲 Монстр добавлен в коллекцию: {captured['name']}\nID: {captured['id']}"
        if crystal_success:
            text += crystal_success
        if crystal_warn:
            text += crystal_warn

        if hunter_gain:
            if hunter_gain.get("is_max_level"):
                text += "\n🎯 Ловец: максимальный уровень."
            elif hunter_gain.get("leveled_up"):
                text += f"\n🎉 🎯 Ловец повышен до {hunter_gain['level_after']} уровня!"
            else:
                text += (
                    f"\n🎯 Ловец: +{hunter_gain['gained_exp']} опыта "
                    f"({hunter_gain['exp_after']}/{hunter_gain['exp_to_next']})"
                )

        extras = _render_completed_quests(
            message.from_user.id,
            progress_quests(message.from_user.id, "capture"),
        )

        guild_done = progress_guild_quests(message.from_user.id, "capture", 1)
        try:
            guild_done += _gq_progress(
                message.from_user.id,
                "hunter",
                "capture",
                1,
                {"rarity": encounter.get("rarity"), "location": player.location_slug},
            )
            guild_done += _gq_progress(
                message.from_user.id,
                "hunter",
                "capture_rare",
                1,
                {"rarity": encounter.get("rarity"), "location": player.location_slug},
            )
            guild_done += _gq_progress(
                message.from_user.id,
                "hunter",
                "capture_rarity_exact",
                1,
                {"rarity": encounter.get("rarity"), "location": player.location_slug},
            )
        except Exception:
            pass
        if guild_done:
            extras.extend(
                [
                    f"📜 Квест выполнен: {q['title']}\n"
                    f"💰 Награда: +{q['reward_gold']} золота\n"
                    f"✨ Награда: +{q['reward_exp']} опыта"
                    for q in guild_done
                ]
            )
            for q in guild_done:
                add_player_gold(message.from_user.id, q["reward_gold"])
                add_player_experience(message.from_user.id, q["reward_exp"])

        if extras:
            text += "\n\n" + "\n\n".join(extras)

        if damage_text:
            text += "\n\n" + damage_text

        await message.answer(
            text,
            reply_markup=main_menu(player.location_slug),
        )
        return

    save_pending_encounter(message.from_user.id, encounter)
    await message.answer(
        result["text"] + (("\n\n" + damage_text) if damage_text else ""),
        reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ),
    )
async def flee_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    begin_action_scope(message.from_user.id, "battle_flee")
    tick_birth_cooldown(message.from_user.id)
    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра.")
        return
    encounter = get_pending_encounter(message.from_user.id)
    if not encounter:
        await message.answer("Сейчас нет активной встречи.")
        return
    result = resolve_flee(encounter)
    damaged, damage_text = _apply_enemy_damage(message.from_user.id, result)
    if result.get("finished"):
        clear_pending_encounter(message.from_user.id)
        text = _append_progression(message.from_user.id, result["text"], result, _district_mood_from_player(player), "flee_success")
        if damage_text:
            text += "\n\n" + damage_text
        await message.answer(text, reply_markup=main_menu(player.location_slug))
        await message.answer(
            "Что делать:",
            reply_markup=location_actions_inline(
                player.location_slug,
                has_dungeon=player.location_slug in DUNGEONS
            )
        )
        return
    if damaged and damaged["current_hp"] <= 0:
        clear_pending_encounter(message.from_user.id)
        await message.answer(result["text"] + "\n\n" + damage_text + "\n\nТебе удалось вырваться, но активный монстр повержен.", reply_markup=main_menu(player.location_slug))
        await message.answer(
            "Что делать:",
            reply_markup=location_actions_inline(
                player.location_slug,
                has_dungeon=player.location_slug in DUNGEONS
            )
        )
        return
    save_pending_encounter(message.from_user.id, encounter)
    await message.answer(result["text"] + (("\n\n" + damage_text) if damage_text else ""), reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))
