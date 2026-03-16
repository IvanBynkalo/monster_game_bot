from aiogram.types import Message
from database.repositories import get_active_monster, get_monster_by_id, get_player, get_player_monsters, heal_active_monster, set_active_monster
from game.infection_service import render_monster_infection
from game.type_service import get_type_label
from keyboards.main_menu import main_menu
from utils.logger import log_event

RARITY_LABELS = {"common": "Обычный", "rare": "Редкий", "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический"}
MOOD_LABELS = {"rage": "Ярость", "fear": "Страх", "instinct": "Инстинкт", "inspiration": "Вдохновение"}

def _render_monster_list(monsters):
    if not monsters:
        return "У тебя пока нет монстров."
    lines = ["🐲 Твои монстры", ""]
    for monster in monsters:
        marker = "⭐ Активный" if monster.get("is_active") else "▫️ Монстр"
        source = "🌌 Эмоциональный" if monster.get("source_type") == "emotion" else "🐾 Дикий"
        evo = "🦋 Есть эволюция" if monster.get("evolution_stage", 0) > 0 else "• Без эволюции"
        lines.extend([
            f"{marker} | {source} | #{monster['id']} {monster['name']}",
            f"Редкость: {RARITY_LABELS.get(monster['rarity'], monster['rarity'])}",
            f"Эмоция: {MOOD_LABELS.get(monster['mood'], monster['mood'])}",
            f"Тип: {get_type_label(monster.get('monster_type'))}",
            f"HP: {monster.get('current_hp', monster['hp'])}/{monster.get('max_hp', monster['hp'])} | Атака: {monster['attack']}",
            f"Уровень: {monster['level']} | Опыт: {monster.get('experience', 0)}/{monster['level'] * 5}",
            f"Состояние: {evo}",
            f"{render_monster_infection(monster)}",
        ])
        if not monster.get("is_active"):
            lines.append(f"Сделать активным: ✅ {monster['id']}")
        lines.append("")
    return "\n".join(lines)

async def monsters_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    monsters = get_player_monsters(message.from_user.id)
    await message.answer(_render_monster_list(monsters), reply_markup=main_menu(player.location_slug))

async def set_active_monster_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    raw = (message.text or "").replace("✅", "", 1).replace("Активный", "", 1).strip()
    if not raw.isdigit():
        await message.answer("Формат команды: ✅ ID")
        return
    monster_id = int(raw)
    monster = get_monster_by_id(message.from_user.id, monster_id)
    if not monster:
        await message.answer("Монстр с таким ID не найден.")
        return
    set_active_monster(message.from_user.id, monster_id)
    active = get_active_monster(message.from_user.id)
    log_event("active_monster_changed", message.from_user.id, active["name"])
    await message.answer(f"✅ Активный монстр изменён: {active['name']}", reply_markup=main_menu(player.location_slug))

async def heal_monster_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.gold < 8:
        await message.answer("Недостаточно золота. Лечение стоит 8 золота.")
        return
    active = heal_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра.")
        return
    player.gold -= 8
    log_event("monster_healed", message.from_user.id, active["name"])
    await message.answer(f"❤️ {active['name']} полностью восстановлен. HP: {active['current_hp']}/{active['max_hp']}\nПотрачено: 8 золота", reply_markup=main_menu(player.location_slug))
