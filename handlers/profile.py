from aiogram.types import Message
from database.repositories import get_active_monster, get_player, get_player_monsters, get_temp_effects, restore_player_energy
from game.emotion_service import render_emotions_panel
from game.infection_service import render_monster_infection
from game.type_service import get_type_label
from game.progression_service import render_attributes, render_professions
from game.monster_abilities import render_abilities
from game.map_service import get_location_name
from game.expedition_service import render_effects_text
from game.district_service import get_district_name
from game.player_survival_service import render_player_status
from keyboards.main_menu import main_menu
from utils.logger import log_event

async def profile_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    monsters = get_player_monsters(message.from_user.id)
    emotion_monsters = sum(1 for m in monsters if m.get("source_type") == "emotion")
    evolved_monsters = sum(1 for m in monsters if m.get("evolution_stage", 0) > 0)
    active = get_active_monster(message.from_user.id)
    active_text = active["name"] if active else "нет"
    infection_text = render_monster_infection(active) if active else "Искажение: нет"
    hp_text = f"{active.get('current_hp', active['hp'])}/{active.get('max_hp', active['hp'])}" if active else "-"
    monster_xp = f"{active.get('experience', 0)}/{active['level'] * 5}" if active else "-"
    evolution_text = f"Стадия эволюции: {active.get('evolution_stage', 0)}" if active else "Стадия эволюции: -"
    monster_type = get_type_label(active.get("monster_type")) if active else "-"
    await message.answer(
        f"Профиль\n\n"
        f"Имя: {player.name}\n"
        f"Уровень игрока: {player.level}\n"
        f"Опыт игрока: {player.experience}/{player.level * 10}\n"
        f"Энергия: {player.energy}/12\n"
        f"Золото: {player.gold}\n"
        f"{render_player_status(player)}\n"
        f"Монстров всего: {len(monsters)}\n"
        f"Эмоциональных монстров: {emotion_monsters}\n"
        f"Эволюционировавших монстров: {evolved_monsters}\n"
        f"Активный монстр: {active_text}\n"
        f"Тип монстра: {monster_type}\n"
        f"Уровень монстра: {active['level'] if active else '-'}\n"
        f"Опыт монстра: {monster_xp}\n"
        f"HP активного монстра: {hp_text}\n"
        f"{evolution_text}\n"
        f"{render_abilities(active) if active else 'Способности: -'}\n"
        f"{infection_text}\n\n"
        f"{render_emotions_panel(message.from_user.id)}\n\n"
        f"{render_attributes(player)}\n\n"
        f"{render_professions(player)}\n"
        f"🎒 Вместимость сумки: {player.bag_capacity}\n"
        f"{render_effects_text(get_temp_effects(message.from_user.id))}\n\n"
        f"Текущий регион: Долина эмоций\n"
        f"Текущая локация: {get_location_name(player.location_slug)}\n"
        f"Текущий район: {get_district_name(player.location_slug, player.current_district_slug)}",
        reply_markup=main_menu(player.location_slug),
    )

async def restore_energy_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.gold < 3:
        await message.answer("Недостаточно золота. Восстановление энергии стоит 3 золота.")
        return
    restore_player_energy(message.from_user.id, amount=5, max_energy=12)
    player.gold -= 3
    log_event("energy_restored", message.from_user.id, "gold_spent=3")
    await message.answer(f"Энергия восстановлена. Текущее значение: {player.energy}/12\nПотрачено: 3 золота", reply_markup=main_menu(player.location_slug))
