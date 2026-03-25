from aiogram.types import CallbackQuery, Message

from database.repositories import (
    get_active_monster,
    get_player,
    get_player_emotions,
    get_player_monsters,
    get_temp_effects,
    get_total_energy_display,
    get_ui_screen,
    restore_player_energy,
    set_ui_screen,
    spend_stat_point,
    tick_energy_regen,
)
from game.district_service import get_district_name
from game.emotion_service import EMOTION_LABELS
from game.expedition_service import render_effects_text
from game.infection_service import render_monster_infection
from game.map_service import get_location_name
from game.monster_abilities import render_abilities
from game.player_survival_service import render_player_status
from game.progression_service import render_attributes, render_professions
from game.type_service import get_type_label
from keyboards.main_menu import main_menu
from keyboards.profile_menu import profile_tabs, stat_spend_inline
from utils.logger import log_event


RARITY_LABELS = {
    "common": "Обычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
    "mythic": "Мифический",
}


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


def _safe_energy_text(user_id: int, fallback_energy: int) -> str:
    try:
        current, maximum, bonus = get_total_energy_display(user_id)
        text = f"⚡ Энергия: {current}/{maximum}"
        if bonus > 0:
            text += f" +{bonus}🔥"
        return text
    except Exception:
        return f"⚡ Энергия: {fallback_energy}"


def _location_block(player) -> str:
    district_slug = getattr(player, "current_district_slug", None)
    location_line = f"📍 {get_location_name(player.location_slug)}"
    if district_slug:
        try:
            district_name = get_district_name(district_slug)
            if district_name:
                location_line += f" · {district_name}"
        except Exception:
            pass
    return location_line


def _crystal_summary(user_id: int) -> tuple[str, str]:
    try:
        from game.crystal_service import get_player_crystals, get_summoned_monster

        crystals = get_player_crystals(user_id)
        summoned = get_summoned_monster(user_id)
        crystals_line = f"💎 Кристаллы: {len(crystals)}"
        summon_line = (
            f"⚡ Призван: {summoned['name']} ур.{summoned['level']}"
            if summoned else
            "⚡ Призванный монстр: нет"
        )
        return crystals_line, summon_line
    except Exception:
        return "", ""


def _tab_main(player, monsters: list[dict]) -> str:
    crystals_line, summon_line = _crystal_summary(player.telegram_id)
    parts = [
        "👤 *Персонаж*",
        "",
        f"Имя: {player.name}",
        f"Уровень: {player.level}",
        f"✨ Опыт: {player.experience}/{max(10, player.level * 10)}",
        _safe_energy_text(player.telegram_id, player.energy),
        f"💰 Золото: {player.gold}",
        render_player_status(player),
        "",
        f"🐲 Монстров: {len(monsters)}",
        _location_block(player),
    ]
    if crystals_line:
        parts.append(crystals_line)
    if summon_line:
        parts.append(summon_line)
    return "\n".join([p for p in parts if p is not None])


def _tab_monster(active: dict | None) -> str:
    if not active:
        return "🐲 *Активный монстр*\n\nУ тебя сейчас нет активного монстра."

    current_hp = active.get("current_hp", active.get("hp", 1))
    max_hp = active.get("max_hp", active.get("hp", 1))
    exp_value = active.get("experience", 0)
    level = active.get("level", 1)
    next_exp = max(5, level * 5)

    parts = [
        "🐲 *Активный монстр*",
        "",
        f"Имя: {active.get('name', 'Безымянный')}",
        f"Редкость: {RARITY_LABELS.get(active.get('rarity', 'common'), 'Обычный')}",
        f"Тип: {get_type_label(active.get('monster_type'))}",
        f"Уровень: {level}",
        f"✨ Опыт: {exp_value}/{next_exp}",
        f"❤️ HP: {current_hp}/{max_hp}",
        f"⚔️ Атака: {active.get('attack', 0)}",
        f"🦋 Эволюция: стадия {active.get('evolution_stage', 0)}",
    ]

    abilities = render_abilities(active)
    infection = render_monster_infection(active)
    if abilities:
        parts.extend(["", abilities])
    if infection:
        parts.extend(["", infection])
    return "\n".join(parts)


def _tab_stats(player) -> str:
    return (
        "💪 *Характеристики*\n\n"
        f"{render_attributes(player)}\n\n"
        f"🎒 Вместимость сумки: {player.bag_capacity}"
    )


def _tab_progress(player) -> str:
    points_text = (
        f"🟡 Свободных очков: {player.stat_points}"
        if player.stat_points > 0
        else "Свободных очков нет"
    )
    return (
        "📈 *Развитие*\n\n"
        f"{render_attributes(player)}\n\n"
        f"{points_text}\n\n"
        f"🎒 Вместимость сумки: {player.bag_capacity}\n"
        "Новые сумки можно купить в Торговом квартале."
    )


def _tab_professions(player) -> str:
    return f"🎓 *Профессии*\n\n{render_professions(player)}"


def _tab_emotions(user_id: int, monsters: list[dict]) -> str:
    emotions = get_player_emotions(user_id)
    emotion_monsters = sum(1 for m in monsters if m.get("source_type") == "emotion")
    evolved_monsters = sum(1 for m in monsters if m.get("evolution_stage", 0) > 0)
    combo_monsters = sum(1 for m in monsters if m.get("combo_mutation"))

    lines = ["✨ *Эмоции*", ""]
    has_values = False
    for key, label in EMOTION_LABELS.items():
        value = emotions.get(key, 0)
        if value > 0:
            has_values = True
            lines.append(f"{label}: {value}")
    if not has_values:
        lines.append("Пока нет накопленных эмоций.")

    lines.extend([
        "",
        f"🐲 Эмо-монстров: {emotion_monsters}",
        f"🦋 Эволюционировавших: {evolved_monsters}",
        f"⚡ С комбо-мутацией: {combo_monsters}",
    ])
    return "\n".join(lines)


def _tab_effects(user_id: int) -> str:
    return f"🎒 *Эффекты*\n\n{render_effects_text(get_temp_effects(user_id))}"


def _build_tab_text(tab: str, player, monsters: list[dict], active: dict | None) -> str:
    if tab == "monster":
        return _tab_monster(active)
    if tab == "stats":
        return _tab_stats(player)
    if tab == "progress":
        return _tab_progress(player)
    if tab == "prof":
        return _tab_professions(player)
    if tab == "emo":
        return _tab_emotions(player.telegram_id, monsters)
    if tab == "effects":
        return _tab_effects(player.telegram_id)
    return _tab_main(player, monsters)


async def _send_profile_screen(message: Message, player, tab: str = "main", prefix: str | None = None):
    monsters = get_player_monsters(message.from_user.id)
    active = get_active_monster(message.from_user.id)
    set_ui_screen(message.from_user.id, "progression", tab=tab)

    text = _build_tab_text(tab, player, monsters, active)
    if prefix:
        text = f"{prefix}\n\n{text}"

    await message.answer(
        text,
        reply_markup=_root_markup(player, message.from_user.id),
        parse_mode="Markdown",
    )
    await message.answer(
        "Выбери вкладку:",
        reply_markup=profile_tabs(tab),
    )
    if tab == "progress" and player.stat_points >= 0:
        await message.answer(
            "Потратить очки:",
            reply_markup=stat_spend_inline(player.stat_points),
        )


async def profile_handler(message: Message):
    tick_energy_regen(message.from_user.id)
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    await _send_profile_screen(message, player, tab="main")


async def profile_tab_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    tab = parts[2] if len(parts) > 2 else "main"
    user_id = callback.from_user.id
    player = get_player(user_id)
    if not player:
        await callback.answer("Сначала напиши /start", show_alert=True)
        return

    monsters = get_player_monsters(user_id)
    active = get_active_monster(user_id)
    text = _build_tab_text(tab, player, monsters, active)
    set_ui_screen(user_id, "progression", tab=tab)

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=profile_tabs(tab),
            parse_mode="Markdown",
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=profile_tabs(tab),
            parse_mode="Markdown",
        )

    if tab == "progress":
        await callback.message.answer(
            "Потратить очки:",
            reply_markup=stat_spend_inline(player.stat_points),
        )


async def restore_energy_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if player.gold < 3:
        await message.answer(
            "Недостаточно золота. Восстановление энергии стоит 3 золота.",
            reply_markup=_root_markup(player, message.from_user.id),
        )
        return

    try:
        from database.repositories import add_bonus_energy, get_max_energy
    except Exception:
        await message.answer("Не удалось восстановить энергию. Попробуй позже.")
        return

    current_energy, max_energy, bonus_energy = get_total_energy_display(message.from_user.id)
    capsule_amount = 5

    if current_energy >= max_energy:
        add_bonus_energy(message.from_user.id, capsule_amount)
        await message.answer(
            f"⚡🔥 Капсула использована! +{capsule_amount} бонусной энергии.\n"
            f"Энергия: {current_energy}/{max_energy} +{bonus_energy + capsule_amount}🔥",
            reply_markup=_root_markup(player, message.from_user.id),
        )
        return

    restore_player_energy(message.from_user.id, amount=capsule_amount, max_energy=max_energy)
    updated = get_player(message.from_user.id)
    log_event("energy_restored", message.from_user.id, "gold_spent=3")
    await message.answer(
        f"⚡ Энергия восстановлена: {updated.energy}/{get_max_energy(updated.telegram_id)}\n"
        f"💰 Потрачено: 3 золота",
        reply_markup=_root_markup(updated, message.from_user.id),
    )


async def profile_stat_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    stat = parts[2] if len(parts) > 2 else ""
    user_id = callback.from_user.id

    if not stat:
        await callback.answer("Неизвестная характеристика", show_alert=True)
        return

    if not spend_stat_point(user_id, stat):
        await callback.answer("Нет свободных очков!", show_alert=True)
        return

    player = get_player(user_id)
    if not player:
        await callback.answer("Игрок не найден", show_alert=True)
        return

    set_ui_screen(user_id, "progression", tab="progress")
    text = _tab_progress(player)
    await callback.answer("✅ Характеристика повышена!")

    try:
        await callback.message.edit_text(
            text,
            reply_markup=profile_tabs("progress"),
            parse_mode="Markdown",
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=profile_tabs("progress"),
            parse_mode="Markdown",
        )

    await callback.message.answer(
        "Потратить ещё:",
        reply_markup=stat_spend_inline(player.stat_points),
    )
