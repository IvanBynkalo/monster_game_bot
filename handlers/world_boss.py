from aiogram.types import Message

from database.repositories import (
    add_active_monster_experience,
    add_player_experience,
    add_player_gold,
    clear_pending_encounter,
    damage_active_monster,
    defeat_player_state,
    get_active_monster,
    get_pending_encounter,
    get_player,
    save_pending_encounter,
)
from keyboards.encounter_menu import encounter_menu, encounter_inline_menu
from game.monster_abilities import get_attack_bonus, mitigate_incoming_damage, try_regeneration
from game.evolution_service import render_evolution_text, try_evolve_active_monster
from keyboards.main_menu import main_menu
from keyboards.location_menu import location_actions_inline
from game.dungeon_service import DUNGEONS

async def boss_attack_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.is_defeated:
        await message.answer("☠️ Герой повержен. Сначала вылечи его.", reply_markup=main_menu(player.location_slug))
        return
    encounter = get_pending_encounter(message.from_user.id)
    if not encounter or encounter.get("type") != "world_boss":
        await message.answer("Сейчас нет активного мирового босса.")
        return
    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра.")
        return
    if active.get("current_hp", active.get("hp", 1)) <= 0:
        await message.answer("Активный монстр повержен.")
        return

    attack_bonus = get_attack_bonus(active, encounter)
    damage = max(4, active.get("attack", 6) + attack_bonus)
    encounter["hp"] = max(0, encounter["hp"] - damage)

    retaliation = max(5, encounter.get("attack", 12) // 2)
    final_retaliation, ability_text = mitigate_incoming_damage(active, retaliation)
    damage_active_monster(message.from_user.id, final_retaliation)
    active = get_active_monster(message.from_user.id)
    regen = try_regeneration(active) if active else 0

    if encounter["hp"] <= 0:
        clear_pending_encounter(message.from_user.id)
        add_player_gold(message.from_user.id, encounter.get("reward_gold", 80))
        add_player_experience(message.from_user.id, encounter.get("reward_exp", 30))
        add_active_monster_experience(message.from_user.id, max(8, encounter.get("reward_exp", 30) // 2))
        evolved = try_evolve_active_monster(message.from_user.id)
        evo_text = render_evolution_text(evolved)
        await message.answer(
            f"👑 Ты победил мирового босса: {encounter['name']}\n"
            f"💰 Награда: +{encounter.get('reward_gold', 80)} золота\n"
            f"✨ Награда: +{encounter.get('reward_exp', 30)} опыта"
            + (f"\n\n{evo_text}" if evo_text else ""),
            reply_markup=main_menu(player.location_slug),
        )
        await message.answer(
            "Что делать:",
            reply_markup=location_actions_inline(
                player.location_slug,
                has_dungeon=player.location_slug in DUNGEONS
            )
        )
        return

    save_pending_encounter(message.from_user.id, encounter)
    if active and active["current_hp"] <= 0:
        gold_loss = min(30, max(10, player.gold // 10))
        defeat_player_state(message.from_user.id, gold_loss)
        await message.answer(
            f"☠️ Твой монстр пал в бою с мировым боссом.\n"
            f"Герой повержен и отступает.\n"
            f"Потеряно золота: {gold_loss}",
            reply_markup=main_menu("silver_city"),
        )
        return

    await message.answer(
        f"⚔️ Ты наносишь {damage} урона боссу {encounter['name']}\n"
        f"Осталось HP босса: {encounter['hp']}\n"
        f"Ответный удар: {final_retaliation}\n"
        + (f"{ability_text}\n" if ability_text else "")
        + (f"💚 Регенерация: +{regen} HP\n" if regen else "")
        + f"HP твоего монстра: {active['current_hp']}/{active['max_hp']}",
        reply_markup=encounter_inline_menu(has_trap=False, has_poison_trap=False),
    )

async def boss_flee_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.is_defeated:
        await message.answer("☠️ Герой повержен. Сначала вылечи его.", reply_markup=main_menu(player.location_slug))
        return
    encounter = get_pending_encounter(message.from_user.id)
    if not encounter or encounter.get("type") != "world_boss":
        await message.answer("Сейчас нет активного мирового босса.")
        return
    clear_pending_encounter(message.from_user.id)
    await message.answer(
        "🏃 Ты отступаешь от мирового босса и спасаешься.",
        reply_markup=main_menu(player.location_slug)
    )
    await message.answer(
        "Что делать:",
        reply_markup=location_actions_inline(
            player.location_slug,
            has_dungeon=player.location_slug in DUNGEONS
        )
    )
