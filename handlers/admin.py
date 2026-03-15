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
from game.district_service import get_default_district_slug, get_districts_for_location
from keyboards.main_menu import main_menu
from utils.logger import log_event

def _is_admin(message: Message) -> bool:
    return message.from_user.id in ADMIN_IDS

async def _deny(message: Message):
    await message.answer("⛔ Недостаточно прав.")

async def admin_panel_handler(message: Message):
    if not _is_admin(message):
        return await _deny(message)
    await message.answer(
        "🛠 Админ-панель\n\n"
        "/grant_gold <amount>\n"
        "/grant_energy <amount>\n"
        "/heal_all\n"
        "/teleport_location <slug>\n"
        "/teleport_district <slug>\n"
        "/reset_player"
    )

async def grant_gold_handler(message: Message):
    if not _is_admin(message):
        return await _deny(message)
    player = get_player(message.from_user.id)
    if not player:
        return await message.answer("Сначала напиши /start")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        return await message.answer("Использование: /grant_gold 100")
    amount = int(parts[1])
    player.gold += amount
    log_event("admin_grant_gold", message.from_user.id, f"amount={amount}")
    await message.answer(f"💰 Золото изменено на {amount}. Текущий баланс: {player.gold}")

async def grant_energy_handler(message: Message):
    if not _is_admin(message):
        return await _deny(message)
    player = get_player(message.from_user.id)
    if not player:
        return await message.answer("Сначала напиши /start")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        return await message.answer("Использование: /grant_energy 5")
    amount = int(parts[1])
    restore_player_energy(message.from_user.id, amount=amount, max_energy=999)
    log_event("admin_grant_energy", message.from_user.id, f"amount={amount}")
    await message.answer(f"⚡ Энергия изменена на +{amount}. Текущее значение: {player.energy}")

async def heal_all_handler(message: Message):
    if not _is_admin(message):
        return await _deny(message)
    player = get_player(message.from_user.id)
    if not player:
        return await message.answer("Сначала напиши /start")
    monsters = heal_all_monsters(message.from_user.id)
    log_event("admin_heal_all", message.from_user.id, f"count={len(monsters)}")
    await message.answer(f"❤️ Восстановлено монстров: {len(monsters)}")

async def teleport_location_handler(message: Message):
    if not _is_admin(message):
        return await _deny(message)
    player = get_player(message.from_user.id)
    if not player:
        return await message.answer("Сначала напиши /start")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Использование: /teleport_location dark_forest")
    slug = parts[1].strip()
    update_player_location(message.from_user.id, slug)
    default_district = get_default_district_slug(slug)
    if default_district:
        update_player_district(message.from_user.id, default_district)
    log_event("admin_teleport_location", message.from_user.id, slug)
    await message.answer(f"🚶 Телепорт в локацию: {slug}", reply_markup=main_menu(player.location_slug))

async def teleport_district_handler(message: Message):
    if not _is_admin(message):
        return await _deny(message)
    player = get_player(message.from_user.id)
    if not player:
        return await message.answer("Сначала напиши /start")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Использование: /teleport_district mushroom_path")
    slug = parts[1].strip()
    districts = get_districts_for_location(player.location_slug)
    if slug not in [d["slug"] for d in districts]:
        return await message.answer("Такого района нет в текущей локации.")
    update_player_district(message.from_user.id, slug)
    log_event("admin_teleport_district", message.from_user.id, slug)
    await message.answer(f"🧭 Телепорт в район: {slug}", reply_markup=main_menu(player.location_slug))

async def reset_player_handler(message: Message):
    if not _is_admin(message):
        return await _deny(message)
    player = reset_player_state(message.from_user.id, message.from_user.first_name or "Игрок")
    log_event("admin_reset_player", message.from_user.id)
    await message.answer("♻️ Игрок сброшен. Напиши /start для повторной инициализации.", reply_markup=main_menu(player.location_slug))
