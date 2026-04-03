# ── Error tracking shim ─────────────────────────────
try:
    from game.error_tracker import log_logic_error as _log_logic, log_exception as _log_exc
except Exception:
    def _log_logic(*a, **k):
        pass
    def _log_exc(*a, **k):
        pass
# ────────────────────────────────────────────────────

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.repositories import (
    add_player_experience,
    add_player_gold,
    add_city_order,
    complete_city_order,
    count_active_city_orders,
    get_active_city_orders,
    get_city_resource_market,
    get_equipped_bag,
    get_player,
    get_player_bags,
    get_player_monsters,
    get_resources,
    grant_bag,
    has_active_city_order,
    equip_bag,
    sell_bag,
    remove_player_monster,
    sell_resource_to_city_market,
    buy_resource_from_city_market,
    set_ui_screen,
    spend_item,
    spend_resource,
    update_player_district,
)
from database.db import get_connection

try:
    from database.repositories import get_inventory
except ImportError:
    def get_inventory(_telegram_id: int):
        return {}

try:
    from database.repositories import add_captured_monster, purchase_market_monster
except ImportError:
    add_captured_monster = None
    purchase_market_monster = None

from game.city_service import render_city_menu
from game.craft_service import render_craft_text
from game.guild_quests import (
    render_guild_panel,
    get_active_quests,
    get_available_quests,
)
from game.item_service import ITEMS
from game.location_rules import is_city
from game.market_service import BAG_OFFERS, get_resource_label
from game.shop_service import MONSTER_SHOP_OFFERS
from game.trap_service import render_trap_shop, craft_trap_item, TRAP_RECIPES

from keyboards.board_menu import board_menu
from keyboards.city_menu import city_menu, district_actions_menu, invalidate_quest_status_cache
from keyboards.craft_menu import craft_menu
from keyboards.main_menu import main_menu
from keyboards.shop_menu import sell_menu, buy_resources_menu


CITY_ORDER_LIMIT = 2

CITY_BOARD_ORDER_DEFS = {
    "herbalist_order": {
        "title": "Заказ травника",
        "goal_text": "Продай 3 🌿 Лесная трава Борту в лавку ресурсов.",
        "reward_gold": 35,
        "reward_exp": 12,
    },
    "ore_order": {
        "title": "Нужна руда для печей",
        "goal_text": "Продай 2 🔥 Угольный камень Борту в лавку ресурсов.",
        "reward_gold": 40,
        "reward_exp": 14,
    },
}

MIRNA_BUY_PRICES = {
    "small_potion": 6,
    "big_potion": 11,
    "energy_capsule": 9,
    "basic_trap": 7,
    "poison_trap": 12,
    "spark_tonic": 14,
    "field_elixir": 16,
    "crystal_focus": 20,
    "swamp_antidote": 16,
}

RARITY_SELL_BASE = {
    "common": 20,
    "rare": 45,
    "epic": 90,
    "legendary": 180,
    "mythic": 320,
}

NPC_QUEST_DEFS = {
    "mirna_travel_set": {
        "npc": "mirna",
        "title": "Походный набор для каравана",
        "goal_text": "Принеси Мирне 2 🧪 Малое зелье и 1 ⚡ Капсула энергии.",
        "reward_gold": 35,
        "reward_exp": 18,
        "kind": "items",
        "requirements": {"small_potion": 2, "energy_capsule": 1},
    },
    "varg_first_beast": {
        "npc": "varg",
        "title": "Первый зверь для перепродажи",
        "goal_text": "Отдай Варгу 1 неактивного монстра.",
        "reward_gold": 55,
        "reward_exp": 28,
        "kind": "monster",
        "requirements": {"count": 1},
    },
    "bort_supply_batch": {
        "npc": "bort",
        "title": "Поставка для складов",
        "goal_text": "Принеси Борту 3 🌿 Лесная трава и 2 🔥 Угольный камень.",
        "reward_gold": 50,
        "reward_exp": 24,
        "kind": "resources",
        "requirements": {"forest_herb": 3, "ember_stone": 2},
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _answer_with_city_image(message: Message, image_name: str, text: str, reply_markup):
    from utils.images import CITY_DIR, CITY_IMAGES
    from aiogram.types import FSInputFile

    context = image_name.replace(".png", "")
    mapped = CITY_IMAGES.get(context, image_name)
    image_path = CITY_DIR / mapped
    if image_path.exists():
        await message.answer_photo(
            photo=FSInputFile(str(image_path)),
            caption=text,
            reply_markup=reply_markup,
        )
    else:
        await message.answer(text, reply_markup=reply_markup)


async def _edit_city_inline(callback: CallbackQuery, text: str, reply_markup=None):
    msg = callback.message
    if not msg:
        await callback.answer()
        return
    try:
        if getattr(msg, "photo", None) or getattr(msg, "caption", None) is not None:
            await msg.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await msg.edit_text(text=text, reply_markup=reply_markup)
        return
    except Exception:
        pass
    await msg.answer(text, reply_markup=reply_markup)


def _root_reply_markup(player, user_id: int):
    return main_menu(
        player.location_slug,
        getattr(player, "current_district_slug", None),
        telegram_id=user_id,
    )


def _get_active_npc_order(player_id: int, npc_slug: str):
    active_orders = get_active_city_orders(player_id)
    quest_slugs = [slug for slug, data in NPC_QUEST_DEFS.items() if data["npc"] == npc_slug]
    for order in active_orders:
        if order["order_slug"] in quest_slugs:
            return order
    return None


def _npc_quest_ready(player_id: int, quest_slug: str) -> bool:
    quest = NPC_QUEST_DEFS[quest_slug]
    kind = quest["kind"]
    req = quest["requirements"]

    if kind == "items":
        inventory = get_inventory(player_id)
        return all(inventory.get(slug, 0) >= count for slug, count in req.items())

    if kind == "resources":
        resources = get_resources(player_id)
        return all(resources.get(slug, 0) >= count for slug, count in req.items())

    if kind == "monster":
        monsters = get_player_monsters(player_id)
        non_active = [m for m in monsters if not m.get("is_active")]
        return len(non_active) >= int(req.get("count", 1))

    return False


def _complete_npc_quest_requirements(player_id: int, quest_slug: str) -> bool:
    quest = NPC_QUEST_DEFS[quest_slug]
    kind = quest["kind"]
    req = quest["requirements"]

    if kind == "items":
        for slug, count in req.items():
            if not spend_item(player_id, slug, count):
                return False
        return True

    if kind == "resources":
        for slug, count in req.items():
            if not spend_resource(player_id, slug, count):
                return False
        return True

    if kind == "monster":
        for monster in get_player_monsters(player_id):
            if not monster.get("is_active"):
                return bool(remove_player_monster(player_id, int(monster["id"])))
        return False

    return False


def _grant_npc_quest_rewards(player_id: int, quest_slug: str):
    quest = NPC_QUEST_DEFS[quest_slug]
    add_player_gold(player_id, quest["reward_gold"])
    add_player_experience(player_id, quest["reward_exp"])


def _npc_status_label(player_id: int, npc_slug: str) -> str:
    """Оставлено для совместимости. Используй _npc_quest_button_label."""
    return _npc_quest_button_label(player_id, npc_slug)


def _npc_quest_button_label(player_id: int, npc_slug: str) -> str:
    """Текст кнопки поручения на главном экране NPC."""
    active = _get_active_npc_order(player_id, npc_slug)
    if active:
        if _npc_quest_ready(player_id, active["order_slug"]):
            return "✅ Поручение — готово к сдаче"
        return "🕒 Поручение — в процессе"
    remaining = _get_npc_quest_cooldown(player_id, npc_slug)
    if remaining > 0:
        return f"🕐 Поручение — через {_fmt_cooldown(remaining)}"
    return "📋 Посмотреть поручение"


def _reward_text(player_id: int, quests: list[dict]) -> str:
    parts = []
    for quest in quests:
        add_player_gold(player_id, quest["reward_gold"])
        add_player_experience(player_id, quest["reward_exp"])
        parts.append(
            f"📜 Квест выполнен: {quest['title']}\n"
            f"💰 Награда: +{quest['reward_gold']} золота\n"
            f"✨ Награда: +{quest['reward_exp']} опыта"
        )
    return "\n\n".join(parts)


def _mark_city_order_progress(player_id: int, resource_slug: str):
    rewards = []
    active_orders = get_active_city_orders(player_id)
    for order in active_orders:
        if order["order_slug"] == "herbalist_order" and resource_slug == "forest_herb":
            sold = int(order.get("progress", 0)) + 1
            if sold >= 3:
                complete_city_order(order["id"])
                rewards.append(CITY_BOARD_ORDER_DEFS["herbalist_order"])
        elif order["order_slug"] == "ore_order" and resource_slug == "ember_stone":
            sold = int(order.get("progress", 0)) + 1
            if sold >= 2:
                complete_city_order(order["id"])
                rewards.append(CITY_BOARD_ORDER_DEFS["ore_order"])
    return rewards


def _get_npc_quest_cooldown(player_id: int, npc_slug: str) -> int:
    """Возвращает оставшиеся секунды кулдауна после завершения NPC-квеста (0 = нет кулдауна)."""
    import time
    quest_slugs = [slug for slug, data in NPC_QUEST_DEFS.items() if data["npc"] == npc_slug]
    if not quest_slugs:
        return 0
    with get_connection() as conn:
        for quest_slug in quest_slugs:
            row = conn.execute(
                "SELECT completed_at FROM player_city_orders "
                "WHERE telegram_id=? AND order_slug=? AND status='completed' "
                "ORDER BY completed_at DESC LIMIT 1",
                (player_id, quest_slug)
            ).fetchone()
            if row and row["completed_at"]:
                elapsed = int(time.time()) - int(row["completed_at"])
                cooldown_secs = 86400
                if elapsed < cooldown_secs:
                    return cooldown_secs - elapsed
    return 0


def _fmt_cooldown(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours} ч. {minutes} мин."
    return f"{minutes} мин."


def _render_npc_quest_status_line(player_id: int, npc_slug: str) -> str:
    """Короткая строка статуса для главного экрана NPC (без описания)."""
    active = _get_active_npc_order(player_id, npc_slug)
    if active:
        quest_slug = active["order_slug"]
        if _npc_quest_ready(player_id, quest_slug):
            return "✅ Готово к сдаче"
        return f"🕒 Активно: {active['title']}"
    remaining = _get_npc_quest_cooldown(player_id, npc_slug)
    if remaining > 0:
        return f"🕐 Доступно через {_fmt_cooldown(remaining)}"
    return "📌 Есть поручение"


def render_npc_quest_detail(player_id: int, npc_slug: str) -> str:
    """Детальный экран поручения: описание + прогресс/статус + награда."""
    active = _get_active_npc_order(player_id, npc_slug)
    if active:
        quest_slug = active["order_slug"]
        quest_def = NPC_QUEST_DEFS.get(quest_slug, {})
        goal = quest_def.get("goal_text", active.get("goal_text", "Выполни условия."))
        reward_gold = active.get("reward_gold", 0)
        reward_exp = active.get("reward_exp", 0)
        ready = _npc_quest_ready(player_id, quest_slug)
        status = "✅ Условия выполнены! Нажми «Сдать»" if ready else "🕒 Выполняется..."
        return (
            f"📋 Поручение: {active['title']}\n"
            f"{'─' * 30}\n"
            f"{goal}\n\n"
            f"Статус: {status}\n\n"
            f"💰 Награда: {reward_gold} золота  ✨ {reward_exp} опыта"
        )
    remaining = _get_npc_quest_cooldown(player_id, npc_slug)
    if remaining > 0:
        return (
            f"✅ Поручение выполнено!\n\n"
            f"🕐 Следующее поручение будет доступно через {_fmt_cooldown(remaining)}.\n\n"
            f"Возвращайся позже."
        )
    quest_slug = next((slug for slug, data in NPC_QUEST_DEFS.items() if data["npc"] == npc_slug), None)
    if not quest_slug:
        return "Поручений пока нет."
    q = NPC_QUEST_DEFS[quest_slug]
    return (
        f"📋 Поручение: {q['title']}\n"
        f"{'─' * 30}\n"
        f"{q['goal_text']}\n\n"
        f"💰 Награда: {q['reward_gold']} золота  ✨ {q['reward_exp']} опыта\n\n"
        f"Нажми «Взять поручение», чтобы принять его."
    )


def npc_quest_detail_inline(player_id: int, npc_slug: str) -> InlineKeyboardMarkup:
    """Кнопки на детальном экране поручения."""
    active = _get_active_npc_order(player_id, npc_slug)
    back_cb = f"marketnpc:{npc_slug}_back"
    rows = []
    if active:
        quest_slug = active["order_slug"]
        if _npc_quest_ready(player_id, quest_slug):
            rows.append([InlineKeyboardButton(
                text="✅ Сдать поручение",
                callback_data=f"marketnpc:npc_quest_claim:{npc_slug}",
            )])
        else:
            rows.append([InlineKeyboardButton(text="🕒 Ещё не выполнено", callback_data="marketnpc:noop")])
    else:
        if _get_npc_quest_cooldown(player_id, npc_slug) <= 0:
            rows.append([InlineKeyboardButton(
                text="📌 Взять поручение",
                callback_data=f"marketnpc:npc_quest_take:{npc_slug}",
            )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _npc_take_or_claim_result(player_id: int, npc_slug: str):
    active = _get_active_npc_order(player_id, npc_slug)
    if not active:
        # Проверяем кулдаун — нельзя брать снова раньше 24ч
        remaining = _get_npc_quest_cooldown(player_id, npc_slug)
        if remaining > 0:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            if hours > 0:
                cd_str = f"{hours} ч. {minutes} мин."
            else:
                cd_str = f"{minutes} мин."
            return False, f"🕐 Следующее поручение доступно через {cd_str}"

        quest_slug = next((slug for slug, data in NPC_QUEST_DEFS.items() if data["npc"] == npc_slug), None)
        if not quest_slug:
            return False, "Поручение не найдено."
        quest = NPC_QUEST_DEFS[quest_slug]
        add_city_order(
            telegram_id=player_id,
            order_slug=quest_slug,
            title=quest["title"],
            goal_text=quest["goal_text"],
            reward_gold=quest["reward_gold"],
            reward_exp=quest["reward_exp"],
        )
        invalidate_quest_status_cache(player_id, npc_slug)
        return True, (
            f"📌 Поручение взято: {quest['title']}\n"
            f"📋 {quest['goal_text']}\n"
            f"💰 Награда: {quest['reward_gold']}з + {quest['reward_exp']} опыта"
        )

    quest_slug = active["order_slug"]
    if not _npc_quest_ready(player_id, quest_slug):
        quest_def = NPC_QUEST_DEFS.get(quest_slug, {})
        return False, f"🕒 Пока условия не выполнены.\n📋 {quest_def.get('goal_text', '')}"

    if not _complete_npc_quest_requirements(player_id, quest_slug):
        return False, "Не удалось списать требуемые ресурсы или предметы."

    complete_city_order(active["id"])
    _grant_npc_quest_rewards(player_id, quest_slug)
    invalidate_quest_status_cache(player_id, npc_slug)
    quest = NPC_QUEST_DEFS[quest_slug]
    return True, (
        f"✅ Поручение сдано: {quest['title']}\n"
        f"💰 +{quest['reward_gold']} золота\n"
        f"✨ +{quest['reward_exp']} опыта\n"
        f"🕐 Новое поручение будет доступно через 24 ч."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Board
# ──────────────────────────────────────────────────────────────────────────────

async def city_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    if not is_city(player.location_slug):
        await message.answer(
            "Ты сейчас не в городе.",
            reply_markup=_root_reply_markup(player, message.from_user.id),
        )
        return

    set_ui_screen(message.from_user.id, "city")
    text = (
        "🏙 Сереброград\n\n"
        f"Текущий район: {getattr(player, 'current_district_slug', 'city')}\n\n"
        "Выбери крупный городской раздел:\n"
        "• Торговый квартал — покупки, продажа и торговцы\n"
        "• Гильдии — поручения и профессии\n"
        "• Ремесленный квартал — алхимия, ловушки, мастерские\n"
        "• Главные ворота — выход из города"
    )
    await _answer_with_city_image(
        message,
        "city_square.png",
        text,
        city_menu(player.current_district_slug, message.from_user.id),
    )


async def city_board_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Доска заказов доступна только в городе.")
        return

    active_orders = get_active_city_orders(message.from_user.id)
    set_ui_screen(message.from_user.id, "board")

    text = (
        "📜 Доска заказов\n\n"
        "1) Заказ травника\n"
        "Продай 3 🌿 Лесная трава Борту в лавку ресурсов.\n"
        "Награда: 35 золота, 12 опыта\n\n"
        "2) Нужна руда для печей\n"
        "Продай 2 🔥 Угольный камень Борту в лавку ресурсов.\n"
        "Награда: 40 золота, 14 опыта\n\n"
        f"Активных заказов: {len(active_orders)}/{CITY_ORDER_LIMIT}"
    )
    await _answer_with_city_image(message, "bag_market.png", text, board_menu())


async def take_herbalist_order_handler(message: Message):
    await _take_city_order(message, "herbalist_order")


async def take_ore_order_handler(message: Message):
    await _take_city_order(message, "ore_order")


async def _take_city_order(message: Message, order_slug: str):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Доска заказов доступна только в городе.")
        return

    order_def = CITY_BOARD_ORDER_DEFS[order_slug]

    if has_active_city_order(message.from_user.id, order_slug):
        await message.answer(
            f"⚠️ Этот заказ уже активен:\n\n{order_def['title']}",
            reply_markup=board_menu(),
        )
        return

    active_count = count_active_city_orders(message.from_user.id)
    if active_count >= CITY_ORDER_LIMIT:
        await message.answer(
            f"⚠️ У тебя уже максимум активных городских заказов: {CITY_ORDER_LIMIT}.",
            reply_markup=board_menu(),
        )
        return

    add_city_order(
        telegram_id=message.from_user.id,
        order_slug=order_slug,
        title=order_def["title"],
        goal_text=order_def["goal_text"],
        reward_gold=order_def["reward_gold"],
        reward_exp=order_def["reward_exp"],
    )

    await message.answer(
        f"✅ Заказ взят: {order_def['title']}\n\n"
        f"Цель: {order_def['goal_text']}\n"
        f"Награда: {order_def['reward_gold']} золота, {order_def['reward_exp']} опыта",
        reply_markup=board_menu(),
    )


async def my_board_orders_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Доска заказов доступна только в городе.")
        return

    active_orders = get_active_city_orders(message.from_user.id)
    if not active_orders:
        await message.answer("📒 У тебя нет активных городских заказов.", reply_markup=board_menu())
        return

    lines = ["📒 Мои заказы", ""]
    for idx, order in enumerate(active_orders, start=1):
        lines.extend([
            f"{idx}. {order['title']}",
            f"Цель: {order['goal_text']}",
            f"Награда: {order['reward_gold']} золота, {order['reward_exp']} опыта",
            "",
        ])
    await message.answer("\n".join(lines), reply_markup=board_menu())


async def back_to_city_from_board_handler(message: Message):
    await city_handler(message)


# ──────────────────────────────────────────────────────────────────────────────
# Guilds
# ──────────────────────────────────────────────────────────────────────────────

def _guild_meta(profession: str) -> tuple[str, str]:
    mapping = {
        "hunter": (
            "🎯 Гильдия ловцов",
            "Здесь учат чувствовать момент для поимки и обращаться с ловушками.",
        ),
        "gatherer": (
            "🌿 Гильдия собирателей",
            "Здесь учат находить полезные травы и безопасно ходить в экспедиции.",
        ),
        "geologist": (
            "⛏ Гильдия геологов",
            "Здесь учат видеть жилы руды, камень и редкие кристаллы.",
        ),
        "alchemist": (
            "⚗ Гильдия алхимиков",
            "Здесь раскрывают секреты настоев, зелий и полевых эликсиров.",
        ),
    }
    return mapping.get(profession, ("Гильдия", ""))


def build_guild_inline_markup(telegram_id: int, profession: str):
    """
    Кнопки гильдии: все поручения открываются через детальный экран.
    Взять/Сдать — только на детальном экране, чтобы игрок видел описание перед взятием.
    """
    rows = []

    available = get_available_quests(telegram_id, profession)
    for q in available:
        rows.append([InlineKeyboardButton(
            text=f"📋 {q['title']}",
            callback_data=f"guild:detail:{profession}:{q['id']}",
        )])

    active = get_active_quests(telegram_id, profession)
    for q in active:
        if q.get("completed"):
            status = "✅"
        else:
            status = "🕒"
        rows.append([InlineKeyboardButton(
            text=f"{status} {q.get('title', 'Поручение')}",
            callback_data=f"guild:detail:{profession}:{q.get('id', q.get('quest_id', ''))}",
        )])

    if not rows:
        rows.append([InlineKeyboardButton(text="Поручений пока нет", callback_data="guild:noop:none:0")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_guild_quest_detail_inline(profession: str, quest_id: str, is_active: bool, is_completed: bool) -> InlineKeyboardMarkup:
    """Кнопки на детальном экране конкретного поручения гильдии."""
    rows = []
    if is_active:
        if is_completed:
            rows.append([InlineKeyboardButton(
                text="✅ Сдать поручение",
                callback_data=f"guild:claim:{profession}:{quest_id}",
            )])
        else:
            rows.append([InlineKeyboardButton(
                text="🕒 Ещё не выполнено",
                callback_data="guild:noop:none:0",
            )])
    else:
        rows.append([InlineKeyboardButton(
            text="📌 Взять поручение",
            callback_data=f"guild:take:{profession}:{quest_id}",
        )])
    rows.append([InlineKeyboardButton(
        text="⬅️ Назад к поручениям",
        callback_data=f"guild:back:{profession}",
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def city_guilds_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Гильдии доступны только в городе.")
        return

    update_player_district(message.from_user.id, "guild_quarter")
    set_ui_screen(message.from_user.id, "district")
    text = (
        "🏛 Квартал гильдий\n\n"
        "Здесь собраны профессиональные союзы Сереброграда.\n"
        "Выбери гильдию, чтобы посмотреть поручения и специализацию."
    )
    await _answer_with_city_image(
        message,
        "guild_hall.png",
        text,
        district_actions_menu("guild_quarter", message.from_user.id),
    )


async def guild_hunters_handler(message: Message):
    await _guild_handler(message, "hunter", "hunters_guild.png")


async def guild_gatherers_handler(message: Message):
    await _guild_handler(message, "gatherer", "guild_hall.png")


async def guild_geologists_handler(message: Message):
    await _guild_handler(message, "geologist", "guild_hall.png")


async def guild_alchemists_handler(message: Message):
    await _guild_handler(message, "alchemist", "guild_hall.png")


async def _guild_handler(message: Message, profession: str, image_name: str):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Гильдии доступны только в городе.")
        return

    set_ui_screen(message.from_user.id, "guilds")
    title, description = _guild_meta(profession)
    panel_text = render_guild_panel(message.from_user.id, profession, title, description)
    await _answer_with_city_image(
        message,
        image_name,
        panel_text,
        district_actions_menu("guild_quarter", message.from_user.id),
    )
    await message.answer(
        "📌 Поручения гильдии\nНажми кнопку ниже, чтобы взять или сдать поручение.",
        reply_markup=build_guild_inline_markup(message.from_user.id, profession),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Gate / leave city
# ──────────────────────────────────────────────────────────────────────────────

async def city_guard_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Стража доступна только в городе.")
        return

    update_player_district(message.from_user.id, "main_gate")
    set_ui_screen(message.from_user.id, "district")
    text = (
        "🛡 Городская стража\n\n"
        "Стражник напоминает: за воротами опасно.\n"
        "Подготовь сумку, расходники и выходи только если готов к пути."
    )
    await _answer_with_city_image(
        message,
        "city_square.png",
        text,
        district_actions_menu("main_gate", message.from_user.id),
    )


async def leave_city_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Ты и так не в городе.")
        return

    from game.travel_service import start_travel, LOCATION_NAMES

    travel = start_travel(
        message.from_user.id,
        player.location_slug,
        "dark_forest",
        agility=player.agility,
    )

    from_name = LOCATION_NAMES.get(player.location_slug, "Сереброград")
    to_name = LOCATION_NAMES.get("dark_forest", "Тёмный лес")

    await message.answer(
        f"🚶 Ты покидаешь {from_name}.\n"
        f"{from_name} → {to_name}\n"
        f"⏱ Время в пути: {travel['time_text']}\n\n"
        f"Во время перехода нельзя исследовать и сражаться.\n"
        f"Нажми 🚫 Отменить перемещение, если хочешь остаться.",
        reply_markup=main_menu(player.location_slug, player.current_district_slug, is_traveling=True, telegram_id=message.from_user.id),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Market quarter
# ──────────────────────────────────────────────────────────────────────────────

async def city_market_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Торговый квартал доступен только в городе.")
        return

    update_player_district(message.from_user.id, "market_square")
    set_ui_screen(message.from_user.id, "district")
    text = (
        "🏬 Торговый квартал\n\n"
        "Здесь находятся ключевые торговцы Сереброграда:\n"
        "• Мирна — сумки и снаряжение для походов\n"
        "• Варг — покупка и выкуп монстров\n"
        "• Борт — скупка и продажа ресурсов"
    )
    await _answer_with_city_image(
        message,
        "city_square.png",
        text,
        district_actions_menu("market_square", message.from_user.id),
    )


def mirna_main_inline(player_id: int):
    rows = [
        [InlineKeyboardButton(text="🛒 Купить сумки", callback_data="marketnpc:mirna_buy_menu")],
        [InlineKeyboardButton(text="🎒 Мои сумки", callback_data="marketnpc:mirna_bags_menu")],
        [InlineKeyboardButton(text="💰 Продать походные товары", callback_data="marketnpc:mirna_sell_menu")],
        [InlineKeyboardButton(text=_npc_quest_button_label(player_id, "mirna"), callback_data="marketnpc:npc_quest_detail:mirna")],
        [InlineKeyboardButton(text="⬅️ Назад в квартал", callback_data="marketnpc:district_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mirna_buy_inline():
    rows = []
    for slug, offer in BAG_OFFERS.items():
        rows.append([InlineKeyboardButton(
            text=f"🛒 {offer['name']} — {offer['capacity']} мест — {offer['price']}з",
            callback_data=f"marketnpc:mirna_buy:{slug}",
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к Мирне", callback_data="marketnpc:mirna_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mirna_bags_inline(player_id: int):
    rows = []
    for bag in get_player_bags(player_id):
        slug = bag["bag_slug"]
        title = f"{bag['bag_name']} • {bag['capacity']} мест"
        if bag.get("is_equipped"):
            rows.append([InlineKeyboardButton(text=f"✅ {title}", callback_data="marketnpc:mirna_bags_menu")])
        else:
            rows.append([
                InlineKeyboardButton(text=f"🎒 Надеть {title}", callback_data=f"marketnpc:mirna_bag_equip:{slug}"),
                InlineKeyboardButton(text="💰 Продать", callback_data=f"marketnpc:mirna_bag_sell:{slug}"),
            ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к Мирне", callback_data="marketnpc:mirna_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mirna_sell_inline(player_id: int):
    inventory = get_inventory(player_id)
    rows = []
    for slug, price in MIRNA_BUY_PRICES.items():
        qty = inventory.get(slug, 0)
        if qty <= 0:
            continue
        item = ITEMS.get(slug, {"name": slug.replace("_", " ").title()})
        rows.append([InlineKeyboardButton(
            text=f"💰 {item['name']} x{qty} — {price}з",
            callback_data=f"marketnpc:mirna_sell:{slug}",
        )])
    if not rows:
        rows.append([InlineKeyboardButton(text="Нет подходящих товаров", callback_data="marketnpc:noop")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к Мирне", callback_data="marketnpc:mirna_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def render_mirna_text(player_id: int) -> str:
    equipped = get_equipped_bag(player_id)
    equipped_line = f"Надета сейчас: {equipped['bag_name']} ({equipped['capacity']} мест)" if equipped else "Сумка пока не выбрана."
    quest_status = _render_npc_quest_status_line(player_id, "mirna")
    player = get_player(player_id)
    gold = player.gold if player else 0
    return (
        "🎒 Мирна — дорожная лавка\n\n"
        "У Мирны можно купить сумку, управлять своими сумками и продать часть походных расходников.\n\n"
        f"💰 Золото: {gold}з\n"
        f"{equipped_line}\n"
        f"Поручение: {quest_status}"
    )


def render_mirna_buy_text(player_id: int) -> str:
    lines = ["🛒 Мирна — покупка сумок", "", "Доступные сумки:"]
    equipped = get_equipped_bag(player_id)
    if equipped:
        lines.append(f"Сейчас надета: {equipped['bag_name']} ({equipped['capacity']} мест)")
        lines.append("")
    for offer in BAG_OFFERS.values():
        lines.append(f"• {offer['name']} — {offer['capacity']} мест — {offer['price']}з")
    return "\n".join(lines)


def render_mirna_bags_text(player_id: int) -> str:
    bags = get_player_bags(player_id)
    if not bags:
        return "🎒 У тебя пока нет сумок, кроме стартовой."
    lines = ["🎒 Мирна — твои сумки", ""]
    for bag in bags:
        marker = "✅ надета" if bag.get("is_equipped") else f"можно продать за {bag.get('sell_price', 0)}з"
        lines.append(f"• {bag['bag_name']} — {bag['capacity']} мест — {marker}")
    return "\n".join(lines)


def render_mirna_sell_text(player_id: int) -> str:
    inventory = get_inventory(player_id)
    lines = ["💰 Мирна выкупает походные товары", ""]
    any_items = False
    for slug, price in MIRNA_BUY_PRICES.items():
        qty = inventory.get(slug, 0)
        if qty > 0:
            any_items = True
            item = ITEMS.get(slug, {"name": slug.replace("_", " ").title()})
            lines.append(f"• {item['name']} — x{qty} — {price}з за штуку")
    if not any_items:
        lines.append("Подходящих товаров у тебя нет.")
    return "\n".join(lines)


async def city_bags_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Портная лавка доступна только в городе.")
        return
    set_ui_screen(message.from_user.id, "district")
    await _answer_with_city_image(
        message,
        "mirna_shop.png",
        render_mirna_text(message.from_user.id),
        mirna_main_inline(message.from_user.id),
    )


def varg_main_inline(player_id: int):
    rows = [
        [InlineKeyboardButton(text="🛒 Купить монстра", callback_data="marketnpc:varg_buy_menu")],
        [InlineKeyboardButton(text="💰 Продать монстра", callback_data="marketnpc:varg_sell_menu")],
        [InlineKeyboardButton(text=_npc_quest_button_label(player_id, "varg"), callback_data="marketnpc:npc_quest_detail:varg")],
        [InlineKeyboardButton(text="⬅️ Назад в квартал", callback_data="marketnpc:district_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def varg_buy_inline():
    rows = []
    for slug, offer in MONSTER_SHOP_OFFERS.items():
        rows.append([InlineKeyboardButton(
            text=f"🛒 {offer['name']} — {offer['base_price']}з",
            callback_data=f"marketnpc:varg_buy:{slug}",
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к Варгу", callback_data="marketnpc:varg_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def varg_sell_inline(player_id: int):
    rows = []
    for monster in get_player_monsters(player_id):
        if monster.get("is_active"):
            continue
        price = RARITY_SELL_BASE.get(monster.get("rarity", "common"), 20)
        rows.append([InlineKeyboardButton(
            text=f"💰 {monster['name']} — {price}з",
            callback_data=f"marketnpc:varg_sell:{monster['id']}",
        )])
    if not rows:
        rows.append([InlineKeyboardButton(text="Нет неактивных монстров", callback_data="marketnpc:noop")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к Варгу", callback_data="marketnpc:varg_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def render_varg_text(player_id: int) -> str:
    quest_status = _render_npc_quest_status_line(player_id, "varg")
    player = get_player(player_id)
    gold = player.gold if player else 0
    return (
        "🐲 Варг — рынок монстров\n\n"
        "Здесь можно купить стартового монстра для отряда или продать неактивных существ.\n\n"
        f"💰 Золото: {gold}з\n"
        f"Поручение: {quest_status}"
    )


def render_varg_buy_text() -> str:
    lines = ["🛒 Варг — покупка монстров", ""]
    for offer in MONSTER_SHOP_OFFERS.values():
        lines.append(
            f"• {offer['name']} — {offer['base_price']}з\n"
            f"  {offer['description']}"
        )
    return "\n".join(lines)


def render_varg_sell_text(player_id: int) -> str:
    lines = ["💰 Варг выкупает неактивных монстров", ""]
    any_monsters = False
    for monster in get_player_monsters(player_id):
        if monster.get("is_active"):
            continue
        any_monsters = True
        price = RARITY_SELL_BASE.get(monster.get("rarity", "common"), 20)
        lines.append(f"• {monster['name']} — {price}з")
    if not any_monsters:
        lines.append("У тебя нет неактивных монстров для продажи.")
    return "\n".join(lines)


async def city_monsters_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Лавка монстров доступна только в городе.")
        return
    set_ui_screen(message.from_user.id, "district")
    await _answer_with_city_image(
        message,
        "varg_shop.png",
        render_varg_text(message.from_user.id),
        varg_main_inline(message.from_user.id),
    )


def bort_main_inline(player_id: int):
    rows = [
        [InlineKeyboardButton(text="💰 Продать ресурсы", callback_data="marketnpc:bort_sell_menu")],
        [InlineKeyboardButton(text="🛒 Купить ресурсы", callback_data="marketnpc:bort_buy_menu")],
        [InlineKeyboardButton(text=_npc_quest_button_label(player_id, "bort"), callback_data="marketnpc:npc_quest_detail:bort")],
        [InlineKeyboardButton(text="⬅️ Назад в квартал", callback_data="marketnpc:district_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bort_sell_inline(player_id: int, city_slug: str):
    resources = get_resources(player_id)
    rows = []

    # Группируем ресурсы по типу и показываем цену продажи
    CATEGORY_ORDER = ["herb", "ore", "crystal", "trophy", "loot", "other"]
    CATEGORY_LABELS = {
        "herb": "🌿 Травы и растения",
        "ore":  "⛏ Руда и камни",
        "crystal": "💎 Кристаллы",
        "trophy": "🏆 Трофеи",
        "loot": "📦 Добыча",
        "other": "📦 Прочее",
    }

    def _get_category(slug: str) -> str:
        herb_keys = ["herb", "flower", "leaf", "moss", "spore", "root", "petal", "grass"]
        ore_keys = ["ore", "stone", "coal", "mineral", "rock"]
        crystal_keys = ["crystal", "gem", "shard", "jewel"]
        trophy_keys = ["trophy", "horn", "fang", "claw", "scale", "skin", "hide", "fur", "bone", "feather", "pearl"]
        s = slug.lower()
        if any(k in s for k in crystal_keys): return "crystal"
        if any(k in s for k in trophy_keys): return "trophy"
        if any(k in s for k in herb_keys): return "herb"
        if any(k in s for k in ore_keys): return "ore"
        return "other"

    from game.market_service import get_city_resource_sell_price
    categorized = {}
    for slug, qty in resources.items():
        if qty <= 0:
            continue
        cat = _get_category(slug)
        if cat not in categorized:
            categorized[cat] = []
        try:
            price = get_city_resource_sell_price(city_slug, slug, merchant_level=1, amount=1)
        except Exception:
            price = 0
        categorized[cat].append((slug, qty, price))

    if not categorized:
        rows.append([InlineKeyboardButton(text="Нет ресурсов для продажи", callback_data="marketnpc:noop")])
    else:
        # Кнопка «Продать всё» вверху
        rows.append([InlineKeyboardButton(
            text="💰 Продать всё сразу",
            callback_data="marketnpc:bort_sell_all",
        )])
        for cat in CATEGORY_ORDER:
            items = categorized.get(cat, [])
            if not items:
                continue
            rows.append([InlineKeyboardButton(
                text=CATEGORY_LABELS.get(cat, "📦 Прочее"),
                callback_data="marketnpc:noop"
            )])
            for slug, qty, price in sorted(items, key=lambda x: -x[1]):
                label = get_resource_label(slug)
                total_price = price * qty
                price_str = f"{total_price}з ({price}з/шт)" if price > 0 else "нет цены"
                rows.append([InlineKeyboardButton(
                    text=f"💰 {label} ×{qty} → {price_str}",
                    callback_data=f"marketnpc:bort_sell:{slug}",
                )])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Борту", callback_data="marketnpc:bort_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Категории ресурсов для магазина Борта
BORT_BUY_CATEGORIES = {
    "🌿 Травы и растения": ["forest_herb", "mushroom_cap", "silver_moss", "swamp_moss",
                            "toxic_spore", "field_grass", "sun_blossom", "bog_flower",
                            "ghost_reed", "ash_leaf"],
    "⛏ Руды и минералы":  ["ember_stone", "raw_ore", "granite_shard", "magma_core",
                            "sky_crystal", "dew_crystal", "dark_resin"],
    "🦴 Охотничий лут":   [],  # всё остальное — wildlife loot
}


def _bort_buy_categorize(market: dict) -> dict[str, list]:
    """Разбивает товары рынка по категориям."""
    categorized: dict[str, list] = {cat: [] for cat in BORT_BUY_CATEGORIES}
    known_slugs = set()
    for cat, slugs in BORT_BUY_CATEGORIES.items():
        if not slugs:
            continue
        for slug in slugs:
            if slug in market:
                entry = market[slug]
                if int(entry.get("stock", 0)) > 0:
                    categorized[cat].append((slug, entry))
                    known_slugs.add(slug)
    # Всё что не попало в явные категории — в охотничий лут
    for slug, entry in market.items():
        if slug not in known_slugs and int(entry.get("stock", 0)) > 0:
            categorized["🦴 Охотничий лут"].append((slug, entry))
    return categorized


def bort_buy_category_inline(city_slug: str, cat_index: int = 0) -> InlineKeyboardMarkup:
    """Магазин Борта: одна категория за раз с навигацией."""
    market = get_city_resource_market(city_slug)
    categorized = _bort_buy_categorize(market)
    # Фильтруем пустые категории
    filled = [(cat, items) for cat, items in categorized.items() if items]

    rows = []
    if not filled:
        rows.append([InlineKeyboardButton(text="Склад пуст", callback_data="marketnpc:noop")])
        rows.append([InlineKeyboardButton(text="⬅️ Назад к Борту", callback_data="marketnpc:bort_back")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    cat_index = max(0, min(cat_index, len(filled) - 1))
    cat_name, items = filled[cat_index]

    # Заголовок категории
    rows.append([InlineKeyboardButton(text=f"── {cat_name} ──", callback_data="marketnpc:noop")])

    # Товары текущей категории
    for slug, entry in items:
        price = entry.get("buy_price") or entry.get("price") or 0
        stock = int(entry.get("stock", 0))
        rows.append([InlineKeyboardButton(
            text=f"🛒 {get_resource_label(slug)} — {price}з ({stock}шт)",
            callback_data=f"marketnpc:bort_buy:{slug}",
        )])

    # Навигация по категориям
    nav_row = []
    if len(filled) > 1:
        prev_i = (cat_index - 1) % len(filled)
        next_i = (cat_index + 1) % len(filled)
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"marketnpc:bort_buy_cat:{prev_i}"))
        nav_row.append(InlineKeyboardButton(text=f"{cat_index+1}/{len(filled)}", callback_data="marketnpc:noop"))
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"marketnpc:bort_buy_cat:{next_i}"))
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="⬅️ Назад к Борту", callback_data="marketnpc:bort_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bort_buy_inline(city_slug: str):
    """Обёртка для обратной совместимости — открывает первую категорию."""
    return bort_buy_category_inline(city_slug, 0)


def render_bort_text(city_slug: str, player_id: int) -> str:
    resources = get_resources(player_id)
    total = sum(v for v in resources.values() if v > 0)
    quest_status = _render_npc_quest_status_line(player_id, "bort")
    player = get_player(player_id)
    gold = player.gold if player else 0
    return (
        "💰 Борт — склад и лавка ресурсов\n\n"
        "Здесь можно продавать добычу и выкупать ресурсы с городского рынка.\n\n"
        f"💰 Золото: {gold}з\n"
        f"Ресурсов у тебя: {total}\n"
        f"Поручение: {quest_status}"
    )


def render_bort_buy_text(city_slug: str, player_id: int) -> str:
    """Текст экрана покупки ресурсов у Борта."""
    player = get_player(player_id)
    gold = player.gold if player else 0
    market = get_city_resource_market(city_slug)
    in_stock = sum(1 for e in market.values() if int(e.get("stock", 0)) > 0)
    return (
        "🛒 Борт — купить ресурсы\n\n"
        f"💰 Твой баланс: {gold}з\n"
        f"Позиций на складе: {in_stock}\n\n"
        "Выбери категорию и нажми на ресурс — купишь 1 штуку.\n"
        "Переключай категории стрелками ◀️ ▶️."
    )


async def city_buyer_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Лавка ресурсов доступна только в городе.")
        return
    set_ui_screen(message.from_user.id, "district")
    await _answer_with_city_image(
        message,
        "bort_shop.png",
        render_bort_text(player.location_slug, message.from_user.id),
        bort_main_inline(message.from_user.id),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Craft quarter
# ──────────────────────────────────────────────────────────────────────────────

async def city_craft_quarter_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Ремесленный квартал доступен только в городе.")
        return

    set_ui_screen(message.from_user.id, "district")
    update_player_district(message.from_user.id, "craft_quarter")
    text = (
        "⚒ Ремесленный квартал\n\n"
        "Здесь можно варить зелья, собирать ловушки и работать с мастерскими."
    )
    await _answer_with_city_image(
        message,
        "alchemy_lab.png",
        text,
        district_actions_menu("craft_quarter", message.from_user.id),
    )


async def city_alchemy_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return

    resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "craft")
    await message.answer(render_craft_text(player, resources), reply_markup=craft_menu(player, resources))


async def city_traps_handler(message: Message):
    player = get_player(message.from_user.id)
    if not player or not is_city(player.location_slug):
        await message.answer("Мастер ловушек доступен только в городе.")
        return

    resources = get_resources(message.from_user.id)
    set_ui_screen(message.from_user.id, "traps")

    rows = []
    hunter_level = getattr(player, "hunter_level", 1)
    for slug, recipe in TRAP_RECIPES.items():
        if recipe["hunter_level"] > hunter_level:
            continue
        has_mats = all(resources.get(r, 0) >= qty for r, qty in recipe["ingredients"].items())
        can_afford = player.gold >= recipe["gold_cost"]
        status = "✅" if (has_mats and can_afford) else "❌"
        rows.append([InlineKeyboardButton(
            text=f"{status} {recipe['name']} — {recipe['gold_cost']}з",
            callback_data=f"trap:craft:{slug}",
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="trap:back")])

    await _answer_with_city_image(
        message,
        "trap_workshop.png",
        render_trap_shop(player, resources),
        district_actions_menu("craft_quarter", message.from_user.id),
    )
    await message.answer("Выбери предмет для крафта:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


# ──────────────────────────────────────────────────────────────────────────────
# Inline callbacks
# ──────────────────────────────────────────────────────────────────────────────

async def trap_inline_callback(callback: CallbackQuery):
    data = callback.data or ""
    uid = callback.from_user.id

    if data == "trap:back":
        await callback.answer()
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    if data.startswith("trap:craft:"):
        slug = data.split(":", 2)[2]
        player = get_player(uid)
        if not player:
            await callback.answer("Сначала напиши /start", show_alert=True)
            return

        resources = get_resources(uid)
        result = craft_trap_item(player, resources, slug)
        if not result["ok"]:
            await callback.answer(result["msg"], show_alert=True)
            return

        from database.repositories import spend_resource as _spend_resource, add_item, improve_profession_from_action
        for res_slug, qty in result["ingredients"].items():
            _spend_resource(uid, res_slug, qty)
        add_player_gold(uid, -result["gold_cost"])
        add_item(uid, result["item"], result["amount"])
        improve_profession_from_action(uid, "hunter")
        msg_craft = f"🪤 {result['msg']} | 💰 -{result['gold_cost']}з | +{result['amount']}шт"
        await callback.answer(msg_craft[:200], show_alert=True)
        return

    await callback.answer()


async def market_inline_callback(callback: CallbackQuery):
    player = get_player(callback.from_user.id)
    if not player:
        await callback.answer("Сначала напиши /start", show_alert=True)
        return

    data = callback.data or ""
    uid = callback.from_user.id

    if data == "marketnpc:noop":
        await callback.answer()
        return

    # ── Детальный экран поручения NPC ─────────────────────────────────────────
    if data.startswith("marketnpc:npc_quest_detail:"):
        npc_slug = data.split(":")[-1]
        await _edit_city_inline(callback, render_npc_quest_detail(uid, npc_slug), npc_quest_detail_inline(uid, npc_slug))
        await callback.answer()
        return

    if data.startswith("marketnpc:npc_quest_take:"):
        npc_slug = data.split(":")[-1]
        ok, msg = _npc_take_or_claim_result(uid, npc_slug)
        await callback.answer(msg[:200], show_alert=ok)
        # После взятия — остаёмся на детальном экране (теперь с прогрессом)
        await _edit_city_inline(callback, render_npc_quest_detail(uid, npc_slug), npc_quest_detail_inline(uid, npc_slug))
        return

    if data.startswith("marketnpc:npc_quest_claim:"):
        npc_slug = data.split(":")[-1]
        ok, msg = _npc_take_or_claim_result(uid, npc_slug)
        await callback.answer(msg[:200], show_alert=ok)
        # После сдачи — показываем детальный экран (кулдаун или новое)
        await _edit_city_inline(callback, render_npc_quest_detail(uid, npc_slug), npc_quest_detail_inline(uid, npc_slug))
        return

    if data == "marketnpc:district_back":
        await callback.answer()
        await callback.message.answer(
            "🏬 Возврат в торговый квартал.",
            reply_markup=district_actions_menu("market_square", uid),
        )
        return

    # Мирна
    if data == "marketnpc:mirna_back":
        await _edit_city_inline(callback, render_mirna_text(uid), mirna_main_inline(uid))
        await callback.answer()
        return
    if data == "marketnpc:mirna_buy_menu":
        await _edit_city_inline(callback, render_mirna_buy_text(uid), mirna_buy_inline())
        await callback.answer()
        return
    if data == "marketnpc:mirna_bags_menu":
        await _edit_city_inline(callback, render_mirna_bags_text(uid), mirna_bags_inline(uid))
        await callback.answer()
        return
    if data == "marketnpc:mirna_sell_menu":
        await _edit_city_inline(callback, render_mirna_sell_text(uid), mirna_sell_inline(uid))
        await callback.answer()
        return
    if data == "marketnpc:mirna_quest":
        # Legacy — redirect to detail screen
        await _edit_city_inline(callback, render_npc_quest_detail(uid, "mirna"), npc_quest_detail_inline(uid, "mirna"))
        await callback.answer()
        return
    if data.startswith("marketnpc:mirna_buy:"):
        slug = data.split(":")[-1]
        offer = BAG_OFFERS.get(slug)
        if not offer:
            await callback.answer("Товар не найден.", show_alert=True)
            return
        if player.gold < offer["price"]:
            await callback.answer("Недостаточно золота.", show_alert=True)
            return
        added, bag = grant_bag(
            uid,
            slug,
            offer["name"],
            offer["capacity"],
            source="shop",
            sell_price=max(1, offer["price"] // 2),
            auto_equip=True,
        )
        if not added:
            await callback.answer("Такая сумка у тебя уже есть.", show_alert=True)
            return
        add_player_gold(uid, -offer["price"])
        await callback.answer(f"🎒 Куплена {offer['name']}", show_alert=False)
        await _edit_city_inline(callback, render_mirna_buy_text(uid), mirna_buy_inline())
        return
    if data.startswith("marketnpc:mirna_bag_equip:"):
        slug = data.split(":")[-1]
        if equip_bag(uid, slug):
            await callback.answer("✅ Сумка надета")
        else:
            await callback.answer("Не удалось надеть сумку", show_alert=True)
        await _edit_city_inline(callback, render_mirna_bags_text(uid), mirna_bags_inline(uid))
        return
    if data.startswith("marketnpc:mirna_bag_sell:"):
        slug = data.split(":")[-1]
        gold = sell_bag(uid, slug)
        if gold is None:
            await callback.answer("Эту сумку нельзя продать.", show_alert=True)
            return
        await callback.answer(f"💰 Получено {gold} золота", show_alert=False)
        await _edit_city_inline(callback, render_mirna_bags_text(uid), mirna_bags_inline(uid))
        return
    if data.startswith("marketnpc:mirna_sell:"):
        slug = data.split(":")[-1]
        price = MIRNA_BUY_PRICES.get(slug)
        if not price:
            await callback.answer("Неизвестный товар.", show_alert=True)
            return
        if not spend_item(uid, slug, 1):
            await callback.answer("У тебя нет этого товара.", show_alert=True)
            return
        add_player_gold(uid, price)
        await callback.answer(f"💰 Продано за {price}з", show_alert=False)
        await _edit_city_inline(callback, render_mirna_sell_text(uid), mirna_sell_inline(uid))
        return

       # Варг
    if data == "marketnpc:varg_back":
        await _edit_city_inline(callback, render_varg_text(uid), varg_main_inline(uid))
        await callback.answer()
        return

    if data == "marketnpc:varg_buy_menu":
        await _edit_city_inline(callback, render_varg_buy_text(), varg_buy_inline())
        await callback.answer()
        return

    if data == "marketnpc:varg_sell_menu":
        await _edit_city_inline(callback, render_varg_sell_text(uid), varg_sell_inline(uid))
        await callback.answer()
        return

    if data == "marketnpc:varg_quest":
        await _edit_city_inline(callback, render_npc_quest_detail(uid, "varg"), npc_quest_detail_inline(uid, "varg"))
        await callback.answer()
        return

    if data.startswith("marketnpc:varg_buy:"):
        slug = data.split(":")[-1]
        offer = MONSTER_SHOP_OFFERS.get(slug)

        if not offer:
            await callback.answer("Монстр недоступен.", show_alert=True)
            return

        # 🔥 проверка кристалла ДО покупки
        try:
            from game.crystal_service import can_receive_monster

            preview = {
                "name": offer["name"],
                "rarity": offer.get("rarity", "common"),
                "level": 1,
                "hp": offer.get("hp", 1),
                "max_hp": offer.get("hp", 1),
                "attack": offer.get("attack", 1),
                "mood": offer.get("mood", "instinct"),
            }

            can_store, store_msg, target_crystal = can_receive_monster(uid, monster=preview)
        except Exception:
            can_store, store_msg, target_crystal = True, "", None

        if not can_store:
            await callback.answer(store_msg or "❌ Нет свободных кристаллов!", show_alert=True)
            return

        # покупка
        price = purchase_market_monster(uid, slug)
        if price is None:
            await callback.answer("❌ Недостаточно золота.", show_alert=True)
            return

        captured = add_captured_monster(
            telegram_id=uid,
            name=offer["name"],
            rarity=offer["rarity"],
            mood=offer["mood"],
            hp=offer["hp"],
            attack=offer["attack"],
            source_type="рынок",
        )

        # кладём в кристалл
        try:
            from game.crystal_service import store_monster_in_crystal

            ok, msg = store_monster_in_crystal(
                uid,
                captured["id"],
                target_crystal["id"] if target_crystal else None,
            )

            if not ok:
                remove_player_monster(uid, captured["id"])
                add_player_gold(uid, price)
                
                await callback.answer("❌ Не удалось поместить монстра в кристалл.", show_alert=True)
                return

        except Exception:
            pass

        await callback.answer(f"🐲 Куплен {offer['name']}", show_alert=False)
        await _edit_city_inline(callback, render_varg_buy_text(), varg_buy_inline())
        return

    if data.startswith("marketnpc:varg_sell:"):
        monster_id = int(data.split(":")[-1])

        target = None
        for monster in get_player_monsters(uid):
            if int(monster["id"]) == monster_id and not monster.get("is_active"):
                target = monster
                break

        if not target:
            await callback.answer("Монстр не найден или активен.", show_alert=True)
            return

        price = RARITY_SELL_BASE.get(target.get("rarity", "common"), 20)

        if not remove_player_monster(uid, monster_id):
            await callback.answer("Не удалось продать монстра.", show_alert=True)
            return

        add_player_gold(uid, price)

        await callback.answer(f"💰 Получено {price}з", show_alert=False)
        await _edit_city_inline(callback, render_varg_sell_text(uid), varg_sell_inline(uid))
        return

    # Борт
    if data == "marketnpc:bort_back":
        await _edit_city_inline(callback, render_bort_text(player.location_slug, uid), bort_main_inline(uid))
        await callback.answer()
        return
    if data == "marketnpc:bort_sell_menu":
        await _edit_city_inline(callback, render_bort_text(player.location_slug, uid), bort_sell_inline(uid, player.location_slug))
        await callback.answer()
        return
    if data == "marketnpc:bort_buy_menu":
        await _edit_city_inline(callback, render_bort_buy_text(player.location_slug, uid), bort_buy_category_inline(player.location_slug, 0))
        await callback.answer()
        return

    if data.startswith("marketnpc:bort_buy_cat:"):
        try:
            cat_i = int(data.split(":")[-1])
        except ValueError:
            cat_i = 0
        await _edit_city_inline(callback, render_bort_buy_text(player.location_slug, uid), bort_buy_category_inline(player.location_slug, cat_i))
        await callback.answer()
        return
    if data == "marketnpc:bort_quest":
        await _edit_city_inline(callback, render_npc_quest_detail(uid, "bort"), npc_quest_detail_inline(uid, "bort"))
        await callback.answer()
        return
    if data == "marketnpc:bort_sell_all":
        # Продаём все ресурсы разом
        from database.repositories import get_resources as _get_res_all
        _all_res = _get_res_all(uid)
        total_gold_all = 0
        sold_items = []
        for _slug, _qty in list(_all_res.items()):
            if _qty <= 0:
                continue
            for _ in range(int(_qty)):
                _g = sell_resource_to_city_market(uid, player.location_slug, _slug, 1)
                if _g and _g > 0:
                    total_gold_all += _g
                else:
                    break
            if _g and _g > 0:
                sold_items.append(get_resource_label(_slug))
        if total_gold_all > 0:
            await callback.answer(f"💰 Продано всё за {total_gold_all}з", show_alert=True)
        else:
            await callback.answer("Нечего продавать или нет цен.", show_alert=True)
        await _edit_city_inline(callback, render_bort_text(player.location_slug, uid), bort_sell_inline(uid, player.location_slug))
        return

    if data.startswith("marketnpc:bort_sell:"):
        slug = data.split(":")[-1]
        # Продаём всё количество сразу
        from database.repositories import get_resources as _get_res
        _res = _get_res(uid)
        qty_to_sell = int(_res.get(slug, 0))
        if qty_to_sell <= 0:
            await callback.answer("Ресурс закончился.", show_alert=True)
            return
        total_gold = 0
        rewards = []
        for _ in range(qty_to_sell):
            gold = sell_resource_to_city_market(uid, player.location_slug, slug, 1)
            if gold is None or gold <= 0:
                break
            total_gold += gold
            rewards += _mark_city_order_progress(uid, slug)
        if total_gold <= 0:
            await callback.answer("Этот ресурс нельзя продать.", show_alert=True)
            return
        popup = f"💰 Продано {qty_to_sell}×{get_resource_label(slug)} за {total_gold}з"
        if rewards:
            popup += " | " + " ".join(r["title"] for r in rewards)
        await callback.answer(popup[:200], show_alert=False)
        await _edit_city_inline(callback, render_bort_text(player.location_slug, uid), bort_sell_inline(uid, player.location_slug))
        return
    if data.startswith("marketnpc:bort_buy:"):
        slug = data.split(":")[-1]
        price = buy_resource_from_city_market(uid, player.location_slug, slug, 1)
        if price is None:
            await callback.answer("Недостаточно золота или склад пуст.", show_alert=True)
            return
        await callback.answer(f"🛒 Куплено за {price}з", show_alert=False)
        await _edit_city_inline(callback, render_bort_buy_text(player.location_slug, uid), bort_buy_category_inline(player.location_slug, 0))
        return

    await callback.answer()
