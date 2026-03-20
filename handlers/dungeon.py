from aiogram.types import Message
from database.repositories import (
    add_active_monster_experience,
    add_item,
    add_player_experience,
    add_player_gold,
    clear_temp_effect,
    damage_active_monster,
    defeat_player_state,
    get_player,
    get_active_monster,
    get_player,
    restore_player_energy,
    set_temp_effect,
    spend_player_energy,
)
from game.dungeon_service import generate_room, get_dungeon, render_dungeon_state, start_dungeon_state
from game.player_survival_service import render_injury_warning
from keyboards.dungeon_menu import dungeon_menu
from keyboards.main_menu import main_menu

def _get_dungeon_state(player):
    flags = getattr(player, "_dungeon_flags", None)
    return flags

def _set_dungeon_state(player, state):
    player._dungeon_flags = state

def _clear_dungeon_state(player):
    if hasattr(player, "_dungeon_flags"):
        player._dungeon_flags = None

async def dungeon_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.is_defeated:
        await message.answer("☠️ Герой повержен. Сначала вылечи его в городе.", reply_markup=main_menu(player.location_slug))
        return
    if getattr(player, "injury_turns", 0) > 0:
        await message.answer(render_injury_warning(player), reply_markup=main_menu(player.location_slug))
        return
    dungeon = get_dungeon(player.location_slug)
    if not dungeon:
        await message.answer("В этой локации подземелье пока недоступно.", reply_markup=main_menu(player.location_slug))
        return
    if not spend_player_energy(message.from_user.id, 2):
        await message.answer("⚡ Для входа в подземелье нужно 2 энергии.", reply_markup=main_menu(player.location_slug))
        return
    state = start_dungeon_state(player.location_slug)
    _set_dungeon_state(player, state)
    entry_text = (
        f"🕳 Ты входишь в подземелье: {state['name']}\n"
        f"Потрачено энергии: 2\n"
        f"Внутри тебя ждут {state['rooms_total']} комнаты."
    )
    await send_dungeon_image(message, player.location_slug, entry_text,
                              reply_markup=dungeon_menu())

async def dungeon_next_room_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    state = _get_dungeon_state(player)
    if not state:
        await message.answer("Сейчас ты не в подземелье.", reply_markup=main_menu(player.location_slug))
        return
    room = generate_room(state)
    state["room_index"] += 1
    state["current_room"] = room

    if room["type"] == "treasure":
        add_player_gold(message.from_user.id, room["gold"])
        for item_slug, amount in room["items"].items():
            add_item(message.from_user.id, item_slug, amount)
        item_text = ", ".join([f"{slug} x{amount}" for slug, amount in room["items"].items()])
        await message.answer(
            render_dungeon_state(state) + f"\n\n💰 +{room['gold']} золота\n🎒 {item_text}",
            reply_markup=dungeon_menu(),
        )
        return
    if room["type"] == "rest":
        monster = get_active_monster(message.from_user.id)
        heal_text = ""
        if monster:
            before = monster["current_hp"]
            monster["current_hp"] = min(monster["max_hp"], monster["current_hp"] + room["heal"])
            heal_text = f"\n❤️ Восстановлено HP: +{monster['current_hp'] - before}"
        restore_player_energy(message.from_user.id, room["energy"], max_energy=12)
        await message.answer(
            render_dungeon_state(state) + heal_text + f"\n⚡ Энергия: +{room['energy']}",
            reply_markup=dungeon_menu(),
        )
        return
    if room["type"] == "event":
        add_player_gold(message.from_user.id, room["reward_gold"])
        add_player_experience(message.from_user.id, room["reward_exp"])
        await message.answer(
            render_dungeon_state(state) + f"\n\n💰 +{room['reward_gold']} золота\n✨ +{room['reward_exp']} опыта",
            reply_markup=dungeon_menu(),
        )
        return

    await message.answer(render_dungeon_state(state), reply_markup=dungeon_menu(room["type"]))

async def dungeon_fight_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    state = _get_dungeon_state(player)
    if not state or not state.get("current_room") or state["current_room"]["type"] not in {"combat", "boss"}:
        await message.answer("Сейчас не с кем сражаться в подземелье.", reply_markup=main_menu(player.location_slug))
        return

    room = state["current_room"]
    enemy = room["enemy"]
    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра.", reply_markup=main_menu(player.location_slug))
        return
    if active["current_hp"] <= 0:
        await message.answer("☠️ Активный монстр повержен. Сначала вылечи его.", reply_markup=main_menu(player.location_slug))
        return

    damage = max(5, active.get("attack", 6))
    enemy["hp"] = max(0, enemy["hp"] - damage)
    retaliation = max(4, enemy["attack"] // 2)

    if enemy["hp"] <= 0:
        add_player_gold(message.from_user.id, enemy["reward_gold"])
        add_player_experience(message.from_user.id, enemy["reward_exp"])
        add_active_monster_experience(message.from_user.id, max(4, enemy["reward_exp"] // 2))

        if room["type"] == "boss":
            state["completed"] = True
            _clear_dungeon_state(player)
            await message.answer(
                f"👑 Босс повержен: {enemy['name']}\n"
                f"💰 +{enemy['reward_gold']} золота\n"
                f"✨ +{enemy['reward_exp']} опыта\n\n"
                f"🕳 Подземелье пройдено!",
                reply_markup=main_menu(player.location_slug),
            )
            return

        state["current_room"] = None
        await message.answer(
            f"⚔️ Ты побеждаешь врага: {enemy['name']}\n"
            f"💰 +{enemy['reward_gold']} золота\n"
            f"✨ +{enemy['reward_exp']} опыта\n"
            f"➡️ Можно идти дальше.",
            reply_markup=dungeon_menu(),
        )
        return

    damage_active_monster(message.from_user.id, retaliation)
    active = get_active_monster(message.from_user.id)
    if active["current_hp"] <= 0:
        _clear_dungeon_state(player)
        gold_loss = min(25, max(8, player.gold // 10))
        defeat_player_state(message.from_user.id, gold_loss)
        player = get_player(message.from_user.id)
        await message.answer(
            f"☠️ {active['name']} пал в подземелье.\n"
            f"Герой тоже повержен и едва выбирается наружу.\n"
            f"Потеряно золота: {gold_loss}\n"
            f"Ты возвращаешься в Сереброград.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    await message.answer(
        f"⚔️ Ты наносишь {damage} урона.\n"
        f"У врага осталось: {enemy['hp']} HP\n"
        f"Ответный удар: {retaliation}\n"
        f"HP твоего монстра: {active['current_hp']}/{active['max_hp']}",
        reply_markup=dungeon_menu(room['type']),
    )

async def dungeon_leave_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    state = _get_dungeon_state(player)
    if not state:
        await message.answer("Ты сейчас не в подземелье.", reply_markup=main_menu(player.location_slug))
        return
    _clear_dungeon_state(player)
    await message.answer("🏃 Ты покидаешь подземелье и возвращаешься наружу.", reply_markup=main_menu(player.location_slug))
