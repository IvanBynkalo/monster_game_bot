from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def city_menu(district_slug: str | None = None, telegram_id: int = None):
    keyboard = [
        [KeyboardButton(text="🏬 Торговый квартал"), KeyboardButton(text=_npc_qi("📜 Доска заказов", "board"))],
        [KeyboardButton(text="🏛 Гильдии"),           KeyboardButton(text="⚒ Ремесленный квартал")],
        [KeyboardButton(text="🐲 Мои монстры"),        KeyboardButton(text="💎 Кристаллы")],
        [KeyboardButton(text="🎒 Инвентарь"),          KeyboardButton(text="👤 Персонаж")],
        [KeyboardButton(text="📅 Сегодня"),             KeyboardButton(text="🔔 Уведомления")],
        [KeyboardButton(text="⚔️ Экипировка"),         KeyboardButton(text="📂 Ещё")],
        [KeyboardButton(text="🧭 Перемещение"),        KeyboardButton(text="🚶 Покинуть город")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def district_actions_menu(district_slug: str, telegram_id: int = None):
    keyboard = [
        [KeyboardButton(text="⬅️ Назад")],
    ]

    if district_slug == "market_square":
        # Quest indicators для торговцев
        def _npc_qi(base: str, npc_key: str) -> str:
            if not telegram_id:
                return base
            try:
                from database.repositories import get_npc_quest_status
                st = get_npc_quest_status(telegram_id, npc_key)
                if st == "ready":
                    return f"{base} (✅)"
                elif st == "active":
                    return f"{base} (❗)"
                elif st == "available":
                    return f"{base} (📌)"
            except Exception:
                pass
            return base

        keyboard = [
            [KeyboardButton(text=_npc_qi("🎒 Лавка сумок", "mirna")),
             KeyboardButton(text=_npc_qi("🐲 Рынок монстров", "varg"))],
            [KeyboardButton(text="🧪 Лавка зелий"),
             KeyboardButton(text=_npc_qi("💰 Скупщик ресурсов", "bort"))],
            [KeyboardButton(text="💎 Кристаллы"), KeyboardButton(text="⚔️ Экипировка")],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "craft_quarter":
        def _craft_qi(base: str, npc_key: str) -> str:
            """Индикатор для Геммы — редкие заказы."""
            if not telegram_id:
                return base
            try:
                from game.rare_orders import get_active_orders, check_order_fulfillment
                orders = get_active_orders(telegram_id)
                npc_name_map = {"gemma": "Гемма"}
                npc_name = npc_name_map.get(npc_key, "")
                npc_orders = [o for o in orders if o.get("npc") == npc_name]
                if any(check_order_fulfillment(telegram_id, o) for o in npc_orders):
                    return f"{base} (✅)"
                if npc_orders:
                    return f"{base} (📌)"
            except Exception:
                pass
            return base

        def _orders_qi(base: str) -> str:
            """Индикатор для кнопки Заказы — сколько можно сдать."""
            if not telegram_id:
                return base
            try:
                from game.rare_orders import get_active_orders, check_order_fulfillment
                orders = get_active_orders(telegram_id)
                ready = sum(1 for o in orders if check_order_fulfillment(telegram_id, o))
                available = len(orders)
                if ready > 0:
                    return f"{base} ({ready} ✅)"
                if available > 0:
                    return f"{base} ({available} 📌)"
            except Exception:
                pass
            return base

        keyboard = [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")],
            [KeyboardButton(text=_craft_qi("🔨 Мастерская", "gemma")),
             KeyboardButton(text="🏛 Аукцион")],
            [KeyboardButton(text=_orders_qi("📋 Заказы"))],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "guild_quarter":
        # Проверяем выполненные квесты для индикаторов
        _q_done = {}
        if telegram_id:
            try:
                from database.repositories import get_guild_quests_status
                _q_done = get_guild_quests_status(telegram_id)
            except Exception:
                pass

        def _qi(base_text: str, guild_key: str) -> str:
            """Quest indicator на кнопке гильдии — знак в конце в скобках."""
            status = _q_done.get(guild_key)
            if status == "ready":
                return f"{base_text} (✅)"
            elif status == "active":
                return f"{base_text} (❗)"
            # Проверяем доступные квесты через общую функцию
            if telegram_id:
                try:
                    from database.repositories import get_npc_quest_status
                    st2 = get_npc_quest_status(telegram_id, guild_key)
                    if st2 == "available":
                        return f"{base_text} (📌)"
                except Exception:
                    pass
            return base_text


        def _altar_label(tid: int) -> str:
            if not tid:
                return "🌌 Алтарь рождения"
            try:
                from database.repositories import get_player
                from game.emotion_birth_service import can_birth
                if can_birth and can_birth(tid):
                    return "✨ Алтарь рождения"
            except Exception:
                pass
            return "🌌 Алтарь рождения"

        keyboard = [
            [KeyboardButton(text=_qi("🎯 Гильдия ловцов", "hunter")),
             KeyboardButton(text=_qi("🌿 Гильдия собирателей", "gatherer"))],
            [KeyboardButton(text=_qi("⛏ Гильдия геологов", "geologist")),
             KeyboardButton(text=_qi("⚗ Гильдия алхимиков", "alchemist"))],
            [KeyboardButton(text=_altar_label(telegram_id))],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    elif district_slug == "main_gate":
        keyboard = [
            [KeyboardButton(text="🛡 Городская стража"), KeyboardButton(text="🚶 Покинуть город")],
            [KeyboardButton(text="⬅️ Назад")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
