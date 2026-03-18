from aiogram.types import Message
from database.repositories import get_player, update_player_district
from game.district_service import (
    get_district_move_commands,
    get_districts_for_location,
    render_district_card,
)
from keyboards.main_menu import main_menu


def _normalize_district_text(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("Район: "):
        return "🧭→ " + text.replace("Район: ", "", 1)
    return text


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
        reply_markup=main_menu(player.location_slug, player.current_district_slug),
    )


async def district_move_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if (message.text or "").strip() == "⬅️ Назад":
        await message.answer(
            "Главное меню",
            reply_markup=main_menu(player.location_slug, player.current_district_slug),
        )
        return

    normalized = _normalize_district_text(message.text)
    available_names = set(get_district_move_commands(player.location_slug))

    if normalized not in available_names:
        await message.answer("Из текущей локации в этот район перейти нельзя.")
        return

    district_name = normalized.replace("🧭→ ", "", 1).strip()
    districts = get_districts_for_location(player.location_slug)

    target = None
    for district in districts:
        if district["name"] == district_name:
            target = district
            break

    if not target:
        await message.answer("Не удалось определить район.")
        return

    update_player_district(message.from_user.id, target["slug"])

    await message.answer(
        f"🧭 Ты переместился в район: {target['name']}\n\n"
        f"{render_district_card(player.location_slug, target['slug'])}",
        reply_markup=main_menu(player.location_slug, target["slug"]),
    )
