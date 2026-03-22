from aiogram.types import Message, CallbackQuery
from database.repositories import (
    get_active_monster,
    get_player,
    get_player_monsters,
    get_temp_effects,
    restore_player_energy,
    get_player_emotions,
    get_max_energy,
    tick_energy_regen,
)
from game.emotion_service import EMOTION_LABELS
from game.infection_service import render_monster_infection
from game.type_service import get_type_label
from game.progression_service import render_attributes, render_professions
from game.monster_abilities import render_abilities
from game.map_service import get_location_name
from game.expedition_service import render_effects_text
from game.district_service import get_district_name
from game.player_survival_service import render_player_status
from keyboards.main_menu import main_menu
from keyboards.profile_menu import profile_tabs, stat_spend_inline
from utils.logger import log_event


# ── Компактные тексты для каждой вкладки ──────────────────────────────────────

def _tab_main(player, monsters) -> str:
    # Crystal summary
    try:
        from game.crystal_service import get_player_crystals as _gpc, get_summoned_monster as _gsm
        _crystals = _gpc(player.telegram_id)
        _summoned = _gsm(player.telegram_id)
        _crystal_line = f"\n💎 Кристаллов: {len(_crystals)}"
        _summon_line = f"\n⚡ Призван: {_summoned['name']} ур.{_summoned['level']}" if _summoned else ""
    except Exception:
        _crystal_line = ""
        _summon_line = ""
    # Energy display with bonus
    try:
        from database.repositories import get_total_energy_display
        _e, _m, _b = get_total_energy_display(player.telegram_id)
        _energy_str = f"⚡ Энергия: {_e}/{_m}" + (f" +{_b}🔥 бонус" if _b > 0 else "")
    except Exception:
        _energy_str = f"⚡ Энергия: {player.energy}/{get_max_energy(player.telegram_id)}"
    return (
        f"📊 *Основное*\n\n"
        f"👤 {player.name} | Ур. {player.level}\n"
        f"✨ Опыт: {player.experience}/{player.level * 10}\n"
        f"{_energy_str}\n"
        f"💰 Золото: {player.gold}\n"
        f"{render_player_status(player)}\n\n"
        f"🐲 Монстров: {len(monsters)}"
        + _crystal_line + _summon_line + "\n"
        + f"📍 {get_location_name(player.location_slug)}"
    )


def _tab_monster(active) -> str:
    if not active:
        return "🐲 *Монстр*\n\nНет активного монстра."
    RARITY = {"common":"Обычный","rare":"Редкий","epic":"Эпический",
               "legendary":"Легендарный","mythic":"Мифический"}
    hp = f"{active.get('current_hp', active['hp'])}/{active.get('max_hp', active['hp'])}"
    xp = f"{active.get('experience',0)}/{active.get('level',1)*5}"
    return (
        f"🐲 *Монстр*\n\n"
        f"Имя: {active['name']}\n"
        f"Редкость: {RARITY.get(active.get('rarity','common'), '?')}\n"
        f"Тип: {get_type_label(active.get('monster_type'))}\n"
        f"Уровень: {active.get('level',1)} | Опыт: {xp}\n"
        f"HP: {hp} | ATK: {active.get('attack',0)}\n"
        f"Эволюция: стадия {active.get('evolution_stage',0)}\n"
        f"{render_abilities(active)}\n"
        f"{render_monster_infection(active)}"
    )


def _tab_stats(player) -> str:
    return (
        f"💪 *Характеристики*\n\n"
        f"{render_attributes(player)}\n\n"
        f"🎒 Сумка: {player.bag_capacity} слотов"
    )


def _tab_progress(player) -> str:
    pts = player.stat_points
    pts_text = f"🟡 Свободных очков: {pts}" if pts > 0 else "Нет свободных очков"
    return (
        f"📈 *Развитие*\n\n"
        f"{render_attributes(player)}\n\n"
        f"{pts_text}\n"
        f"_(Нажми кнопку ниже чтобы потратить очко)_\n\n"
        f"🎒 Сумка: {player.bag_capacity} слотов\n"
        f"_Новые сумки — в Торговом квартале_"
    )


def _tab_professions(player) -> str:
    return f"🎓 *Профессии*\n\n{render_professions(player)}"


def _tab_emotions(uid, monsters) -> str:
    emotions = get_player_emotions(uid)
    emo_monsters   = sum(1 for m in monsters if m.get("source_type") == "emotion")
    evo_monsters   = sum(1 for m in monsters if m.get("evolution_stage", 0) > 0)
    combo_monsters = sum(1 for m in monsters if m.get("combo_mutation"))
    lines = ["✨ *Эмоции*\n"]
    for key, label in EMOTION_LABELS.items():
        val = emotions.get(key, 0)
        if val > 0:
            lines.append(f"{label}: {val}")
    if len(lines) == 1:
        lines.append("Пусто")
    lines.append(f"\n🐲 Эмоц. монстров: {emo_monsters}")
    lines.append(f"🦋 Эволюционировавших: {evo_monsters}")
    lines.append(f"⚡ С комбо-мутацией: {combo_monsters}")
    return "\n".join(lines)


def _tab_effects(uid) -> str:
    effects = render_effects_text(get_temp_effects(uid))
    return f"🎒 *Эффекты*\n\n{effects}"


# ── Handlers ──────────────────────────────────────────────────────────────────

async def profile_handler(message: Message):
    # Регенерация энергии при открытии профиля
    tick_energy_regen(message.from_user.id)
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    monsters = get_player_monsters(message.from_user.id)
    text = _tab_main(player, monsters)

    await message.answer(
        text,
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
        parse_mode="Markdown",
    )
    await message.answer(
        "Выбери вкладку:",
        reply_markup=profile_tabs("main"),
    )


async def profile_tab_callback(callback: CallbackQuery):
    """Обработчик переключения вкладок профиля."""
    tab = callback.data.split(":")[2]
    uid = callback.from_user.id

    player   = get_player(uid)
    monsters = get_player_monsters(uid)
    active   = get_active_monster(uid)

    if not player:
        await callback.answer("Сначала напиши /start")
        return

    if tab == "main":
        text = _tab_main(player, monsters)
    elif tab == "monster":
        text = _tab_monster(active)
    elif tab == "stats":
        text = _tab_stats(player)
    elif tab == "progress":
        text = _tab_progress(player)
    elif tab == "prof":
        text = _tab_professions(player)
    elif tab == "emo":
        text = _tab_emotions(uid, monsters)
    elif tab == "effects":
        text = _tab_effects(uid)
    else:
        text = _tab_main(player, monsters)

    await callback.answer()
    # Для вкладки Развитие добавляем кнопки трат очков
    extra_markup = None
    if tab == "progress":
        extra_markup = stat_spend_inline(player.stat_points)

    try:
        await callback.message.edit_text(text, reply_markup=profile_tabs(tab),
                                          parse_mode="Markdown")
    except Exception:
        await callback.message.answer(text, reply_markup=profile_tabs(tab),
                                       parse_mode="Markdown")
    if extra_markup:
        await callback.message.answer("Потратить очко:", reply_markup=extra_markup)


async def restore_energy_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if player.gold < 3:
        await message.answer(
            "Недостаточно золота. Восстановление энергии стоит 3 золота.",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    from database.repositories import get_max_energy, add_bonus_energy, get_total_energy_display
    _e, _max_e, _bonus = get_total_energy_display(message.from_user.id)
    CAPSULE_AMOUNT = 5
    if _e >= _max_e:
        # Уже полная — даём бонусную
        add_bonus_energy(message.from_user.id, CAPSULE_AMOUNT)
        await message.answer(
            f"⚡🔥 Капсула использована! +{CAPSULE_AMOUNT} бонусной энергии (сверх лимита).\n"
            f"Энергия: {_e}/{_max_e} +{_bonus + CAPSULE_AMOUNT}🔥"
        )
        return
    else:
        restore_player_energy(message.from_user.id, amount=CAPSULE_AMOUNT, max_energy=_max_e)
    player = get_player(message.from_user.id)
    log_event("energy_restored", message.from_user.id, "gold_spent=3")
    await message.answer(
        f"⚡ Энергия восстановлена: {player.energy}/{get_max_energy(player.telegram_id)}\n💰 Потрачено: 3 золота",
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
    )


async def profile_stat_callback(callback: CallbackQuery):
    """Трата очков характеристик прямо из профиля."""
    parts = callback.data.split(":")
    stat = parts[2] if len(parts) > 2 else ""
    uid = callback.from_user.id

    from database.repositories import spend_stat_point, get_player
    if not spend_stat_point(uid, stat):
        await callback.answer("Нет свободных очков!", show_alert=True)
        return

    await callback.answer("✅ Характеристика повышена!")
    player = get_player(uid)
    text = _tab_progress(player)
    try:
        await callback.message.edit_text(text, reply_markup=profile_tabs("progress"),
                                          parse_mode="Markdown")
    except Exception:
        await callback.message.answer(text, reply_markup=profile_tabs("progress"),
                                       parse_mode="Markdown")
    await callback.message.answer("Потратить ещё:", reply_markup=stat_spend_inline(player.stat_points))
