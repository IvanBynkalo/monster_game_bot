from aiogram.types import Message

from config import ADMIN_IDS
from database.repositories import (
    get_player,
    heal_all_monsters,
    reset_player_state,
    restore_player_energy,
    update_player_district,
    update_player_location,
)
from keyboards.admin_menu import admin_menu
from keyboards.main_menu import main_menu

ADMIN_STATES = {}

LOCATION_SLUGS = [
    "dark_forest",
    "shadow_swamp",
    "volcano_wrath",
    "bone_desert",
    "ancient_ruins",
    "emotion_rift",
    "storm_ridge",
]

DISTRICT_SLUGS = [
    "mushroom_path",
    "wet_thicket",
    "whisper_den",
    "black_water",
    "fog_trail",
    "grave_of_voices",
    "ash_slope",
    "lava_bridge",
    "heart_of_magma",
]

def _is_admin(user_id: int) -> bool:
    return user_id in set(ADMIN_IDS or [])

def _set_state(admin_id: int, action: str):
    ADMIN_STATES[admin_id] = {"action": action}

def _clear_state(admin_id: int):
    ADMIN_STATES.pop(admin_id, None)

def _get_state(admin_id: int):
    return ADMIN_STATES.get(admin_id)

def _parse_two_numbers(text: str):
    parts = (text or "").strip().split()
    if len(parts) != 2:
        return None, None
    if not parts[0].isdigit():
        return None, None
    try:
        value = int(parts[1])
    except ValueError:
        return None, None
    return int(parts[0]), value

def _parse_id_and_slug(text: str):
    parts = (text or "").strip().split(maxsplit=1)
    if len(parts) != 2 or not parts[0].isdigit():
        return None, None
    return int(parts[0]), parts[1].strip()

async def admin_panel_handler(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("У тебя нет доступа к админ-панели.")
        return
    _clear_state(message.from_user.id)
    await message.answer(
        "🛠 Админ-панель открыта.\nВыбери действие кнопками ниже.",
        reply_markup=admin_menu(),
    )

async def admin_buttons_handler(message: Message):
    if not _is_admin(message.from_user.id):
        return False

    text = (message.text or "").strip()

    if text == "💰 Выдать золото":
        _set_state(message.from_user.id, "grant_gold")
        await message.answer("Введи: ID_игрока количество\nПример: 123456789 500", reply_markup=admin_menu())
        return True

    if text == "⚡ Выдать энергию":
        _set_state(message.from_user.id, "grant_energy")
        await message.answer("Введи: ID_игрока количество\nПример: 123456789 5", reply_markup=admin_menu())
        return True

    if text == "❤️ Вылечить монстров":
        _set_state(message.from_user.id, "heal_all")
        await message.answer("Введи ID игрока", reply_markup=admin_menu())
        return True

    if text == "🧹 Сбросить игрока":
        _set_state(message.from_user.id, "reset_player")
        await message.answer("Введи ID игрока", reply_markup=admin_menu())
        return True

    if text == "🗺 Телепорт по локации":
        _set_state(message.from_user.id, "teleport_location")
        await message.answer(
            "Введи: ID_игрока slug_локации\n"
            "Доступно: " + ", ".join(LOCATION_SLUGS),
            reply_markup=admin_menu(),
        )
        return True

    if text == "🧭 Телепорт по району":
        _set_state(message.from_user.id, "teleport_district")
        await message.answer(
            "Введи: ID_игрока slug_района\n"
            "Доступно: " + ", ".join(DISTRICT_SLUGS),
            reply_markup=admin_menu(),
        )
        return True

    if text == "❌ Закрыть админ-панель":
        _clear_state(message.from_user.id)
        player = get_player(message.from_user.id)
        location_slug = player.location_slug if player else "dark_forest"
        await message.answer("Админ-панель закрыта.", reply_markup=main_menu(location_slug))
        return True

    state = _get_state(message.from_user.id)
    if not state:
        return False

    action = state["action"]

    if action == "grant_gold":
        target_id, amount = _parse_two_numbers(text)
        if target_id is None:
            await message.answer("Неверный формат. Введи: ID_игрока количество", reply_markup=admin_menu())
            return True
        player = get_player(target_id)
        if not player:
            await message.answer("Игрок не найден.", reply_markup=admin_menu())
            return True
        player.gold += amount
        _clear_state(message.from_user.id)
        await message.answer(f"✅ Игроку {target_id} выдано {amount} золота.\nТеперь золота: {player.gold}", reply_markup=admin_menu())
        return True

    if action == "grant_energy":
        target_id, amount = _parse_two_numbers(text)
        if target_id is None:
            await message.answer("Неверный формат. Введи: ID_игрока количество", reply_markup=admin_menu())
            return True
        player = get_player(target_id)
        if not player:
            await message.answer("Игрок не найден.", reply_markup=admin_menu())
            return True
        restore_player_energy(target_id, amount, max_energy=12)
        _clear_state(message.from_user.id)
        await message.answer(f"✅ Игроку {target_id} выдано {amount} энергии.\nТеперь энергии: {player.energy}", reply_markup=admin_menu())
        return True

    if action == "heal_all":
        if not text.isdigit():
            await message.answer("Введи корректный ID игрока.", reply_markup=admin_menu())
            return True
        target_id = int(text)
        player = get_player(target_id)
        if not player:
            await message.answer("Игрок не найден.", reply_markup=admin_menu())
            return True
        heal_all_monsters(target_id)
        _clear_state(message.from_user.id)
        await message.answer(f"✅ Все монстры игрока {target_id} вылечены.", reply_markup=admin_menu())
        return True

    if action == "reset_player":
        if not text.isdigit():
            await message.answer("Введи корректный ID игрока.", reply_markup=admin_menu())
            return True
        target_id = int(text)
        player = get_player(target_id)
        if not player:
            await message.answer("Игрок не найден.", reply_markup=admin_menu())
            return True
        reset_player_state(target_id, name=player.name)
        _clear_state(message.from_user.id)
        await message.answer(f"✅ Игрок {target_id} сброшен.", reply_markup=admin_menu())
        return True

    if action == "teleport_location":
        target_id, slug = _parse_id_and_slug(text)
        if target_id is None:
            await message.answer("Неверный формат. Введи: ID_игрока slug_локации", reply_markup=admin_menu())
            return True
        player = get_player(target_id)
        if not player:
            await message.answer("Игрок не найден.", reply_markup=admin_menu())
            return True
        if slug not in LOCATION_SLUGS:
            await message.answer("Неизвестный slug локации.", reply_markup=admin_menu())
            return True
        update_player_location(target_id, slug)
        _clear_state(message.from_user.id)
        await message.answer(f"✅ Игрок {target_id} телепортирован в локацию: {slug}", reply_markup=admin_menu())
        return True

    if action == "teleport_district":
        target_id, slug = _parse_id_and_slug(text)
        if target_id is None:
            await message.answer("Неверный формат. Введи: ID_игрока slug_района", reply_markup=admin_menu())
            return True
        player = get_player(target_id)
        if not player:
            await message.answer("Игрок не найден.", reply_markup=admin_menu())
            return True
        if slug not in DISTRICT_SLUGS:
            await message.answer("Неизвестный slug района.", reply_markup=admin_menu())
            return True
        update_player_district(target_id, slug)
        _clear_state(message.from_user.id)
        await message.answer(f"✅ Игрок {target_id} телепортирован в район: {slug}", reply_markup=admin_menu())
        return True

    return False

# Старые slash-команды оставлены для совместимости

async def grant_gold_handler(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("У тебя нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer("Формат: /grant_gold ID количество")
        return
    target_id = int(parts[1])
    amount = int(parts[2])
    player = get_player(target_id)
    if not player:
        await message.answer("Игрок не найден.")
        return
    player.gold += amount
    await message.answer(f"✅ Игроку {target_id} выдано {amount} золота.")

async def grant_energy_handler(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("У тебя нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer("Формат: /grant_energy ID количество")
        return
    target_id = int(parts[1])
    amount = int(parts[2])
    player = get_player(target_id)
    if not player:
        await message.answer("Игрок не найден.")
        return
    restore_player_energy(target_id, amount, max_energy=12)
    await message.answer(f"✅ Игроку {target_id} выдано {amount} энергии.")

async def heal_all_handler(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("У тебя нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Формат: /heal_all ID")
        return
    target_id = int(parts[1])
    if not get_player(target_id):
        await message.answer("Игрок не найден.")
        return
    heal_all_monsters(target_id)
    await message.answer(f"✅ Все монстры игрока {target_id} вылечены.")

async def teleport_location_handler(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("У тебя нет доступа.")
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer("Формат: /teleport_location ID slug")
        return
    target_id = int(parts[1])
    slug = parts[2].strip()
    if not get_player(target_id):
        await message.answer("Игрок не найден.")
        return
    if slug not in LOCATION_SLUGS:
        await message.answer("Неизвестный slug локации.")
        return
    update_player_location(target_id, slug)
    await message.answer(f"✅ Игрок {target_id} телепортирован в локацию: {slug}")

async def teleport_district_handler(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("У тебя нет доступа.")
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer("Формат: /teleport_district ID slug")
        return
    target_id = int(parts[1])
    slug = parts[2].strip()
    if not get_player(target_id):
        await message.answer("Игрок не найден.")
        return
    if slug not in DISTRICT_SLUGS:
        await message.answer("Неизвестный slug района.")
        return
    update_player_district(target_id, slug)
    await message.answer(f"✅ Игрок {target_id} телепортирован в район: {slug}")

async def reset_player_handler(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("У тебя нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Формат: /reset_player ID")
        return
    target_id = int(parts[1])
    player = get_player(target_id)
    if not player:
        await message.answer("Игрок не найден.")
        return
    reset_player_state(target_id, name=player.name)
    await message.answer(f"✅ Игрок {target_id} сброшен.")
