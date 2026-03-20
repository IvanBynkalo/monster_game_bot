"""
P2P-рынок монстров с комиссией 8% (рекомендация #16).
Игроки выставляют своих уникальных монстров на продажу.
"""
from database.repositories import (
    get_player, get_monster_by_id, get_player_monsters,
    list_monster_for_sale, delist_monster, get_p2p_market_listings,
    buy_p2p_monster as _buy, track,
)

COMMISSION_RATE  = 0.08  # 8% комиссии разработчику
MIN_LISTING_PRICE = 10
MAX_LISTING_PRICE = 50_000
LISTING_EXPIRES_HOURS = 72

RARITY_ORDER = {"common": 0, "rare": 1, "epic": 2, "legendary": 3, "mythic": 4}


def try_list_monster(telegram_id: int, monster_id: int, price: int) -> tuple[bool, str]:
    """Выставить монстра на продажу."""
    if price < MIN_LISTING_PRICE:
        return False, f"Минимальная цена: {MIN_LISTING_PRICE} золота."
    if price > MAX_LISTING_PRICE:
        return False, f"Максимальная цена: {MAX_LISTING_PRICE} золота."

    m = get_monster_by_id(telegram_id, monster_id)
    if not m:
        return False, "Монстр не найден."
    if m.get("is_active"):
        return False, "Нельзя продать активного монстра. Смени активного."
    if m.get("is_listed"):
        return False, "Монстр уже выставлен на продажу."

    monsters = get_player_monsters(telegram_id)
    active_count = sum(1 for x in monsters if not x.get("is_listed"))
    if active_count <= 1:
        return False, "Нельзя продать последнего монстра."

    ok = list_monster_for_sale(telegram_id, monster_id, price)
    if ok:
        track(telegram_id, "p2p_listed", {"monster_id": monster_id, "price": price, "name": m["name"]})
    return ok, "" if ok else "Не удалось выставить монстра."


def try_delist_monster(telegram_id: int, monster_id: int) -> tuple[bool, str]:
    """Снять монстра с продажи."""
    m = get_monster_by_id(telegram_id, monster_id)
    if not m:
        return False, "Монстр не найден."
    if not m.get("is_listed"):
        return False, "Монстр не выставлен на продажу."
    ok = delist_monster(telegram_id, monster_id)
    return ok, "" if ok else "Ошибка снятия с продажи."


def try_buy_monster(buyer_id: int, monster_id: int) -> tuple[dict | None, str]:
    """Купить монстра у другого игрока."""
    # Проверяем что он выставлен
    listings = get_p2p_market_listings(limit=1000)
    listing  = next((l for l in listings if l["id"] == monster_id), None)
    if not listing:
        return None, "Лот не найден или уже продан."

    seller_id = listing.get("telegram_id")
    if seller_id == buyer_id:
        return None, "Нельзя купить своего же монстра."

    buyer = get_player(buyer_id)
    if not buyer:
        return None, "Игрок не найден."
    if buyer.gold < listing["list_price"]:
        return None, f"Недостаточно золота. Нужно: {listing['list_price']}, у тебя: {buyer.gold}."

    monster = _buy(buyer_id, monster_id)
    if not monster:
        return None, "Не удалось завершить сделку. Возможно, монстр уже продан."

    commission = int(listing["list_price"] * COMMISSION_RATE)
    seller_got = listing["list_price"] - commission

    track(buyer_id,   "p2p_bought",  {"monster_id": monster_id, "price": listing["list_price"], "name": listing["name"]})
    track(seller_id,  "p2p_sold",    {"monster_id": monster_id, "price": seller_got, "name": listing["name"]})

    return monster, f"seller_got:{seller_got}"


def render_p2p_market(listings: list[dict], page: int = 0, per_page: int = 8) -> str:
    if not listings:
        return "🏪 Рынок монстров\n\nПока нет предложений. Будь первым!"

    start = page * per_page
    page_items = listings[start:start + per_page]
    total_pages = (len(listings) - 1) // per_page + 1

    lines = [f"🏪 Рынок монстров (стр. {page+1}/{total_pages})\n"]
    for m in page_items:
        rarity_icons = {"common":"⚪","rare":"🔵","epic":"🟣","legendary":"🟡","mythic":"🔴"}
        icon  = rarity_icons.get(m.get("rarity","common"), "⚪")
        combo = f" ✨{m['combo_mutation']}" if m.get("combo_mutation") else ""
        infect = f" [{m['infection_type'][:3]}]" if m.get("infection_type") else ""
        lines.append(
            f"{icon} {m['name']}{combo}{infect}\n"
            f"   Ур.{m.get('level',1)} | HP:{m['max_hp']} ATK:{m['attack']} | "
            f"{m['list_price']}з | /buy_monster {m['id']}"
        )
    lines.append(f"\nКомиссия: {int(COMMISSION_RATE*100)}% (продавец получает {int((1-COMMISSION_RATE)*100)}%)")
    return "\n".join(lines)


def render_my_listings(telegram_id: int) -> str:
    monsters = get_player_monsters(telegram_id)
    listed   = [m for m in monsters if m.get("is_listed")]
    if not listed:
        return "У тебя нет монстров на продаже."
    lines = ["📋 Твои лоты:\n"]
    for m in listed:
        lines.append(f"• {m['name']} — {m['list_price']}з | /delist {m['id']}")
    return "\n".join(lines)
