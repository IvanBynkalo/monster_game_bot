from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database.repositories import get_player, update_player_district
from game.district_service import (
    get_district_move_commands,
    get_districts_for_location,
    render_district_card,
)
from game.location_rules import is_city
from game.gather_service import has_gathering_in_location
from keyboards.city_menu import district_actions_menu
from keyboards.main_menu import main_menu


def _normalize_district_text(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("Район: "):
        return "🧭→ " + text.replace("Район: ", "", 1)
    return text


def _district_transition_text(from_slug: str | None, to_slug: str) -> str:
    transitions = {
        ("market_square", "craft_quarter"): "🧭 Ты проходишь мимо торговых рядов и сворачиваешь в ремесленный квартал.",
        ("market_square", "guild_quarter"): "🧭 Ты уходишь с шумной площади к залам городских гильдий.",
        ("market_square", "main_gate"): "🧭 Ты покидаешь центр города и направляешься к главным воротам.",

        ("craft_quarter", "market_square"): "🧭 Ты выходишь из ремесленного квартала обратно на рыночную площадь.",
        ("craft_quarter", "guild_quarter"): "🧭 Оставив запах зелий и металла позади, ты идёшь к кварталу гильдий.",
        ("craft_quarter", "main_gate"): "🧭 Ты проходишь через городские улицы к главным воротам.",

        ("guild_quarter", "market_square"): "🧭 Ты покидаешь квартал гильдий и возвращаешься на рыночную площадь.",
        ("guild_quarter", "craft_quarter"): "🧭 От залов гильдий ты переходишь к мастерским и алхимическим лавкам.",
        ("guild_quarter", "main_gate"): "🧭 Ты идёшь от квартала гильдий в сторону главных ворот.",

        ("main_gate", "market_square"): "🧭 От городских ворот ты возвращаешься в оживлённый центр Сереброграда.",
        ("main_gate", "craft_quarter"): "🧭 От ворот ты сворачиваешь к мастерским ремесленного квартала.",
        ("main_gate", "guild_quarter"): "🧭 Оставив стражу позади, ты направляешься к кварталу гильдий.",
    }

    if from_slug == to_slug:
        return "🧭 Ты остаёшься в этом районе."

    return transitions.get((from_slug, to_slug), "🧭 Ты переходишь в другой район города.")


def district_menu(location_slug: str) -> ReplyKeyboardMarkup:
    commands = get_district_move_commands(location_slug)

    rows: list[list[KeyboardButton]] = []
    current_row: list[KeyboardButton] = []

    for command in commands:
        current_row.append(KeyboardButton(text=command))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    rows.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )


async def district_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not player.current_district_slug:
        await message.answer(
            "В этой локации пока нет доступных районов.",
            reply_markup=main_menu(player.location_slug, None),
        )
        return

    await message.answer(
        render_district_card(player.location_slug, player.current_district_slug),
        reply_markup=district_menu(player.location_slug),
    )


async def district_move_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if (message.text or "").strip() == "⬅️ Назад":
        await message.answer(
            "Городское меню",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    normalized = _normalize_district_text(message.text)
    available_names = set(get_district_move_commands(player.location_slug, telegram_id=message.from_user.id))

    if normalized not in available_names:
        await message.answer(
            "Из текущей локации в этот район перейти нельзя.",
            reply_markup=district_menu(player.location_slug),
        )
        return

    district_name = normalized.replace("🧭→ ", "", 1).strip()
    districts = get_districts_for_location(player.location_slug)

    target = None
    for district in districts:
        if district["name"] == district_name:
            target = district
            break

    if not target:
        await message.answer(
            "Не удалось определить район.",
            reply_markup=district_menu(player.location_slug),
        )
        return

    old_slug = player.current_district_slug
    new_slug = target["slug"]

    update_player_district(message.from_user.id, new_slug)

    transition_text = _district_transition_text(old_slug, new_slug)
    district_card = render_district_card(player.location_slug, new_slug)

    # В городе — показать меню действий района
    # В полевых локациях — показать основное меню с Исследовать/Собирать
    if is_city(player.location_slug):
        kb = district_actions_menu(new_slug, message.from_user.id)
    else:
        kb = main_menu(player.location_slug, new_slug)

    await message.answer(
        f"{transition_text}\n\n{district_card}",
        reply_markup=kb,
    )
