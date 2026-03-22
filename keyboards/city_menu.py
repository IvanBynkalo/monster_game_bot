from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def city_menu(district_slug: str | None = None, telegram_id: int = None):
    keyboard = [
        [KeyboardButton(text="🏬 Торговый квартал"), KeyboardButton(text="📜 Доска заказов")],
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
                    return f"{base} (✅ 1)"
                elif st == "active":
                    return f"{base} (❗ 1)"
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
        keyboard = [
            [KeyboardButton(text="⚗ Алхимическая лаборатория"), KeyboardButton(text="🪤 Мастер ловушек")],
            [KeyboardButton(text="🔨 Мастерская"), KeyboardButton(text="🏛 Аукцион")],
            [KeyboardButton(text="📋 Заказы")],
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
            """Quest indicator на кнопке гильдии."""
            status = _q_done.get(guild_key)
            if status == "ready":
                return f"✅ {base_text}"
            elif status == "active":
                return f"❗ {base_text}"
            # Проверяем есть ли доступные для взятия квесты
            if telegram_id:
                try:
                    from game.guild_quests import get_available_quests
                    available = get_available_quests(telegram_id, guild_key)
                    if available:
                        return f"📌 {base_text}"
                except Exception:
                    pass
            return base_text

        keyboard = [
            [KeyboardButton(text=_qi("🎯 Гильдия ловцов", "hunter")),
             KeyboardButton(text=_qi("🌿 Гильдия собирателей", "gatherer"))],
            [KeyboardButton(text=_qi("⛏ Гильдия геологов", "geologist")),
             KeyboardButton(text=_qi("⚗ Гильдия алхимиков", "alchemist"))],
            [KeyboardButton(text="🌌 Алтарь рождения")],
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
