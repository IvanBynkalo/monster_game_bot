"""
monsters.py — Просмотр и управление монстрами.
Показывает по одному монстру с полной информацией + кристалл + совместимость.
"""
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.repositories import (
    get_active_monster, get_monster_by_id, get_player,
    get_player_monsters, heal_active_monster, set_active_monster,
)
from game.infection_service import render_monster_infection
from game.type_service import get_type_label
from game.monster_abilities import render_abilities
from keyboards.main_menu import main_menu
from utils.logger import log_event

RARITY_LABELS = {
    "common": "Обычный", "uncommon": "Необычный", "rare": "Редкий",
    "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический",
}
RARITY_EMOJI = {
    "common": "⚪", "uncommon": "🟢", "rare": "🔵",
    "epic": "🟣", "legendary": "🟡", "mythic": "🔴",
}
MOOD_LABELS = {
    "rage": "🔥 Ярость", "fear": "😱 Страх", "instinct": "🎯 Инстинкт",
    "inspiration": "✨ Вдохновение", "sadness": "💧 Грусть", "joy": "🌟 Радость",
}


def _get_crystal_info(telegram_id: int, monster: dict) -> str:
    """Информация о кристалле и совместимости."""
    crystal_id = monster.get("crystal_id")
    if not crystal_id:
        return "💎 Кристалл: не назначен ⚠️ (-15% ATK нестабильность)"
    try:
        from game.crystal_service import get_crystal, get_affinity_bonus, get_bond_level
        from game.crystal_heat import get_heat_level, HEAT_STATUS_LABELS, get_heat_modifiers
        crystal = get_crystal(crystal_id)
        if not crystal:
            return "💎 Кристалл: не найден"

        affinity_bonus = get_affinity_bonus(monster.get("mood","instinct"), crystal["emotion_affinity"])
        bond = get_bond_level(monster["id"], crystal_id)
        heat = get_heat_level(crystal_id)
        heat_mods = get_heat_modifiers(crystal_id)

        lines = [f"💎 Кристалл: {crystal['name']}"]
        # Совместимость
        if affinity_bonus > 1.0:
            lines.append(f"  ✅ Совместимость: +{int((affinity_bonus-1)*100)}% ATK")
        elif affinity_bonus < 1.0:
            lines.append(f"  ❌ Конфликт эмоций: {int((affinity_bonus-1)*100)}% ATK")
        else:
            lines.append(f"  ⚪ Нейтральная совместимость")
        # Связь
        if bond > 0:
            bar = "★" * bond + "☆" * (5-bond)
            lines.append(f"  🔗 Связь [{bar}] ур.{bond}: +{bond*5}% ATK")
        # Жар
        if heat > 0:
            lines.append(f"  {HEAT_STATUS_LABELS.get(heat_mods['status'], '')}")
        return "\n".join(lines)
    except Exception:
        return "💎 Кристалл: ошибка загрузки"


def _render_monster_card_full(monster: dict, telegram_id: int) -> str:
    """Полная карточка монстра с совместимостью кристалла."""
    rarity = monster.get("rarity", "common")
    r_emoji = RARITY_EMOJI.get(rarity, "⚪")
    r_label = RARITY_LABELS.get(rarity, rarity)
    mood = MOOD_LABELS.get(monster.get("mood","instinct"), monster.get("mood",""))
    active_mark = "⭐ АКТИВНЫЙ" if monster.get("is_active") else ""
    source = "🌌 Рождён" if monster.get("source_type") == "emotion" else "🐾 Пойман"
    if monster.get("source_type") == "starter":
        source = "🎁 Стартовый"
    if monster.get("source_type") == "shop":
        source = "🛒 Куплен"

    # Статус смерти
    if monster.get("is_dead"):
        costs = {"common":40,"uncommon":150,"rare":400,"epic":900,"legendary":1500}
        cost = costs.get(rarity, 100)
        dead_block = (
            f"\n\n💀 МОНСТР ПАЛ В БОЮ\n"
            f"Стоимость возрождения: {cost}з\n"
            f"→ Нажми «💎 Возродить монстра» в меню лечения\n"
            f"  или открой 💎 Кристаллы и нажми «Возродить»"
        )
    else:
        dead_block = ""

    # HP бар
    hp = monster.get("current_hp", monster.get("hp", 0))
    max_hp = monster.get("max_hp", monster.get("hp", 1))
    hp_pct = int(hp / max(1, max_hp) * 10)
    hp_bar = "█" * hp_pct + "░" * (10 - hp_pct)
    hp_color = "🟢" if hp_pct >= 7 else ("🟡" if hp_pct >= 4 else "🔴")

    # Опыт бар
    exp = monster.get("experience", 0)
    exp_need = monster["level"] * 5
    exp_pct = int(exp / max(1, exp_need) * 10)
    exp_bar = "█" * exp_pct + "░" * (10 - exp_pct)

    crystal_info = _get_crystal_info(telegram_id, monster)

    # Плюсы и минусы
    abilities_text = render_abilities(monster)
    infection_text = render_monster_infection(monster)

    lines = [
        f"{r_emoji} {monster['name']}  {active_mark}",
        f"{'─'*25}",
        f"📋 {r_label} | {source} | {mood}",
        f"⚔️ Тип: {get_type_label(monster.get('monster_type'))}",
        f"",
        f"{hp_color} HP: [{hp_bar}] {hp}/{max_hp}",
        f"⚔️ Атака: {monster['attack']}",
        f"📊 Ур.{monster['level']} | Опыт: [{exp_bar}] {exp}/{exp_need}",
        f"",
        crystal_info,
        f"",
        abilities_text,
        infection_text,
    ]
    if dead_block:
        lines.append(dead_block)
    return "\n".join(l for l in lines if l is not None)


def _monster_nav_inline(monsters: list, current_id: int, telegram_id: int) -> InlineKeyboardMarkup:
    """Навигация между монстрами + действия."""
    idx = next((i for i, m in enumerate(monsters) if m["id"] == current_id), 0)
    current = monsters[idx]
    rows = []

    # Навигация prev/next
    nav_row = []
    if idx > 0:
        prev = monsters[idx - 1]
        nav_row.append(InlineKeyboardButton(
            text=f"◀️ {prev['name'][:12]}",
            callback_data=f"mon:view:{prev['id']}"
        ))
    if idx < len(monsters) - 1:
        nxt = monsters[idx + 1]
        nav_row.append(InlineKeyboardButton(
            text=f"{nxt['name'][:12]} ▶️",
            callback_data=f"mon:view:{nxt['id']}"
        ))
    if nav_row:
        rows.append(nav_row)

    # Действия для живого монстра
    if not current.get("is_dead"):
        if not current.get("is_active"):
            rows.append([InlineKeyboardButton(
                text=f"✅ Сделать активным",
                callback_data=f"mon:activate:{current['id']}"
            )])
        # Перенос в другой кристалл
        rows.append([InlineKeyboardButton(
            text="💎 Сменить кристалл",
            callback_data=f"mon:move_crystal:{current['id']}"
        )])
    else:
        # Возрождение
        rarity = current.get("rarity","common")
        costs = {"common":40,"uncommon":150,"rare":400,"epic":900,"legendary":1500}
        cost = costs.get(rarity, 100)
        rows.append([InlineKeyboardButton(
            text=f"💀 Возродить за {cost}з",
            callback_data=f"mon:revive:{current['id']}"
        )])

    rows.append([InlineKeyboardButton(text="📋 Список всех", callback_data="mon:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _monsters_list_inline(monsters: list) -> InlineKeyboardMarkup:
    """Список всех монстров для выбора."""
    rows = []
    for m in monsters:
        dead = "💀 " if m.get("is_dead") else ""
        active = "⭐ " if m.get("is_active") else ""
        r = RARITY_EMOJI.get(m.get("rarity","common"), "⚪")
        rows.append([InlineKeyboardButton(
            text=f"{active}{dead}{r} {m['name']} ур.{m['level']} HP:{m.get('current_hp',0)}/{m.get('max_hp',1)}",
            callback_data=f"mon:view:{m['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _crystal_choice_inline(telegram_id: int, monster_id: int) -> InlineKeyboardMarkup:
    """Выбор кристалла для переноса монстра."""
    from game.crystal_service import get_player_crystals, get_monsters_in_crystal
    crystals = get_player_crystals(telegram_id)
    rows = []
    for c in crystals:
        if c.get("location","on_hand") != "on_hand":
            continue
        free_v = c["max_volume"] - c["current_volume"]
        free_s = c["max_monsters"] - c["current_monsters"]
        if free_v > 0 and free_s > 0:
            rows.append([InlineKeyboardButton(
                text=f"💎 {c['name']} [{c['current_volume']}/{c['max_volume']}]",
                callback_data=f"mon:set_crystal:{monster_id}:{c['id']}"
            )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"mon:view:{monster_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def monsters_handler(message: Message):
    """Показывает активного монстра (или первого)."""
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    monsters = get_player_monsters(message.from_user.id)
    if not monsters:
        await message.answer(
            "У тебя пока нет монстров.\n\n"
            "Где найти монстра:\n"
            "• 🌲 Исследовать локацию — встреча с монстром\n"
            "• 🐲 Рынок монстров — купить у Варга\n"
            "• 🌌 Алтарь рождения — создать из эмоций",
            reply_markup=main_menu(player.location_slug, player.current_district_slug)
        )
        return
    # Показываем активного или первого
    active = next((m for m in monsters if m.get("is_active")), monsters[0])
    uid = message.from_user.id
    text = _render_monster_card_full(active, uid)
    kb = _monster_nav_inline(monsters, active["id"], uid)
    await message.answer(text, reply_markup=kb)


async def monster_callback(callback: CallbackQuery):
    """Обрабатывает mon: коллбэки."""
    uid = callback.from_user.id
    player = get_player(uid)
    if not player:
        await callback.answer("Сначала /start")
        return
    data = callback.data
    await callback.answer()
    monsters = get_player_monsters(uid)

    if data == "mon:list":
        if not monsters:
            await callback.message.edit_text("Нет монстров.")
            return
        await callback.message.edit_text(
            "🐲 Твои монстры — выбери:",
            reply_markup=_monsters_list_inline(monsters)
        )

    elif data.startswith("mon:view:"):
        mid = int(data.split(":")[-1])
        monster = next((m for m in monsters if m["id"] == mid), None)
        if not monster:
            await callback.answer("Монстр не найден.", show_alert=True)
            return
        text = _render_monster_card_full(monster, uid)
        try:
            await callback.message.edit_text(text, reply_markup=_monster_nav_inline(monsters, mid, uid))
        except Exception:
            await callback.message.answer(text, reply_markup=_monster_nav_inline(monsters, mid, uid))

    elif data.startswith("mon:activate:"):
        mid = int(data.split(":")[-1])
        set_active_monster(uid, mid)
        # Also summon in crystal system
        try:
            from game.crystal_service import summon_monster
            summon_monster(uid, mid)
        except Exception:
            pass
        monsters = get_player_monsters(uid)
        monster = next((m for m in monsters if m["id"] == mid), None)
        if monster:
            text = _render_monster_card_full(monster, uid)
            await callback.message.edit_text(
                f"✅ {monster['name']} теперь активен!\n\n" + text,
                reply_markup=_monster_nav_inline(monsters, mid, uid)
            )

    elif data.startswith("mon:revive:"):
        mid = int(data.split(":")[-1])
        monster = next((m for m in monsters if m["id"] == mid), None)
        if not monster:
            await callback.answer("Монстр не найден.", show_alert=True)
            return
        costs = {"common":40,"uncommon":150,"rare":400,"epic":900,"legendary":1500}
        cost = costs.get(monster.get("rarity","common"), 100)
        if player.gold < cost:
            await callback.answer(
                f"Недостаточно золота! Нужно {cost}з, у тебя {player.gold}з",
                show_alert=True
            )
            return
        from database.repositories import revive_monster, _update_player_field
        revive_hp = max(1, monster["max_hp"] * 30 // 100)
        revive_monster(uid, mid, revive_hp)
        _update_player_field(uid, gold=player.gold - cost)
        monsters = get_player_monsters(uid)
        monster = next((m for m in monsters if m["id"] == mid), None)
        if monster:
            text = _render_monster_card_full(monster, uid)
            await callback.message.edit_text(
                f"✅ {monster['name']} возрождён с {revive_hp} HP!\n💰 Потрачено {cost}з\n\n" + text,
                reply_markup=_monster_nav_inline(monsters, mid, uid)
            )

    elif data.startswith("mon:move_crystal:"):
        mid = int(data.split(":")[-1])
        await callback.message.edit_text(
            "💎 Выбери кристалл для переноса монстра:",
            reply_markup=_crystal_choice_inline(uid, mid)
        )

    elif data.startswith("mon:set_crystal:"):
        parts = data.split(":")
        mid, cid = int(parts[2]), int(parts[3])
        from game.crystal_service import store_monster_in_crystal, get_crystal
        from database.repositories import get_connection as _gc
        # Убираем монстра из текущего кристалла
        monster = next((m for m in monsters if m["id"] == mid), None)
        if monster and monster.get("crystal_id"):
            old_cid = monster["crystal_id"]
            with _gc() as conn:
                vol = monster.get("storage_volume", 1)
                conn.execute(
                    "UPDATE player_crystals SET current_volume=MAX(0,current_volume-?), "
                    "current_monsters=MAX(0,current_monsters-1) WHERE id=?",
                    (vol, old_cid)
                )
                conn.execute(
                    "UPDATE player_monsters SET crystal_id=NULL WHERE id=?", (mid,)
                )
                conn.commit()
        ok, msg = store_monster_in_crystal(uid, mid, cid)
        await callback.answer(msg, show_alert=True)
        if ok:
            monsters = get_player_monsters(uid)
            monster = next((m for m in monsters if m["id"] == mid), None)
            if monster:
                text = _render_monster_card_full(monster, uid)
                await callback.message.edit_text(
                    text, reply_markup=_monster_nav_inline(monsters, mid, uid)
                )
