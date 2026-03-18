from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from game.market_service import (
    BAG_OFFERS,
    make_buy_button_text,
    make_sell_button_text,
)


def shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧪 Магазин предметов"), KeyboardButton(text="🐲 Магазин монстров")],
            [KeyboardButton(text="🎒 Сумки"), KeyboardButton(text="💰 Продать ресурсы")],
            [KeyboardButton(text="🛒 Купить ресурсы")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


def item_shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить: Малое зелье"), KeyboardButton(text="🛒 Купить: Капсула энергии")],
            [KeyboardButton(text="🛒 Купить: Простая ловушка")],
            [KeyboardButton(text="⬅️ Назад в магазин")],
        ],
        resize_keyboard=True,
    )


def monster_shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить монстра: Лесной спрайт")],
            [KeyboardButton(text="🛒 Купить монстра: Болотный охотник")],
            [KeyboardButton(text="🛒 Купить монстра: Угольный клык")],
            [KeyboardButton(text="⬅️ Назад в магазин")],
        ],
        resize_keyboard=True,
    )


def bag_shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"🛒 Купить сумку: {BAG_OFFERS['waist_bag']['name']} • {BAG_OFFERS['waist_bag']['price']}з")],
            [KeyboardButton(text=f"🛒 Купить сумку: {BAG_OFFERS['field_pack']['name']} • {BAG_OFFERS['field_pack']['price']}з")],
            [KeyboardButton(text=f"🛒 Купить сумку: {BAG_OFFERS['expedition_backpack']['name']} • {BAG_OFFERS['expedition_backpack']['price']}з")],
            [KeyboardButton(text="⬅️ Назад в магазин")],
        ],
        resize_keyboard=True,
    )


def sell_menu(city_slug: str, resources: dict, merchant_level: int):
    keyboard = []

    for slug, qty in resources.items():
        if qty > 0:
            keyboard.append(
                [
                    KeyboardButton(
                        text=make_sell_button_text(
                            slug=slug,
                            city_slug=city_slug,
                            merchant_level=merchant_level,
                            player_qty=qty,
                        )
                    )
                ]
            )

    keyboard.append([KeyboardButton(text="⬅️ Назад в магазин")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def buy_resources_menu(city_slug: str, market: dict):
    keyboard = []

    for slug, entry in market.items():
        stock = int(entry.get("stock", 0))
        if stock <= 0:
            continue

        keyboard.append(
            [
                KeyboardButton(
                    text=make_buy_button_text(
                        slug=slug,
                        city_slug=city_slug,
                        stock=stock,
                    )
                )
            ]
        )

    keyboard.append([KeyboardButton(text="⬅️ Назад в магазин")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
