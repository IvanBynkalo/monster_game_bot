from aiogram.types import Message

from database.repositories import (
    get_active_monster,
    get_inventory,
    get_item_count,
    get_player,
    heal_active_monster,
    restore_player_energy,
    set_temp_effect,
    set_ui_screen,
    spend_item,
)
from game.item_service import render_inventory_text
from keyboards.inventory_menu import inventory_menu
from keyboards.main_menu import main_menu


USABLE_ITEMS = {
    "small_potion": {
        "label": "🧪 Малое зелье",
        "kind": "heal_monster",
        "amount": 8,
        "empty_text": "🧪 У тебя нет малого зелья.",
        "used_text": "🧪 Использовано малое зелье.",
    },
    "big_potion": {
        "label": "🧪 Большое зелье",
        "kind": "heal_monster",
        "amount": 16,
        "empty_text": "🧪 У тебя нет большого зелья.",
        "used_text": "🧪 Использовано большое зелье.",
    },
    "energy_capsule": {
        "label": "⚡ Капсула энергии",
        "kind": "restore_energy",
        "amount": 6,
        "empty_text": "⚡ У тебя нет капсулы энергии.",
        "used_text": "⚡ Использована капсула энергии.",
        "full_text": "⚡ Энергия уже полная.",
    },
    "spark_tonic": {
        "label": "✨ Настой искры",
        "kind": "restore_energy",
        "amount": 5,
        "empty_text": "✨ У тебя нет настоя искры.",
        "used_text": "✨ Использован настой искры.",
        "full_text": "✨ Энергия уже полная.",
    },
    "field_elixir": {
        "label": "🌼 Эликсир лугов",
        "kind": "effect",
        "effect": "field_capture",
        "turns": 3,
        "empty_text": "🌼 У тебя нет эликсира лугов.",
        "used_text": (
            "🌼 Эликсир лугов использован.\n"
            "Следующие 3 исследования дадут бонус к поимке и помогут в полях."
        ),
    },
    "crystal_focus": {
        "label": "💎 Кристальный концентрат",
        "kind": "energy_and_effect",
        "energy": 4,
        "effect": "crystal_skin",
        "turns": 3,
        "empty_text": "💎 У тебя нет кристального концентрата.",
        "used_text": (
            "💎 Концентрат использован.\n"
            "Следующие 3 исследования будут безопаснее в каменных и жарких зонах."
        ),
    },
    "swamp_antidote": {
        "label": "🪷 Болотный антидот",
        "kind": "effect",
        "effect": "swamp_guard",
        "turns": 3,
        "empty_text": "🪷 У тебя нет болотного антидота.",
        "used_text": (
            "🪷 Ты используешь болотный антидот.\n"
            "Следующие 3 исследования в болотах будут безопаснее."
        ),
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────────────────────────────────────


def _is_traveling_now(user_id: int) -> bool:
    try:
        from game.travel_service import is_traveling as _is_traveling
        return _is_traveling(user_id)
    except Exception:
        return False



def _root_markup(player, user_id: int):
    return main_menu(
        player.location_slug,
        getattr(player, "current_district_slug", None),
        is_traveling=_is_traveling_now(user_id),
        telegram_id=user_id,
    )



def _inventory_markup(player, inventory: dict):
    return inventory_menu(inventory, player.location_slug)



def _energy_limit(user_id: int) -> int:
    try:
        from database.repositories import get_max_energy
        return get_max_energy(user_id)
    except Exception:
        return 12



def _resource_lines(inventory: dict) -> list[str]:
    hidden = {
        "small_potion",
        "big_potion",
        "energy_capsule",
        "spark_tonic",
        "field_elixir",
        "crystal_focus",
        "swamp_antidote",
        "basic_trap",
        "poison_trap",
    }
    lines = []
    for slug, qty in sorted(inventory.items()):
        if qty <= 0 or slug in hidden:
            continue
        label = slug.replace("_", " ").title()
        lines.append(f"• {label}: {qty}")
    return lines


async def _show_inventory(message: Message, player, prefix_text: str | None = None):
    inventory = get_inventory(message.from_user.id)
    set_ui_screen(message.from_user.id, "inventory")
    text = render_inventory_text(inventory)
    if prefix_text:
        text = f"{prefix_text}\n\n{text}"
    await message.answer(
        text,
        reply_markup=_inventory_markup(player, inventory),
    )


async def _show_resources(message: Message, player):
    inventory = get_inventory(message.from_user.id)
    set_ui_screen(message.from_user.id, "inventory")

    lines = _resource_lines(inventory)
    if not lines:
        text = "📦 Ресурсы\n\nСумка с ресурсами пока пуста."
    else:
        text = "📦 Ресурсы\n\n" + "\n".join(lines)

    await message.answer(
        text,
        reply_markup=_inventory_markup(player, inventory),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Основной экран
# ──────────────────────────────────────────────────────────────────────────────

async def inventory_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    await _show_inventory(message, player)


async def resources_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    await _show_resources(message, player)


# ──────────────────────────────────────────────────────────────────────────────
# Использование предметов
# ──────────────────────────────────────────────────────────────────────────────

async def _use_heal_monster_item(message: Message, item_slug: str):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    item = USABLE_ITEMS[item_slug]
    inventory = get_inventory(message.from_user.id)
    active = get_active_monster(message.from_user.id)

    if get_item_count(message.from_user.id, item_slug) <= 0:
        await message.answer(item["empty_text"], reply_markup=_inventory_markup(player, inventory))
        return

    if not active:
        await message.answer(
            "🐲 У тебя нет активного монстра для лечения.",
            reply_markup=_inventory_markup(player, inventory),
        )
        return

    current_hp = active.get("current_hp", active.get("hp", 1))
    max_hp = active.get("max_hp", active.get("hp", 1))
    if current_hp >= max_hp:
        await message.answer(
            f"❤️ {active['name']} уже полностью здоров.\nHP: {current_hp}/{max_hp}",
            reply_markup=_inventory_markup(player, inventory),
        )
        return

    spend_item(message.from_user.id, item_slug, 1)
    active = heal_active_monster(message.from_user.id, item["amount"])
    inventory = get_inventory(message.from_user.id)

    await message.answer(
        f"{item['used_text']}\n❤️ {active['name']}: {active['current_hp']}/{active['max_hp']} HP",
        reply_markup=_inventory_markup(player, inventory),
    )


async def _use_energy_item(message: Message, item_slug: str):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    item = USABLE_ITEMS[item_slug]
    inventory = get_inventory(message.from_user.id)
    max_energy = _energy_limit(message.from_user.id)

    if get_item_count(message.from_user.id, item_slug) <= 0:
        await message.answer(item["empty_text"], reply_markup=_inventory_markup(player, inventory))
        return

    if player.energy >= max_energy:
        await message.answer(item["full_text"], reply_markup=_inventory_markup(player, inventory))
        return

    spend_item(message.from_user.id, item_slug, 1)
    player = restore_player_energy(message.from_user.id, item["amount"], max_energy=max_energy)
    inventory = get_inventory(message.from_user.id)

    await message.answer(
        f"{item['used_text']}\nЭнергия: {player.energy}/{max_energy}",
        reply_markup=_inventory_markup(player, inventory),
    )


async def _use_effect_item(message: Message, item_slug: str):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    item = USABLE_ITEMS[item_slug]
    inventory = get_inventory(message.from_user.id)

    if get_item_count(message.from_user.id, item_slug) <= 0:
        await message.answer(item["empty_text"], reply_markup=_inventory_markup(player, inventory))
        return

    spend_item(message.from_user.id, item_slug, 1)
    set_temp_effect(message.from_user.id, item["effect"], item["turns"])
    inventory = get_inventory(message.from_user.id)

    await message.answer(
        item["used_text"],
        reply_markup=_inventory_markup(player, inventory),
    )


async def _use_energy_and_effect_item(message: Message, item_slug: str):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    item = USABLE_ITEMS[item_slug]
    inventory = get_inventory(message.from_user.id)
    max_energy = _energy_limit(message.from_user.id)

    if get_item_count(message.from_user.id, item_slug) <= 0:
        await message.answer(item["empty_text"], reply_markup=_inventory_markup(player, inventory))
        return

    spend_item(message.from_user.id, item_slug, 1)
    player = restore_player_energy(message.from_user.id, item["energy"], max_energy=max_energy)
    set_temp_effect(message.from_user.id, item["effect"], item["turns"])
    inventory = get_inventory(message.from_user.id)

    await message.answer(
        f"{item['used_text']}\nЭнергия: {player.energy}/{max_energy}",
        reply_markup=_inventory_markup(player, inventory),
    )


async def use_small_potion_handler(message: Message):
    await _use_heal_monster_item(message, "small_potion")


async def use_big_potion_handler(message: Message):
    await _use_heal_monster_item(message, "big_potion")


async def use_energy_capsule_handler(message: Message):
    await _use_energy_item(message, "energy_capsule")


async def use_spark_tonic_handler(message: Message):
    await _use_energy_item(message, "spark_tonic")


async def use_field_elixir_handler(message: Message):
    await _use_effect_item(message, "field_elixir")


async def use_crystal_focus_handler(message: Message):
    await _use_energy_and_effect_item(message, "crystal_focus")


async def use_swamp_antidote_handler(message: Message):
    await _use_effect_item(message, "swamp_antidote")


# ──────────────────────────────────────────────────────────────────────────────
# Возврат из инвентаря
# ──────────────────────────────────────────────────────────────────────────────

async def back_to_menu_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    set_ui_screen(message.from_user.id, "main")
    await message.answer(
        "Главное меню",
        reply_markup=_root_markup(player, message.from_user.id),
    )
