from aiogram.types import Message
from database.repositories import get_active_monster, get_monster_by_id, get_player, get_player_monsters, heal_active_monster, set_active_monster
from game.infection_service import render_monster_infection
from game.type_service import get_type_label
from game.monster_abilities import render_abilities
from keyboards.main_menu import main_menu
from keyboards.monsters_menu import monsters_menu, monsters_inline_menu
from utils.logger import log_event

RARITY_LABELS = {"common": "Обычный", "rare": "Редкий", "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический"}
MOOD_LABELS = {"rage": "Ярость", "fear": "Страх", "instinct": "Инстинкт", "inspiration": "Вдохновение"}

def _render_monster_card(monster: dict):
    marker = "⭐ Активный" if monster.get("is_active") else f"▫️ #{monster['id']}"
    source = "🌌 Эмоциональный" if monster.get("source_type") == "emotion" else "🐾 Дикий"
    evo = "🦋 Есть эволюция" if monster.get("evolution_stage", 0) > 0 else "• Без эволюции"
    return "\n".join([
        f"{marker} | {source} | {monster['name']}",
        f"Редкость: {RARITY_LABELS.get(monster['rarity'], monster['rarity'])}",
        f"Эмоция: {MOOD_LABELS.get(monster['mood'], monster['mood'])}",
        f"Тип: {get_type_label(monster.get('monster_type'))}",
        f"HP: {monster.get('current_hp', monster['hp'])}/{monster.get('max_hp', monster['hp'])} | Атака: {monster['attack']}",
        f"Уровень: {monster['level']} | Опыт: {monster.get('experience', 0)}/{monster['level'] * 5}",
        f"Состояние: {evo}",
        f"{render_abilities(monster)}",
        f"{render_monster_infection(monster)}",
    ])

def _render_monster_list(monsters):
    if not monsters:
        return "У тебя пока нет монстров."
    lines = ["🐲 Твои монстры", ""]
    active = next((m for m in monsters if m.get("is_active")), None)
    if active:
        lines.append(_render_monster_card(active))
        lines.append("")
    others = [m for m in monsters if not m.get("is_active")]
    if others:
        lines.append("Доступны для переключения:")
        lines.append("")
        for monster in others:
            lines.append(_render_monster_card(monster))
            lines.append("")
        lines.append("Нажми кнопку с ID ниже, чтобы сделать монстра активным.")
    else:
        lines.append("У тебя пока только один монстр — он уже активный.")
    return "\n".join(lines)

async def monsters_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    monsters = get_player_monsters(message.from_user.id)
    await message.answer(_render_monster_list(monsters), reply_markup=monsters_inline_menu(monsters))

async def set_active_monster_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    raw = (message.text or "").replace("✅", "", 1).strip()
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
    monsters = get_player_monsters(message.from_user.id)
    await message.answer(
        f"✅ Активный монстр изменён: {active['name']}\n\n{_render_monster_list(monsters)}",
        reply_markup=monsters_inline_menu(monsters),
    )

async def heal_monster_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.gold < 8:
        await message.answer("Недостаточно золота. Лечение стоит 8 золота.", reply_markup=main_menu(player.location_slug))
        return
    active = heal_active_monster(message.from_user.id)
    if not active:
        await message.answer("У тебя нет активного монстра.", reply_markup=main_menu(player.location_slug))
        return
    player.gold -= 8
    log_event("monster_healed", message.from_user.id, active["name"])
    await message.answer(
        f"❤️ {active['name']} полностью восстановлен. HP: {active['current_hp']}/{active['max_hp']}\nПотрачено: 8 золота",
        reply_markup=main_menu(player.location_slug),
    )
