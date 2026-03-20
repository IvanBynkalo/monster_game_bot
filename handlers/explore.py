import random

from aiogram.types import Message
from database.repositories import (
    add_item,
    add_player_experience,
    add_player_gold,
    add_relic,
    damage_player_hp,
    tick_player_injuries,
    begin_action_scope,
    clear_temp_effect,
    get_active_monster,
    get_item_count,
    get_player,
    get_temp_effects,
    has_relic,
    has_temp_effect,
    progress_quests,
    save_pending_encounter,
    set_temp_effect,
    spend_player_energy,
    tick_birth_cooldown,
    tick_temp_effects,
    update_story_progress,
)
from game.district_service import get_district, get_district_explore_text
from game.emotion_birth_service import render_birth_text, try_birth_emotional_monster
from game.emotion_service import grant_event_emotions, render_emotion_changes
from game.encounter_service import generate_district_encounter, render_encounter_text
from game.expedition_service import render_effects_text, roll_hazard
from game.infection_service import apply_dominant_emotion_infection, render_infection_update
from game.story_service import apply_story_reward
from game.treasure_service import roll_treasure
from game.secret_location_service import roll_secret_location
from game.dungeon_keys_service import roll_dungeon_key, get_key_name
from game.world_boss_service import get_world_event, roll_world_boss
from game.world_state_service import get_elite_expedition, roll_weather
from game.player_survival_service import render_injury_warning
from keyboards.encounter_menu import encounter_inline_menu, encounter_menu
from keyboards.main_menu import main_menu
from game.exploration_service import advance_exploration, render_exploration_text, apply_exploration_bonuses
from game.bestiary_service import register_bestiary_seen, check_trophy_drop
from game.weekly_quest_service import progress_weekly_quest, claim_weekly_reward, render_weekly_quest
from game.wildlife_service import roll_wildlife, render_wildlife_encounter, has_wildlife
from utils.logger import log_event
from utils.cooldown import cooldown_guard
from utils.analytics import track_explore
from game.daily_service import progress_daily_tasks, render_daily_completions
from game.season_pass_service import progress_season, render_season_completions

def _render_completed_quests(player_id: int, completed_now):
    parts = []
    for _, quest in completed_now:
        add_player_gold(player_id, quest["reward_gold"])
        add_player_experience(player_id, quest["reward_exp"])
        parts.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )
    return parts

def _apply_hazard(player, active_monster, hazard):
    if not hazard:
        return "", 0
    counter = hazard.get("effect_counter")
    if counter and has_temp_effect(player.telegram_id, counter):
        if counter == "swamp_guard":
            return "🪷 Защитный эффект нейтрализует болотную угрозу.", 0
        if counter == "crystal_skin":
            return "💎 Кристальная защита смягчает опасность местности.", 0
        if counter == "field_capture":
            return "🌼 Чутьё полей помогает безопасно пройти участок.", 0
    if not active_monster or hazard.get("damage", 0) <= 0:
        return hazard["text"], 0
    active_monster["current_hp"] = max(0, active_monster["current_hp"] - hazard["damage"])
    return hazard["text"], hazard["damage"]

def _weather_text(weather):
    if not weather:
        return ""
    return f"{weather['name']}\n{weather['text']}"

async def elite_expedition_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.is_defeated:
        await message.answer("☠️ Герой повержен. Сначала вылечи его.", reply_markup=main_menu(player.location_slug))
        return
    if getattr(player, "injury_turns", 0) > 0:
        await message.answer(render_injury_warning(player), reply_markup=main_menu(player.location_slug))
        return
    elite = get_elite_expedition(player.location_slug)
    if not elite:
        await message.answer("В этой локации элитная экспедиция недоступна.", reply_markup=main_menu(player.location_slug))
        return
    if not spend_player_energy(message.from_user.id, elite["cost_energy"]):
        await message.answer(f"⚡ Нужно {elite['cost_energy']} энергии для элитной экспедиции.", reply_markup=main_menu(player.location_slug))
        return
    set_temp_effect(message.from_user.id, elite["encounter_bonus"], 1)
    await message.answer(
        f"{elite['title']}\n\n{elite['description']}\n"
        f"Потрачено энергии: {elite['cost_energy']}\n"
        f"Следующее исследование пройдёт по элитному маршруту.",
        reply_markup=main_menu(player.location_slug),
    )

async def explore_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    if player.is_defeated:
        await message.answer("☠️ Герой повержен. Сначала вылечи его в Сереброграде.", reply_markup=main_menu(player.location_slug))
        return

    # Антиспам (рек. #2)
    if not await cooldown_guard(message, kind="explore", seconds=1.5):
        return

    # Аналитика (рек. #20)
    track_explore(message.from_user.id, player.location_slug)

    begin_action_scope(message.from_user.id, "explore")
    tick_birth_cooldown(message.from_user.id)

    # Исследование региона (Картограф)
    _expl_result = advance_exploration(message.from_user.id, player.location_slug)
    _expl_text = render_exploration_text(_expl_result, player.location_slug)
    _expl_bonuses = apply_exploration_bonuses(message.from_user.id, player.location_slug)

    if not spend_player_energy(message.from_user.id, 1):
        log_event("explore_failed_no_energy", message.from_user.id)
        await message.answer("⚡ Недостаточно энергии для исследования.")
        return

    tick_player_injuries(message.from_user.id, 1)
    completed_now = progress_quests(message.from_user.id, "explore")
    # Ежедневные задания + сезон (рек. #12, #15)
    _daily_done = progress_daily_tasks(message.from_user.id, "explore")
    _season_done = progress_season(message.from_user.id, "explore")
    story_done = update_story_progress(message.from_user.id, "explore", player.location_slug)

    district = get_district(player.location_slug, player.current_district_slug) if player.current_district_slug else None
    district_mood = district["mood"] if district else None
    intro = get_district_explore_text(player.location_slug, player.current_district_slug) if player.current_district_slug else "Ты исследуешь местность."
    world_event = get_world_event(player.location_slug)
    weather = roll_weather(player.location_slug)
    treasure = roll_treasure()
    dungeon_key = roll_dungeon_key()
    secret_location = roll_secret_location()
    boss = roll_world_boss(player.location_slug)
    hazard = roll_hazard(player.location_slug)
    active = get_active_monster(message.from_user.id)
    attacker_type = active.get("monster_type") if active else None

    hazard_text, hazard_damage = _apply_hazard(player, active, hazard)
    effect_text = render_effects_text(get_temp_effects(message.from_user.id))
    expired = tick_temp_effects(message.from_user.id)
    expired_text = f"⏳ Эффекты завершились: {', '.join(expired)}" if expired else ""

    extras = []
    if dungeon_key:
        add_item(message.from_user.id, dungeon_key, 1)
        extras.append(f"🗝 Найден ключ подземелья: {get_key_name(dungeon_key)}")
    if secret_location:
        extras.append(secret_location['name'])
        extras.append(secret_location['text'])
    if weather:
        extras.append(_weather_text(weather))
    injury_warning = render_injury_warning(player)
    if injury_warning:
        extras.append(injury_warning)

    if treasure:
        extras.append(treasure["title"])
        extras.append(treasure["text"])
        if treasure["type"] == "gold":
            add_player_gold(message.from_user.id, treasure["gold"])
            extras.append(f"💰 Получено золота: +{treasure['gold']}")
        elif treasure["type"] == "items":
            for item_slug, amount in treasure["items"].items():
                add_item(message.from_user.id, item_slug, amount)
            item_text = ", ".join([f"{slug} x{amount}" for slug, amount in treasure["items"].items()])
            extras.append(f"🎒 Найдено: {item_text}")
        elif treasure["type"] == "relic":
            relic_slug = treasure["relic_slug"]
            if not has_relic(message.from_user.id, relic_slug):
                add_relic(message.from_user.id, relic_slug)
                from game.relic_service import get_relic
                relic = get_relic(relic_slug)
                if relic:
                    extras.append(f"🔮 Получена реликвия: {relic['name']}")
            else:
                add_player_gold(message.from_user.id, 25)
                extras.append("🔁 Такая реликвия уже есть. Ты продаёшь находку коллекционеру за 25 золота.")

    if boss:
        encounter = {
            "type": "world_boss",
            "name": boss["name"],
            "hp": boss["hp"],
            "attack": boss["attack"],
            "reward_gold": boss["reward_gold"],
            "reward_exp": boss["reward_exp"],
            "monster_type": boss["monster_type"],
        }
        save_pending_encounter(message.from_user.id, encounter)
        log_event("world_boss", message.from_user.id, boss["name"])
        text = (
            f"{intro}\n\n---\n\n"
            f"👑 Мировой босс!\n{boss['text']}\n"
            f"{boss['name']}\nHP: {boss['hp']} | Атака: {boss['attack']}"
        )
        if hazard_text:
            extras.append(hazard_text + (f"\nПотеря HP: {hazard_damage}" if hazard_damage > 0 else ""))
        _, changes = grant_event_emotions(message.from_user.id, "anomaly", district_mood=district_mood)
        emotion_text = render_emotion_changes(changes)
        if emotion_text:
            extras.append(emotion_text)
        infection_update = render_infection_update(apply_dominant_emotion_infection(message.from_user.id))
        if infection_update:
            extras.append(infection_update)
        born = render_birth_text(try_birth_emotional_monster(message.from_user.id))
        if born:
            extras.append(born)
        extras.extend(_render_completed_quests(message.from_user.id, completed_now))
        if story_done:
            extras.append(apply_story_reward(message.from_user.id, story_done))
        extras.append(effect_text)
        if expired_text:
            extras.append(expired_text)
        if extras:
            text += "\n\n" + "\n\n".join(extras)
        await message.answer(text, reply_markup=encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        ))
        return

    encounter_slug = player.current_district_slug

    if has_temp_effect(message.from_user.id, "elite_forest"):
        encounter_slug = "elite_forest"
        clear_temp_effect(message.from_user.id, "elite_forest")
        extras.append("🌲 Элитный маршрут ведёт тебя в самую опасную часть леса.")
    elif has_temp_effect(message.from_user.id, "elite_hills"):
        encounter_slug = "elite_hills"
        clear_temp_effect(message.from_user.id, "elite_hills")
        extras.append("⛰ Элитный маршрут выводит к глубинной жиле и древним чудовищам.")
    elif has_temp_effect(message.from_user.id, "elite_marsh"):
        encounter_slug = "elite_marsh"
        clear_temp_effect(message.from_user.id, "elite_marsh")
        extras.append("🕸 Элитный маршрут уводит в сердце мёртвого болота.")

    # Распределение встреч: звери > события >> монстры
    # Монстры — редкость, их ценность в уникальности
    _expl_bonus_pct = int(_expl_bonuses.get("rare_bonus", 0) * 100)
    _monster_chance  = max(5, 8 + _expl_bonus_pct)   # 5-18%
    _wildlife_chance = 62                              # 62%
    _event_chance    = 100 - _monster_chance - _wildlife_chance

    _roll = random.randint(1, 100)
    if _roll <= _monster_chance and encounter_slug:
        encounter = generate_district_encounter(encounter_slug)
        # Убеждаемся что это действительно монстр (не событие из пула)
        if encounter.get("type") != "monster":
            encounter = {"type": "event", "text": "В чаще что-то шевелится, но исчезает прежде чем ты успеваешь разглядеть."}
    elif _roll <= _monster_chance + _wildlife_chance and has_wildlife(player.location_slug):
        _animal = roll_wildlife(player.location_slug)
        if _animal:
            encounter = _animal
        else:
            encounter = {"type": "event", "text": "Тишина окутывает местность."}
    else:
        encounter = generate_district_encounter(encounter_slug) if encounter_slug else {"type": "event", "text": "Тишина окутывает местность."}
        # Если выпал монстр — превращаем в событие (шанс монстра уже использован)
        if encounter.get("type") == "monster":
            encounter = {"type": "event", "text": encounter.get("text", "Что-то промелькнуло в тени и скрылось.")}
    if encounter["type"] == "monster":
        capture_bonus = 0.0
        if has_temp_effect(message.from_user.id, "field_capture"):
            capture_bonus += 0.12
        if weather and weather.get("capture_bonus"):
            capture_bonus += weather["capture_bonus"]
        if capture_bonus:
            encounter["bonus_capture"] = encounter.get("bonus_capture", 0.0) + capture_bonus
        save_pending_encounter(message.from_user.id, encounter)
        text = f"{intro}\n\n---\n\n{render_encounter_text(encounter, attacker_type=attacker_type)}"
        # Показываем изображение типа монстра
        _encounter_monster_type = encounter.get("monster_type", "void")
    else:
        event = world_event or encounter
        text = f"{intro}\n\n---\n\n{event['text']}"

    _, changes = grant_event_emotions(message.from_user.id, "anomaly", district_mood=district_mood)
    emotion_text = render_emotion_changes(changes)
    if hazard_text:
        extras.append(hazard_text + (f"\nПотеря HP монстра: {hazard_damage}" if hazard_damage > 0 else ""))
        if hazard_damage >= 4:
            damage_player_hp(message.from_user.id, 2)
            current_player = get_player(message.from_user.id)
            extras.append(f"❤️ Герой тоже получает 2 урона. HP героя: {current_player.hp}/{current_player.max_hp}")
    if emotion_text:
        extras.append(emotion_text)
    infection_update = render_infection_update(apply_dominant_emotion_infection(message.from_user.id))
    if infection_update:
        extras.append(infection_update)
    _born_monster = try_birth_emotional_monster(message.from_user.id)
    born = render_birth_text(_born_monster)
    if born:
        log_event("emotion_birth", message.from_user.id, "explore_birth")
        extras.append(born)
    _born_emotion = _born_monster.get("mood") if _born_monster else None
    extras.extend(_render_completed_quests(message.from_user.id, completed_now))
    if story_done:
        extras.append(apply_story_reward(message.from_user.id, story_done))
    if _expl_text:
        extras.append(_expl_text)
    extras.append(effect_text)
    if expired_text:
        extras.append(expired_text)

    full_text = text + ("\n\n" + "\n\n".join(extras) if extras else "")
    # Если было рождение монстра — показываем отдельное изображение
    _born_emotion_local = locals().get("_born_emotion")
    if _born_emotion_local and born:
        from utils.images import send_birth_image
        await send_birth_image(message, _born_emotion_local, born)

    if encounter["type"] in ("monster", "wildlife"):
        kb = encounter_inline_menu(
            has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
            has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0
        )
        if encounter["type"] == "wildlife":
            # Зверей нельзя поймать — используем боевое меню без кнопки поимки
            from keyboards.encounter_menu import encounter_inline_menu as _wkb
            kb = _wkb(has_trap=get_item_count(message.from_user.id, 'basic_trap') > 0,
                      has_poison_trap=get_item_count(message.from_user.id, 'poison_trap') > 0)
            await message.answer(full_text, reply_markup=kb)
        else:
            from utils.images import send_monster_image
            mtype = locals().get("_encounter_monster_type", encounter.get("monster_type", "void"))
            await send_monster_image(message, mtype, full_text, reply_markup=kb)
    else:
        # Для событий без монстра — показываем картинку локации
        from utils.images import send_location_image
        await send_location_image(message, player.location_slug, full_text,
                                   reply_markup=main_menu(player.location_slug))
