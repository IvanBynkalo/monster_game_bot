"""
Telegram Stars — монетизация через встроенные платежи (рекомендация #14).
"""
from aiogram import Bot
from aiogram.types import LabeledPrice, Message

# Stars → игровые эффекты
STARS_CATALOG = {
    "rage_flask": {
        "title":       "🔥 Флакон ярости",
        "description": "Даёт 5 очков Ярости мгновенно",
        "stars":       50,
        "effect":      {"emotion": "rage", "amount": 5},
    },
    "fear_flask": {
        "title":       "😱 Флакон страха",
        "description": "Даёт 5 очков Страха мгностно",
        "stars":       50,
        "effect":      {"emotion": "fear", "amount": 5},
    },
    "inspiration_flask": {
        "title":       "✨ Флакон вдохновения",
        "description": "Даёт 5 очков Вдохновения",
        "stars":       50,
        "effect":      {"emotion": "inspiration", "amount": 5},
    },
    "joy_flask": {
        "title":       "🌟 Флакон радости",
        "description": "Даёт 5 очков Радости и +30 золота",
        "stars":       60,
        "effect":      {"emotion": "joy", "amount": 5, "gold_bonus": 30},
    },
    "energy_boost": {
        "title":       "⚡ Заряд энергии",
        "description": "Восстанавливает 5 единиц энергии",
        "stars":       40,
        "effect":      {"energy": 5},
    },
    "monster_slot": {
        "title":       "🐲 Слот для монстра",
        "description": "Постоянно добавляет 1 слот в команду",
        "stars":       100,
        "effect":      {"extra_slot": 1},
    },
    "bag_upgrade": {
        "title":       "🎒 Улучшение сумки",
        "description": "Увеличивает вместимость сумки на 8",
        "stars":       80,
        "effect":      {"bag_capacity": 8},
    },
    "season_pass": {
        "title":       "🎫 Сезонный пасс",
        "description": "Открывает премиум-трек сезонных наград",
        "stars":       300,
        "effect":      {"season_pass": True},
    },
}


def render_stars_shop() -> str:
    lines = ["⭐ Магазин Stars\n"]
    for slug, item in STARS_CATALOG.items():
        lines.append(f"• {item['title']} — {item['stars']} ⭐")
        lines.append(f"  {item['description']}")
    lines.append("\nЧтобы купить, отправь: /buy_stars <название>")
    return "\n".join(lines)


async def send_stars_invoice(bot: Bot, chat_id: int, item_slug: str) -> bool:
    item = STARS_CATALOG.get(item_slug)
    if not item:
        return False
    await bot.send_invoice(
        chat_id=chat_id,
        title=item["title"],
        description=item["description"],
        payload=f"stars:{item_slug}",
        currency="XTR",
        prices=[LabeledPrice(label=item["title"], amount=item["stars"])],
    )
    return True


async def process_stars_purchase(telegram_id: int, payload: str) -> str:
    """Вызывается после успешной оплаты в pre_checkout_query."""
    if not payload.startswith("stars:"):
        return ""
    item_slug = payload[6:]
    item      = STARS_CATALOG.get(item_slug)
    if not item:
        return "Неизвестный товар."

    from database.repositories import add_emotions, add_player_gold, _update_player_field, track
    effect = item["effect"]
    lines  = [f"✅ Покупка подтверждена: {item['title']}\n"]

    if "emotion" in effect:
        add_emotions(telegram_id, {effect["emotion"]: effect["amount"]})
        from game.emotion_service import EMOTION_LABELS
        lines.append(f"+{effect['amount']} {EMOTION_LABELS.get(effect['emotion'], effect['emotion'])}")

    if "gold_bonus" in effect:
        add_player_gold(telegram_id, effect["gold_bonus"])
        lines.append(f"+{effect['gold_bonus']} золота")

    if "energy" in effect:
        from database.repositories import restore_player_energy
        restore_player_energy(telegram_id, effect["energy"], max_energy=15)
        lines.append(f"+{effect['energy']} энергии")

    if "bag_capacity" in effect:
        from database.repositories import get_player
        p = get_player(telegram_id)
        if p:
            _update_player_field(telegram_id, bag_capacity=p.bag_capacity + effect["bag_capacity"])
        lines.append(f"+{effect['bag_capacity']} вместимости сумки")

    if effect.get("season_pass"):
        _update_player_field(telegram_id, season_pass_active=1)
        lines.append("Сезонный пасс активирован!")

    track(telegram_id, "stars_purchase", {"item": item_slug, "stars": item["stars"]})
    return "\n".join(lines)
