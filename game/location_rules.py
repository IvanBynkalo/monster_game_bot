CITY_SLUG = "silver_city"

SHOP_LOCATIONS = {
    "silver_city": {
        "has_shop": True,
        "shop_name": "🏪 Торговые ряды Сереброграда",
    },
}

def has_shop(location_slug: str) -> bool:
    return SHOP_LOCATIONS.get(location_slug, {}).get("has_shop", False)

def get_shop_name(location_slug: str) -> str:
    return SHOP_LOCATIONS.get(location_slug, {}).get("shop_name", "Лавка")

def is_city(location_slug: str) -> bool:
    return location_slug == CITY_SLUG
