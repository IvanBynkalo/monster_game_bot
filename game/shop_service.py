from database.repositories import get_market_item_price, get_market_monster_price, get_market_item_entry, get_market_monster_entry

ITEM_ORDER = ["small_potion", "energy_capsule", "basic_trap"]

MONSTER_SHOP_OFFERS = {
    "forest_sprite": {"name": "Лесной спрайт", "rarity": "rare", "mood": "inspiration", "monster_type": "nature", "hp": 30, "attack": 7, "base_price": 90, "description": "Гибкий стартовый монстр поддержки."},
    "swamp_hunter": {"name": "Болотный охотник", "rarity": "rare", "mood": "instinct", "monster_type": "shadow", "hp": 32, "attack": 8, "base_price": 105, "description": "Хорош для поимки и охоты в болотах."},
    "ember_fang": {"name": "Угольный клык", "rarity": "epic", "mood": "rage", "monster_type": "flame", "hp": 38, "attack": 10, "base_price": 160, "description": "Агрессивный боевой монстр для раннего прогресса."},
}

RARITY_LABELS = {"common": "Обычный", "rare": "Редкий", "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический"}
MOOD_LABELS = {"rage": "Ярость", "fear": "Страх", "instinct": "Инстинкт", "inspiration": "Вдохновение"}
TYPE_LABELS = {"flame": "Пламя", "shadow": "Тень", "nature": "Природа", "spirit": "Дух", "bone": "Кость", "storm": "Буря", "void": "Пустота", "echo": "Эхо"}

def _trend_text(base_price: int, current_price: int) -> str:
    if current_price > base_price:
        return "📈 Цена выше базовой"
    if current_price < base_price:
        return "📉 Цена ниже базовой"
    return "➖ Базовая цена"

def render_shop_menu_text():
    return "🏪 Городской рынок\n\nЗдесь цены зависят от спроса среди игроков. Чем чаще покупают товар, тем он дороже. Если спрос падает, цена постепенно снижается."

def render_item_shop_text():
    lines = ["🧪 Магазин предметов", ""]
    labels = {
        "small_potion": ("🧪", "Малое зелье", "Лечит активного монстра на 12 HP."),
        "energy_capsule": ("⚡", "Капсула энергии", "Восстанавливает 3 энергии."),
        "basic_trap": ("🪤", "Простая ловушка", "Даёт +15% к шансу поимки в бою."),
    }
    for slug in ITEM_ORDER:
        emoji, name, desc = labels[slug]
        entry = get_market_item_entry(slug)
        price = get_market_item_price(slug)
        lines.extend([f"{emoji} {name}", f"Цена: {price} золота", desc, _trend_text(entry['base_price'], price), ""])
    lines.append("Используй кнопки ниже для покупки.")
    return "\n".join(lines)

def render_monster_shop_text():
    lines = ["🐲 Магазин монстров", ""]
    for slug, offer in MONSTER_SHOP_OFFERS.items():
        entry = get_market_monster_entry(slug)
        price = get_market_monster_price(slug)
        lines.extend([
            f"{offer['name']} | {RARITY_LABELS.get(offer['rarity'], offer['rarity'])}",
            f"Эмоция: {MOOD_LABELS.get(offer['mood'], offer['mood'])}",
            f"Тип: {TYPE_LABELS.get(offer['monster_type'], offer['monster_type'])}",
            f"HP: {offer['hp']} | Атака: {offer['attack']}",
            offer["description"],
            f"Цена: {price} золота",
            _trend_text(entry['base_price'], price),
            "",
        ])
    lines.append("Используй кнопки ниже для покупки монстров.")
    return "\n".join(lines)
