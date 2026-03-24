import random

from aiogram.types import CallbackQuery, Message

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
    DUNGEONS,
    generate_room,
    get_dungeon,
    render_dungeon_state,
    render_dungeon_summary,
    render_item_rewards,
    start_dungeon_state,
)
from game.player_survival_service import render_injury_warning
from keyboards.dungeon_menu import dungeon_choice_menu, dungeon_menu
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


def _read_value(obj, key: str, default=0):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _get_monster_choice_bonus(active_monster, stat: str | None) -> float:
    """
    Бонус от активного монстра к выбору в подземелье.

    Логика мягкая:
    - если нужных полей нет, просто возвращается 0 или fallback на level
    - бонус ограничен, чтобы не ломать баланс
    """
    if not active_monster or not stat:
        return 0.0

    level = _read_value(active_monster, "level", 1)
    attack = _read_value(active_monster, "attack", 0)
    defense = _read_value(active_monster, "defense", 0)
    agility = _read_value(active_monster, "agility", 0)
    intellect = _read_value(active_monster, "intellect", 0)

    if stat == "strength":
        base_value = max(attack, level)
        return min(0.18, base_value * 0.015)

    if stat == "intellect":
        base_value = max(intellect, level)
        return min(0.18, base_value * 0.015)

    if stat == "agility":
        base_value = max(agility, level)
        return min(0.18, base_value * 0.015)

    if stat == "defense":
        base_value = max(defense, level)
        return min(0.18, base_value * 0.015)

    return min(0.10, level * 0.01)


def calculate_choice_chance(player, choice: dict) -> float:
    base = choice.get("base_chance", choice.get("success_chance", 0.5))
    stat = choice.get("stat")

    if not stat:
        return min(0.95, max(0.1, base))

    player_stat = getattr(player, stat, 5)
    player_bonus = player_stat * 0.03

    active_monster = get_active_monster(player.telegram_id)
    monster_bonus = _get_monster_choice_bonus(active_monster, stat)

    chance = base + player_bonus + monster_bonus
    return min(0.95, max(0.1, chance))


async def dungeon_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if player.is_defeated:
        await message.answer(
            "☠️ Герой повержен. Сначала вылечи его в городе.",
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    if getattr(player, "injury_turns", 0) > 0:
        await message.answer(
            render_injury_warning(player),
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    dungeon = get_dungeon(player.location_slug)
    if not dungeon:
        await message.answer(
            "В этой локации подземелье пока недоступно.",
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    from game.grid_exploration_service import THRESHOLDS, is_dungeon_available

    if not is_dungeon_available(message.from_user.id, player.location_slug):
        await message.answer(
            f"🔒 Вход в подземелье ещё не найден.\n"
            f"Исследуй локацию до {THRESHOLDS['dungeon_unlocks']}% — тогда найдёшь вход.",
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    if not spend_player_energy(message.from_user.id, 2):
        await message.answer(
            "⚡ Для входа в подземелье нужно 2 энергии.",
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    state = start_dungeon_state(player.location_slug)
    _set_dungeon_state(player, state)

    entry_text = (
        f"🕳 Ты входишь в подземелье: {state['name']}\n"
        f"Потрачено энергии: 2\n"
        f"Внутри тебя ждут {state['rooms_total']} комнат."
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
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    if state.get("completed"):
        await message.answer(
            "🏁 Подземелье уже зачищено. Осталось только спокойно выйти наружу.",
            reply_markup=dungeon_menu(completed=True),
        )
        return

    current_room = state.get("current_room")
    if current_room and current_room.get("type") in {
        "combat",
        "elite",
        "boss",
        "event_choice",
    }:
        if current_room["type"] == "event_choice":
            await message.answer(
                "Сначала сделай выбор в текущем событии.",
                reply_markup=dungeon_choice_menu(current_room["choices"], player),
            )
            return

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
            render_dungeon_state({**state, "current_room": room})
            + heal_text
            + f"\n⚡ Энергия: +{room['energy']}",
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
            hp_line = (
                f"\n🩸 HP активного монстра: "
                f"{active['current_hp']}/{active['max_hp']}"
            )

        _set_dungeon_state(player, state)

        await message.answer(
            render_dungeon_state({**state, "current_room": room})
            + f"\n\n🪤 Ловушка наносит {room['damage']} урона.{hp_line}",
            reply_markup=dungeon_menu(),
        )
        return

    if room["type"] == "event_choice":
        await message.answer(
            render_dungeon_state(state),
            reply_markup=dungeon_choice_menu(room["choices"], player),
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
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
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
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    if active["current_hp"] <= 0:
        await message.answer(
            "☠️ Активный монстр повержен. Сначала вылечи его.",
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
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
        add_active_monster_experience(
            message.from_user.id,
            max(4, enemy["reward_exp"] // 2),
        )

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
        fallen_name = active["name"]
        _clear_dungeon_state(player)
        gold_loss = min(25, max(8, player.gold // 10))
        defeat_player_state(message.from_user.id, gold_loss)
        player = get_player(message.from_user.id)

        await message.answer(
            f"☠️ {fallen_name} пал в подземелье.\n"
            f"Герой тоже повержен и едва выбирается наружу.\n"
            f"Потеряно золота: {gold_loss}\n"
            f"Ты возвращаешься в Сереброград.",
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    _set_dungeon_state(player, state)
    enemy_tag = (
        "💀 Элитный враг"
        if room["type"] == "elite"
        else "👑 Босс"
        if room["type"] == "boss"
        else "⚔️ Враг"
    )

    await message.answer(
        f"⚔️ Ты наносишь {base_damage} урона.\n"
        f"{enemy_tag}: {enemy['name']}\n"
        f"У врага осталось: {enemy['hp']} HP\n"
        f"Ответный удар: {retaliation}\n"
        f"HP твоего монстра: {active['current_hp']}/{active['max_hp']}",
        reply_markup=dungeon_menu(room["type"]),
    )


async def dungeon_choice_handler(callback: CallbackQuery):
    player = get_player(callback.from_user.id)
    if not player:
        await callback.answer("Сначала напиши /start", show_alert=True)
        return

    state = _get_dungeon_state(player)
    if not state:
        await callback.answer("Ты не в подземелье.", show_alert=True)
        return

    room = state.get("current_room")
    if not room or room["type"] != "event_choice":
        await callback.answer("Сейчас нет активного выбора.", show_alert=True)
        return

    choice_id = callback.data.split(":")[-1]
    choice = next((c for c in room["choices"] if c["id"] == choice_id), None)
    if not choice:
        await callback.answer("Выбор не найден.", show_alert=True)
        return

    success_chance = calculate_choice_chance(player, choice)
    success = random.random() < success_chance
    result = choice["success"] if success else choice["fail"]

    lines = [
        f"{room['title']}",
        "",
        f"Ты выбираешь: {choice['text']}",
        f"Результат: {'успех' if success else 'неудача'}",
    ]

    if result.get("text"):
        lines.extend(["", result["text"]])

    gold_reward = result.get("gold", 0)
    if gold_reward > 0:
        add_player_gold(player.telegram_id, gold_reward)
        state["summary"]["gold"] += gold_reward
        lines.append(f"💰 +{gold_reward} золота")

    exp_reward = result.get("exp", 0)
    if exp_reward > 0:
        add_player_experience(player.telegram_id, exp_reward)
        state["summary"]["exp"] += exp_reward
        lines.append(f"✨ +{exp_reward} опыта")

    items_reward = result.get("items", {})
    if items_reward:
        for item_slug, amount in items_reward.items():
            add_item(player.telegram_id, item_slug, amount)
        _add_summary_items(state, items_reward)
        lines.extend(["", "🎒 Найдено:", render_item_rewards(items_reward)])

    damage = result.get("damage", 0)
    if damage > 0:
        damage_active_monster(player.telegram_id, damage)
        state["summary"]["traps_triggered"] += 1
        lines.append(f"🩸 Получено урона: {damage}")

        active = get_active_monster(player.telegram_id)
        if active and active["current_hp"] <= 0:
            fallen_name = active["name"]
            _clear_dungeon_state(player)
            gold_loss = min(25, max(8, player.gold // 10))
            defeat_player_state(player.telegram_id, gold_loss)
            player = get_player(player.telegram_id)

            await callback.message.answer(
                f"☠️ {fallen_name} пал после рискованного выбора.\n"
                f"Герой едва выбирается из подземелья.\n"
                f"Потеряно золота: {gold_loss}",
                reply_markup=main_menu(
                    player.location_slug,
                    getattr(player, "current_district_slug", None),
                ),
            )
            await callback.answer()
            return

    state["current_room"] = None
    _set_dungeon_state(player, state)

    await callback.message.answer(
        "\n".join(lines),
        reply_markup=dungeon_menu(),
    )
    await callback.answer()


async def dungeon_leave_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    state = _get_dungeon_state(player)
    if not state:
        await message.answer(
            "Ты сейчас не в подземелье.",
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
        return

    summary_text = ""
    if state.get("completed"):
        summary_text = "\n\n" + render_dungeon_summary(state)

    _clear_dungeon_state(player)
    player = get_player(message.from_user.id)

    await message.answer(
        "🏃 Ты покидаешь подземелье и возвращаешься наружу." + summary_text,
        reply_markup=main_menu(
            player.location_slug,
            getattr(player, "current_district_slug", None),
        ),
    )

    try:
        from handlers.map import show_location_screen

        await show_location_screen(message, player.location_slug)
        return
    except Exception:
        pass

    try:
        from game.grid_exploration_service import is_dungeon_available
        from game.location_rules import is_city
        from game.map_service import render_location_card
        from keyboards.location_menu import location_actions_inline
        from utils.images import send_location_image

        loc_text = render_location_card(player.location_slug)

        await send_location_image(
            message,
            player.location_slug,
            loc_text,
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )

        if not is_city(player.location_slug):
            has_dungeon = False
            try:
                has_dungeon = (
                    player.location_slug in DUNGEONS
                    and is_dungeon_available(message.from_user.id, player.location_slug)
                )
            except Exception:
                has_dungeon = False

            await message.answer(
                "Что будешь делать в этой локации?",
                reply_markup=location_actions_inline(
                    player.location_slug,
                    has_dungeon=has_dungeon,
                ),
            )
    except Exception:
        await message.answer(
            f"📍 Ты сейчас находишься в локации: {player.location_slug}",
            reply_markup=main_menu(
                player.location_slug,
                getattr(player, "current_district_slug", None),
            ),
        )
