from aiogram.types import Message
from database.repositories import get_active_monster, get_player, get_player_monsters, restore_player_energy
from game.emotion_service import render_emotions_panel
from game.infection_service import render_monster_infection
from keyboards.main_menu import main_menu
from utils.logger import log_event

async def profile_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    monsters = get_player_monsters(message.from_user.id)
    emotion_monsters = sum(1 for m in monsters if m.get("source_type") == "emotion")
    active = get_active_monster(message.from_user.id)
    active_text = active["name"] if active else "нет"
    infection_text = render_monster_infection(active) if active else "Заражение: нет"
    hp_text = f"{active.get('current_hp', active['hp'])}/{active.get('max_hp', active['hp'])}" if active else "-"
    await message.answer(
        f"🧭 Профиль\n\n"
        f"Имя: {player.name}\n"
        f"Уровень: {player.level}\n"
        f"Опыт: {player.experience}/{player.level * 10}\n"
        f"Энергия: {player.energy}/10\n"
        f"Золото: {player.gold}\n"
        f"Монстров всего: {len(monsters)}\n"
        f"Эмоциональных монстров: {emotion_monsters}\n"
        f"Активный монстр: {active_text}\n"
        f"HP активного монстра: {hp_text}\n"
        f"{infection_text}\n\n"
        f"{render_emotions_panel(message.from_user.id)}\n\n"
        f"Текущий регион: {player.current_region_slug}\n"
        f"Текущая локация: {player.location_slug}\n"
        f"Текущий район: {player.current_district_slug or 'не выбран'}",
        reply_markup=main_menu(player.location_slug),
    )

async def restore_energy_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.gold < 3:
        await message.answer("💰 Недостаточно золота. Восстановление энергии стоит 3 золота.")
        return
    restore_player_energy(message.from_user.id, amount=5, max_energy=10)
    player.gold -= 3
    log_event("energy_restored", message.from_user.id, "gold_spent=3")
    await message.answer(f"⚡ Энергия восстановлена. Текущее значение: {player.energy}/10\n💰 Потрачено: 3 золота", reply_markup=main_menu(player.location_slug))
