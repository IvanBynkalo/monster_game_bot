from database.repositories import (
    get_city_resource_buy_price,
    get_city_resource_market,
    get_city_resource_sell_price,
)

RESOURCE_LABELS = {
    "forest_herb": "🌿 Лесная трава",
    "mushroom_cap": "🍄 Шляпка гриба",
    "silver_moss": "✨ Серебряный мох",
    "swamp_moss": "🪴 Болотный мох",
    "toxic_spore": "🧫 Токсичная спора",
    "black_pearl": "⚫ Чёрная жемчужина тины",
    "ember_stone": "🔥 Угольный камень",
    "ash_leaf": "🍂 Пепельный лист",
    "magma_core": "💠 Ядро магмы",
    "field_grass": "🌾 Полевая трава",
    "sun_blossom": "🌼 Солнечный цветок",
    "dew_crystal": "💧 Кристалл росы",
    "raw_ore": "⛏ Сырая руда",
    "granite_shard": "🪨 Осколок гранита",
    "sky_crystal": "💎 Небесный кристалл",
    "bog_flower": "🪷 Болотный цветок",
    "dark_resin": "🕯 Тёмная смола",
    "ghost_reed": "🎐 Призрачный камыш",
}

BAG_OFFERS = {
    "waist_bag": {"name": "Поясная сумка", "capacity": 16, "price": 45},
    "field_pack": {"name": "Полевой ранец", "capacity": 24, "price": 95},
    "expedition_backpack": {"name": "Экспедиционный рюкзак", "capacity": 36, "price": 180},
}


def get_resource_label(slug: str) -> str:
    """Возвращает читаемое название ресурса. Проверяет оба словаря."""
    label = RESOURCE_LABELS.get(slug)
    if label:
        return label
    # Проверяем craft_service (содержит охотничий лут)
    try:
        from game.craft_service import RESOURCE_LABELS as CRAFT_LABELS
        label = CRAFT_LABELS.get(slug)
        if label:
            return label
    except Exception:
        pass
    # Красиво форматируем slug как fallback
    return slug.replace("_", " ").title()


def make_sell_button_text(slug: str, city_slug: str, merchant_level: int, player_qty: int) -> str:
    price = get_city_resource_sell_price(city_slug, slug, merchant_level=merchant_level, amount=1)
    return f"💰 Продать: {get_resource_label(slug)} • {price}з • x{player_qty}"


def make_buy_button_text(slug: str, city_slug: str, stock: int | float) -> str:
    price = get_city_resource_buy_price(city_slug, slug, amount=1)
    visible_stock = int(stock)
    return f"🛒 Купить ресурс: {get_resource_label(slug)} • {price}з • {visible_stock}шт"


def get_resource_slug_from_sell_button(text: str) -> str | None:
    text = (text or "").strip()
    for slug, label in RESOURCE_LABELS.items():
        if text.startswith(f"💰 Продать: {label}"):
            return slug
    return None


def get_resource_slug_from_buy_button(text: str) -> str | None:
    text = (text or "").strip()
    for slug, label in RESOURCE_LABELS.items():
        if text.startswith(f"🛒 Купить ресурс: {label}"):
            return slug
    return None


def _stock_state_text(stock: float, target: float) -> str:
    if stock <= max(1, target * 0.35):
        return "📈 Дефицит"
    if stock >= target * 1.8:
        return "📉 Рынок переполнен"
    return "➖ Рынок стабилен"


def render_resource_sell_text(city_slug: str, resources: dict, merchant_level: int):
    lines = ["💰 Скупщик ресурсов", ""]
    lines.append("Здесь можно продать добычу. Цена зависит от запаса товара на рынке этого города.")
    lines.append("Чем больше товара уже у скупщика, тем ниже цена выкупа.")
    lines.append("")

    shown = False
    market = get_city_resource_market(city_slug)

    for slug, qty in resources.items():
        if qty <= 0:
            continue

        entry = market.get(slug)
        if not entry:
            continue

        shown = True
        price = get_city_resource_sell_price(city_slug, slug, merchant_level=merchant_level, amount=1)

        lines.append(f"{get_resource_label(slug)}")
        lines.append(f"У тебя: {qty} шт.")
        lines.append(f"Цена выкупа: {price} золота за 1 шт.")
        lines.append(f"Запас у скупщика: {int(entry['stock'])} шт.")
        lines.append(_stock_state_text(float(entry["stock"]), float(entry["target_stock"])))
        lines.append("")

    if not shown:
        lines.append("У тебя нет ресурсов для продажи.")

    return "\n".join(lines)


def render_resource_buy_text(city_slug: str):
    lines = ["🛒 Покупка ресурсов", ""]
    lines.append("Это общий городской склад. Всё, что продают игроки в этом городе, попадает сюда.")
    lines.append("Чем товара меньше, тем дороже его покупка.")
    lines.append("")

    market = get_city_resource_market(city_slug)
    has_stock = False

    for slug, entry in market.items():
        stock = int(entry.get("stock", 0))
        if stock <= 0:
            continue

        has_stock = True
        price = get_city_resource_buy_price(city_slug, slug, amount=1)

        lines.append(f"{get_resource_label(slug)}")
        lines.append(f"Цена покупки: {price} золота за 1 шт.")
        lines.append(f"В наличии: {stock} шт.")
        lines.append(_stock_state_text(float(entry["stock"]), float(entry["target_stock"])))
        lines.append("")

    if not has_stock:
        lines.append("На складе сейчас нет ресурсов.")

    return "\n".join(lines)


def render_bag_shop_text(player):
    lines = [
        "🎒 Лавка сумок",
        "",
        f"Текущая вместимость: {player.bag_capacity}",
        f"Золото: {player.gold}",
        "",
        "Доступные сумки:",
        "",
    ]

    for offer in BAG_OFFERS.values():
        better = "✅ Можно улучшить" if offer["capacity"] > player.bag_capacity else "— уже не лучше текущей"
        lines.append(
            f"{offer['name']} — {offer['capacity']} мест — {offer['price']} золота {better}"
        )

    return "\n".join(lines)
