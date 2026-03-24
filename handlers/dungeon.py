from aiogram.types import Message

from database.repositories import (
    add_active_monster_experience,
    add_item,
    add_player_experience,
    add_player_gold,
    damage_active_monster,
    defeat_player_state,
    get_active_monster,
    get_player,
    get_ui_state,
    heal_active_monster,
    restore_player_energy,
    set_ui_screen,
    spend_player_energy,
)
from game.dungeon_service import (
    generate_room,
    get_dungeon,
    render_dungeon_state,
    render_dungeon_summary,
    render_item_rewards,
    start_dungeon_state,
)
from game.player_survival_service import render_injury_warning
from keyboards.dungeon_menu import dungeon_menu
from keyboards.main_menu import main_menu
from utils.images import send_dungeon_image


def _get_dungeon_state(player):
    ui = get_ui_state(player.telegram_id)
    return ui.get("context", {}).get("dungeon_state")


def _set_dungeon_state(player, state):
    set_ui_screen(player.telegram_id, "dungeon", dungeon_state=state)


def _clear_dungeon_state(player):
    set_ui_screen(player.telegram_id, "main")


def _add_summary_items(state: dict, items: dict):
    summary_items = state["summary"].setdefault("items", {})
    for slug, amount in items.items():
        summary_items[slug] = summary_items.get(slug, 0) + amount


async def dungeon_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if player.is_defeated:
        await message.answer(
            "☠️ Герой повержен. Сначала вылечи его в городе.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    if getattr(player, "injury_turns", 0) > 0:
        await message.answer(
            render_injury_warning(player),
            reply_markup=main_menu(player.location_slug),
        )
        return

    dungeon = get_dungeon(player.location_slug)
    if not dungeon:
        await message.answer(
            "В этой локации подземелье пока недоступно.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    from game.grid_exploration_service import THRESHOLDS, is_dungeon_available

    if not is_dungeon_available(message.from_user.id, player.location_slug):
        await message.answer(
            f"🔒 Вход в подземелье ещё не найден.\n"
            f"Исследуй локацию до {THRESHOLDS['dungeon_unlocks']}% — тогда найдёшь вход.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    if not spend_player_energy(message.from_user.id, 2):
        await message.answer(
            "⚡ Для входа в подземелье нужно 2 энергии.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    state = start_dungeon_state(player.location_slug)
    _set_dungeon_state(player, state)

    entry_text = (
        f"🕳 Ты входишь в подземелье: {state['name']}\n"
        f"Потрачено энергии: 2\n"
        f"Внутри тебя ждут {state['rooms_total']} комнат.\n\n"
        f"В этот раз путь не будет состоять только из тайников: встречаются бои, ловушки и опасные залы."
    )

    await send_dungeon_image(
        message,
        player.location_slug,
        entry_text,
        reply_markup=dungeon_menu(),
    )


async def dungeon_next_room_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    state = _get_dungeon_state(player)
    if not state:
        await message.answer(
            "Сейчас ты не в подземелье.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    if state.get("completed"):
        await message.answer(
            "🏁 Подземелье уже зачищено. Осталось только спокойно выйти наружу.",
            reply_markup=dungeon_menu(completed=True),
        )
        return

    current_room = state.get("current_room")
    if current_room and current_room.get("type") in {"combat", "elite", "boss"}:
        await message.answer(
            "⚔️ Сначала закончи бой или покинь подземелье.",
            reply_markup=dungeon_menu(current_room["type"]),
        )
        return

    if state["room_index"] >= state["rooms_total"]:
        state["completed"] = True
        _set_dungeon_state(player, state)
        await message.answer(
            render_dungeon_summary(state),
            reply_markup=dungeon_menu(completed=True),
        )
        return

    room = generate_room(state)
    state["room_index"] += 1
    state["current_room"] = room
    state["summary"]["rooms_cleared"] += 1
    _set_dungeon_state(player, state)

    if room["type"] == "treasure":
        add_player_gold(message.from_user.id, room["gold"])
        state["summary"]["gold"] += room["gold"]
        for item_slug, amount in room["items"].items():
            add_item(message.from_user.id, item_slug, amount)
        _add_summary_items(state, room["items"])
        state["current_room"] = None
        _set_dungeon_state(player, state)

        await message.answer(
            render_dungeon_state({**state, "current_room": room})
            + f"\n\n💰 +{room['gold']} золота\n🎒 Найдено:\n{render_item_rewards(room['items'])}",
            reply_markup=dungeon_menu(),
        )
        return

    if room["type"] == "rest":
        heal_text = ""
        monster = get_active_monster(message.from_user.id)
        if monster:
            before = monster["current_hp"]
            healed = heal_active_monster(message.from_user.id, room["heal"])
            if healed:
                restored = healed["current_hp"] - before
                if restored > 0:
                    heal_text = f"\n❤️ Восстановлено HP: +{restored}"
        restore_player_energy(message.from_user.id, room["energy"], max_energy=12)
        state["current_room"] = None
        _set_dungeon_state(player, state)
        await message.answer(
            render_dungeon_state({**state, "current_room": room}) + heal_text + f"\n⚡ Энергия: +{room['energy']}",
            reply_markup=dungeon_menu(),
        )
        return

    if room["type"] == "event":
        add_player_gold(message.from_user.id, room["reward_gold"])
        add_player_experience(message.from_user.id, room["reward_exp"])
        state["summary"]["gold"] += room["reward_gold"]
        state["summary"]["exp"] += room["reward_exp"]
        state["current_room"] = None
        _set_dungeon_state(player, state)
        await message.answer(
            render_dungeon_state({**state, "current_room": room})
            + f"\n\n💰 +{room['reward_gold']} золота\n✨ +{room['reward_exp']} опыта",
            reply_markup=dungeon_menu(),
        )
        return

    if room["type"] == "trap":
        damage_active_monster(message.from_user.id, room["damage"])
        state["summary"]["traps_triggered"] += 1
        state["current_room"] = None
        active = get_active_monster(message.from_user.id)
        hp_line = ""
        if active:
            hp_line = f"\n🩸 HP активного монстра: {active['current_hp']}/{active['max_hp']}"
        _set_dungeon_state(player, state)
        await message.answer(
            render_dungeon_state({**state, "current_room": room})
            + f"\n\n🪤 Ловушка наносит {room['damage']} урона.{hp_line}",
            reply_markup=dungeon_menu(),
        )
        return

    await message.answer(
        render_dungeon_state(state),
        reply_markup=dungeon_menu(room["type"]),
    )


async def dungeon_fight_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    state = _get_dungeon_state(player)
    if not state:
        await message.answer(
            "Сейчас ты не в подземелье.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    room = state.get("current_room")
    if not room or room["type"] not in {"combat", "elite", "boss"}:
        await message.answer(
            "Сейчас не с кем сражаться в подземелье.",
            reply_markup=dungeon_menu(completed=state.get("completed", False)),
        )
        return

    active = get_active_monster(message.from_user.id)
    if not active:
        await message.answer(
            "У тебя нет активного монстра.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    if active["current_hp"] <= 0:
        await message.answer(
            "☠️ Активный монстр повержен. Сначала вылечи его.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    enemy = room["enemy"]
    base_damage = max(5, active.get("attack", 6))
    if room["type"] == "elite":
        retaliation = max(6, enemy["attack"] // 2 + 1)
    elif room["type"] == "boss":
        retaliation = max(7, enemy["attack"] // 2 + 1)
    else:
        retaliation = max(4, enemy["attack"] // 2)

    enemy["hp"] = max(0, enemy["hp"] - base_damage)

    if enemy["hp"] <= 0:
        add_player_gold(message.from_user.id, enemy["reward_gold"])
        add_player_experience(message.from_user.id, enemy["reward_exp"])
        add_active_monster_experience(message.from_user.id, max(4, enemy["reward_exp"] // 2))

        state["summary"]["gold"] += enemy["reward_gold"]
        state["summary"]["exp"] += enemy["reward_exp"]
        state["summary"]["enemies_defeated"] += 1
        state["current_room"] = None

        if room["type"] == "boss":
            state["completed"] = True
            _set_dungeon_state(player, state)
            await message.answer(
                f"👑 Босс повержен: {enemy['name']}\n"
                f"💰 +{enemy['reward_gold']} золота\n"
                f"✨ +{enemy['reward_exp']} опыта\n\n"
                f"{render_dungeon_summary(state)}\n\n"
                f"🚪 Теперь можно спокойно покинуть подземелье.",
                reply_markup=dungeon_menu(completed=True),
            )
            return

        _set_dungeon_state(player, state)
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

    if active and active["current_hp"] <= 0:
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

    _set_dungeon_state(player, state)
    enemy_tag = "💀 Элитный враг" if room["type"] == "elite" else "👑 Босс" if room["type"] == "boss" else "⚔️ Враг"
    await message.answer(
        f"⚔️ Ты наносишь {base_damage} урона.\n"
        f"{enemy_tag}: {enemy['name']}\n"
        f"У врага осталось: {enemy['hp']} HP\n"
        f"Ответный удар: {retaliation}\n"
        f"HP твоего монстра: {active['current_hp']}/{active['max_hp']}",
        reply_markup=dungeon_menu(room["type"]),
    )


async def dungeon_leave_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    state = _get_dungeon_state(player)
    if not state:
        await message.answer(
            "Ты сейчас не в подземелье.",
            reply_markup=main_menu(player.location_slug),
        )
        return

    summary_text = ""
    if state.get("completed"):
        summary_text = "\n\n" + render_dungeon_summary(state)

    _clear_dungeon_state(player)
    await message.answer(
        "🏃 Ты покидаешь подземелье и возвращаешься наружу." + summary_text,
        reply_markup=main_menu(player.location_slug),
    )
