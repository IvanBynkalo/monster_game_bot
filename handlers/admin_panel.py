"""
admin_panel.py — Полноценная админ-панель игры.
Заменяет старый handlers/admin.py (сохраняет его функции + добавляет новые).
"""
import time
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.repositories import (
    get_player, _update_player_field, reset_player_state,
    get_connection, update_player_location,
)
from game.analytics_service import (
    get_online_stats, get_level_distribution, get_inactive_players,
    get_top_players, get_new_players, render_analytics_text,
    log_admin_action, get_admin_log, touch_player_activity,
)
from game.notification_service import (
    create_notification, get_notifications, get_unread_count,
    create_announcement, send_announcement, get_announcements,
    get_segment_players, SEGMENT_LABELS, mark_all_read,
)

import os
ADMIN_IDS = set(
    int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()
)


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


# ── Клавиатуры ────────────────────────────────────────────────────────────────

def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Игроки", callback_data="adm:players"),
         InlineKeyboardButton(text="📊 Аналитика", callback_data="adm:analytics")],
        [InlineKeyboardButton(text="💤 Неактивные", callback_data="adm:inactive:7"),
         InlineKeyboardButton(text="🏆 Топы", callback_data="adm:tops")],
        [InlineKeyboardButton(text="📣 Рассылки", callback_data="adm:broadcasts"),
         InlineKeyboardButton(text="🔔 Уведомления", callback_data="adm:notif_menu")],
        [InlineKeyboardButton(text="📋 Лог действий", callback_data="adm:log"),
         InlineKeyboardButton(text="⚙️ Управление", callback_data="adm:manage")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="adm:close")],
    ])


def analytics_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💤 Неактивные 3д", callback_data="adm:inactive:3"),
         InlineKeyboardButton(text="💤 Неактивные 7д", callback_data="adm:inactive:7")],
        [InlineKeyboardButton(text="💤 Неактивные 14д", callback_data="adm:inactive:14"),
         InlineKeyboardButton(text="🆕 Новые игроки", callback_data="adm:new_players")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")],
    ])


def broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать рассылку", callback_data="adm:bc_create")],
        [InlineKeyboardButton(text="📋 Активные рассылки", callback_data="adm:bc_list")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")],
    ])


def segment_kb() -> InlineKeyboardMarkup:
    rows = []
    items = list(SEGMENT_LABELS.items())
    for i in range(0, len(items), 2):
        row = []
        for code, label in items[i:i+2]:
            row.append(InlineKeyboardButton(text=label, callback_data=f"adm:bc_seg:{code}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Отмена", callback_data="adm:broadcasts")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def manage_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Найти игрока", callback_data="adm:find_player"),
         InlineKeyboardButton(text="💰 Выдать золото", callback_data="adm:give_gold")],
        [InlineKeyboardButton(text="⚡ Выдать энергию", callback_data="adm:give_energy"),
         InlineKeyboardButton(text="🔄 Сбросить игрока", callback_data="adm:reset")],
        [InlineKeyboardButton(text="🚫 Бан/разбан", callback_data="adm:ban"),
         InlineKeyboardButton(text="📍 Телепорт", callback_data="adm:teleport")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")],
    ])


# ── Хендлеры ─────────────────────────────────────────────────────────────────

async def admin_cmd(message: Message):
    """Команда /admin — открывает панель."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return
    touch_player_activity(message.from_user.id, message.from_user.username)
    await message.answer("🛠 Админ-панель Monster Emotions", reply_markup=admin_main_kb())


# Состояния для диалогов (in-memory, simple)
_admin_states: dict[int, dict] = {}


async def admin_callback(callback: CallbackQuery):
    """Обрабатывает все adm: коллбэки."""
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer("⛔ Нет доступа.")
        return
    await callback.answer()
    data = callback.data

    # ── Навигация ──
    if data == "adm:main":
        await callback.message.edit_text(
            "🛠 Админ-панель Monster Emotions",
            reply_markup=admin_main_kb()
        )

    elif data == "adm:close":
        await callback.message.delete()

    # ── Аналитика ──
    elif data == "adm:analytics":
        text = render_analytics_text()
        await callback.message.edit_text(text, reply_markup=analytics_kb())

    elif data.startswith("adm:inactive:"):
        days = int(data.split(":")[-1])
        players = get_inactive_players(days=days, limit=15)
        if not players:
            text = f"💤 Нет игроков без активности {days}+ дней."
        else:
            import datetime
            lines = [f"💤 Неактивные {days}+ дней ({len(players)} чел.)\n"]
            for p in players:
                last = (datetime.datetime.fromtimestamp(p["last_active_at"]).strftime("%d.%m")
                        if p["last_active_at"] else "никогда")
                lines.append(
                    f"• {p['name']} (ур.{p['level']}) | "
                    f"ID:{p['telegram_id']} | последний: {last} ({p['days_absent']}д)"
                )
            text = "\n".join(lines)
        rows = [
            [InlineKeyboardButton(text="📣 Разослать им", callback_data=f"adm:bc_to_inactive:{days}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:analytics")],
        ]
        await callback.message.edit_text(
            text[:4000], reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
        )

    elif data == "adm:tops":
        tops = get_top_players(by="level", limit=10)
        lines = ["🏆 Топ-10 по уровню\n"]
        for i, p in enumerate(tops, 1):
            lines.append(f"{i}. {p['name']} — ур.{p['level']} | {p['gold']}з | ID:{p['telegram_id']}")
        tops_gold = get_top_players(by="gold", limit=5)
        lines.append("\n💰 Топ-5 по золоту")
        for i, p in enumerate(tops_gold, 1):
            lines.append(f"{i}. {p['name']} — {p['gold']}з")
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")]
            ])
        )

    elif data == "adm:new_players":
        players = get_new_players(limit=15)
        import datetime
        lines = [f"🆕 Новые игроки ({len(players)})\n"]
        for p in players:
            reg = datetime.datetime.fromtimestamp(p["created_at_ts"]).strftime("%d.%m %H:%M") if p["created_at_ts"] else "?"
            lines.append(f"• {p['name']} ур.{p['level']} | {reg} | ID:{p['telegram_id']}")
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:analytics")]
            ])
        )

    # ── Рассылки ──
    elif data == "adm:broadcasts":
        anns = get_announcements(limit=5)
        text = "📣 Рассылки\n\n"
        if anns:
            for a in anns:
                import datetime
                dt = datetime.datetime.fromtimestamp(a["created_at"]).strftime("%d.%m %H:%M")
                text += f"• [{dt}] {a['title']} → {a['segment_type']} ({a['sent_count']} отправлено)\n"
        else:
            text += "Рассылок пока нет."
        await callback.message.edit_text(text, reply_markup=broadcast_kb())

    elif data == "adm:bc_create":
        _admin_states[uid] = {"step": "bc_title"}
        await callback.message.edit_text(
            "📝 Создание рассылки\n\nШаг 1/3: Введи заголовок рассылки:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="adm:broadcasts")]
            ])
        )

    elif data == "adm:bc_seg:":
        pass  # handled below

    elif data.startswith("adm:bc_seg:"):
        segment = data.split(":", 2)[-1]
        state = _admin_states.get(uid, {})
        if state.get("step") == "bc_segment":
            title = state.get("title", "Объявление")
            text_body = state.get("text", "")
            players = get_segment_players(segment)
            ann = create_announcement(uid, title, text_body, segment)
            sent = send_announcement(ann["id"])
            log_admin_action(uid, "broadcast", detail=f"seg={segment} sent={sent}")
            await callback.message.edit_text(
                f"✅ Рассылка отправлена!\n"
                f"Заголовок: {title}\n"
                f"Сегмент: {SEGMENT_LABELS.get(segment, segment)}\n"
                f"Отправлено: {sent} игрокам",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ К рассылкам", callback_data="adm:broadcasts")]
                ])
            )
            _admin_states.pop(uid, None)

    elif data.startswith("adm:bc_to_inactive:"):
        days = data.split(":")[-1]
        seg = f"inactive_{days}d"
        _admin_states[uid] = {"step": "bc_title", "segment_override": seg}
        await callback.message.edit_text(
            f"📣 Рассылка неактивным {days}+ дней\n\nВведи заголовок:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="adm:broadcasts")]
            ])
        )

    # ── Уведомления ──
    elif data == "adm:notif_menu":
        await callback.message.edit_text(
            "🔔 Отправить уведомление игроку\n\nВведи: /notif ID Заголовок | Текст",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")]
            ])
        )

    # ── Управление игроками ──
    elif data == "adm:manage":
        await callback.message.edit_text("⚙️ Управление игроками", reply_markup=manage_kb())

    elif data == "adm:find_player":
        _admin_states[uid] = {"step": "find_player"}
        await callback.message.edit_text(
            "🔍 Введи ID или имя игрока командой:\n/admin_find <ID или имя>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:manage")]
            ])
        )

    elif data == "adm:give_gold":
        _admin_states[uid] = {"step": "give_gold"}
        await callback.message.edit_text(
            "💰 Выдача золота\n\nВведи: /admin_gold ID СУММА",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:manage")]
            ])
        )

    elif data == "adm:give_energy":
        _admin_states[uid] = {"step": "give_energy"}
        await callback.message.edit_text(
            "⚡ Выдача энергии\n\nВведи: /admin_energy ID КОЛИЧЕСТВО",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:manage")]
            ])
        )

    elif data == "adm:reset":
        _admin_states[uid] = {"step": "reset_player"}
        await callback.message.edit_text(
            "🔄 Сброс игрока\n\nВведи: /admin_reset ID",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:manage")]
            ])
        )

    elif data == "adm:ban":
        _admin_states[uid] = {"step": "ban_player"}
        await callback.message.edit_text(
            "🚫 Бан/разбан\n\nВведи: /admin_ban ID или /admin_unban ID",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:manage")]
            ])
        )

    elif data == "adm:teleport":
        _admin_states[uid] = {"step": "teleport"}
        await callback.message.edit_text(
            "📍 Телепорт\n\nВведи: /admin_tp ID ЛОКАЦИЯ",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:manage")]
            ])
        )

    # ── Лог ──
    elif data == "adm:log":
        logs = get_admin_log(limit=15)
        import datetime
        lines = ["📋 Последние действия админов\n"]
        for l in logs:
            dt = datetime.datetime.fromtimestamp(l["created_at"]).strftime("%d.%m %H:%M")
            lines.append(f"[{dt}] admin:{l['admin_id']} → {l['action']} {l.get('detail','')}")
        await callback.message.edit_text(
            "\n".join(lines)[:4000],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")]
            ])
        )


# ── Текстовые команды ─────────────────────────────────────────────────────────

async def admin_text_handler(message: Message):
    """Обрабатывает текстовые команды в диалогах и /admin_* команды."""
    uid = message.from_user.id
    if not is_admin(uid):
        return False  # не обрабатываем

    text = (message.text or "").strip()

    # /admin_gold ID AMOUNT
    if text.startswith("/admin_gold"):
        parts = text.split()
        if len(parts) < 3:
            await message.answer("Формат: /admin_gold ID СУММА")
            return True
        try:
            target_id = int(parts[1])
            amount = int(parts[2])
        except ValueError:
            await message.answer("Неверный формат.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        _update_player_field(target_id, gold=p.gold + amount)
        log_admin_action(uid, "give_gold", "player", target_id, f"+{amount}z")
        create_notification(target_id, "🎁 Подарок от администрации",
                            f"Тебе выдано {amount} золота.")
        await message.answer(f"✅ Выдано {amount}з игроку {p.name} (ID:{target_id})")
        return True

    # /admin_energy ID AMOUNT
    elif text.startswith("/admin_energy"):
        parts = text.split()
        if len(parts) < 3:
            await message.answer("Формат: /admin_energy ID КОЛИЧЕСТВО")
            return True
        try:
            target_id, amount = int(parts[1]), int(parts[2])
        except ValueError:
            await message.answer("Неверный формат.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        _update_player_field(target_id, energy=min(p.energy + amount, 20))
        log_admin_action(uid, "give_energy", "player", target_id, f"+{amount}")
        await message.answer(f"✅ Выдано {amount} энергии игроку {p.name}")
        return True

    # /admin_reset ID
    elif text.startswith("/admin_reset"):
        parts = text.split()
        if len(parts) < 2:
            await message.answer("Формат: /admin_reset ID")
            return True
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        reset_player_state(target_id, name=p.name)
        from game.player_service import ensure_starter_monster as _esm
        _esm(target_id)
        log_admin_action(uid, "reset_player", "player", target_id)
        await message.answer(f"✅ Игрок {p.name} (ID:{target_id}) сброшен.")
        return True

    # /admin_ban ID
    elif text.startswith("/admin_ban"):
        parts = text.split()
        if len(parts) < 2:
            await message.answer("Формат: /admin_ban ID")
            return True
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        with get_connection() as conn:
            conn.execute("UPDATE players SET is_banned=1 WHERE telegram_id=?", (target_id,))
            conn.commit()
        log_admin_action(uid, "ban", "player", target_id)
        await message.answer(f"🚫 Игрок {target_id} заблокирован.")
        return True

    # /admin_unban ID
    elif text.startswith("/admin_unban"):
        parts = text.split()
        if len(parts) < 2:
            await message.answer("Формат: /admin_unban ID")
            return True
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        with get_connection() as conn:
            conn.execute("UPDATE players SET is_banned=0 WHERE telegram_id=?", (target_id,))
            conn.commit()
        log_admin_action(uid, "unban", "player", target_id)
        await message.answer(f"✅ Игрок {target_id} разблокирован.")
        return True

    # /admin_find ID
    elif text.startswith("/admin_find"):
        parts = text.split()
        if len(parts) < 2:
            await message.answer("Формат: /admin_find ID")
            return True
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        import datetime
        last = "никогда"
        with get_connection() as conn:
            row = conn.execute("SELECT last_active_at, created_at_ts, is_banned FROM players WHERE telegram_id=?", (target_id,)).fetchone()
        if row and row["last_active_at"]:
            last = datetime.datetime.fromtimestamp(row["last_active_at"]).strftime("%d.%m.%Y %H:%M")
        created = datetime.datetime.fromtimestamp(row["created_at_ts"]).strftime("%d.%m.%Y") if row and row["created_at_ts"] else "?"
        banned = "🚫 ЗАБАНЕН" if row and row["is_banned"] else "✅ Активен"
        await message.answer(
            f"👤 {p.name} (ID:{target_id})\n"
            f"Уровень: {p.level} | Золото: {p.gold}\n"
            f"HP: {p.hp}/{p.max_hp} | Энергия: {p.energy}\n"
            f"Локация: {p.location_slug}\n"
            f"Последний вход: {last}\n"
            f"Зарегистрирован: {created}\n"
            f"Статус: {banned}"
        )
        return True

    # /admin_tp ID LOCATION
    elif text.startswith("/admin_tp"):
        parts = text.split()
        if len(parts) < 3:
            await message.answer("Формат: /admin_tp ID ЛОКАЦИЯ")
            return True
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        slug = parts[2]
        update_player_location(target_id, slug)
        log_admin_action(uid, "teleport", "player", target_id, f"to={slug}")
        await message.answer(f"✅ Игрок {target_id} телепортирован в {slug}.")
        return True

    # /notif ID Заголовок | Текст
    elif text.startswith("/notif"):
        parts = text[7:].strip().split("|", 1)
        first = parts[0].strip().split(" ", 1)
        if len(first) < 2:
            await message.answer("Формат: /notif ID Заголовок | Текст")
            return True
        try:
            target_id = int(first[0])
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        title = first[1].strip()
        body = parts[1].strip() if len(parts) > 1 else ""
        create_notification(target_id, title, body, notif_type="admin")
        log_admin_action(uid, "send_notification", "player", target_id, title)
        await message.answer(f"✅ Уведомление отправлено игроку {target_id}.")
        return True

    # Диалоговые состояния (ввод текста рассылки)
    state = _admin_states.get(uid, {})
    if state.get("step") == "bc_title":
        _admin_states[uid] = {"step": "bc_text", "title": text,
                              "segment_override": state.get("segment_override")}
        await message.answer(
            f"📝 Заголовок: {text}\n\nШаг 2/3: Введи текст рассылки:"
        )
        return True

    elif state.get("step") == "bc_text":
        title = state.get("title", "Объявление")
        seg_override = state.get("segment_override")
        if seg_override:
            # Сразу отправляем с заданным сегментом
            ann = create_announcement(uid, title, text, seg_override)
            sent = send_announcement(ann["id"])
            log_admin_action(uid, "broadcast", detail=f"seg={seg_override} sent={sent}")
            await message.answer(
                f"✅ Рассылка отправлена!\n"
                f"Сегмент: {SEGMENT_LABELS.get(seg_override, seg_override)}\n"
                f"Отправлено: {sent} игрокам"
            )
            _admin_states.pop(uid, None)
        else:
            _admin_states[uid] = {"step": "bc_segment", "title": title, "text": text}
            await message.answer(
                f"📝 Текст получен.\n\nШаг 3/3: Выбери сегмент получателей:",
                reply_markup=segment_kb()
            )
        return True

    return False


# ── Уведомления для игрока ────────────────────────────────────────────────────

async def player_notifications_handler(message: Message):
    """Показывает уведомления игрока."""
    uid = message.from_user.id
    notifs = get_notifications(uid)
    if not notifs:
        await message.answer("🔔 Нет новых уведомлений.")
        return

    import datetime
    lines = [f"🔔 Уведомления ({len(notifs)})\n"]
    rows = []
    for n in notifs[:10]:
        read_icon = "🔵" if not n["is_read"] else "⚪"
        dt = datetime.datetime.fromtimestamp(n["created_at"]).strftime("%d.%m %H:%M")
        lines.append(f"{read_icon} [{dt}] {n['title']}\n  {n['text'][:100]}")
        if not n["is_read"]:
            rows.append([InlineKeyboardButton(
                text=f"✓ Прочитать: {n['title'][:30]}",
                callback_data=f"notif:read:{n['id']}"
            )])

    rows.append([InlineKeyboardButton(text="✅ Прочитать все", callback_data="notif:read_all")])
    await message.answer(
        "\n\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


async def notification_callback(callback: CallbackQuery):
    """Обрабатывает notif: коллбэки."""
    uid = callback.from_user.id
    data = callback.data
    await callback.answer()

    if data.startswith("notif:read:"):
        nid = int(data.split(":")[-1])
        from game.notification_service import mark_read
        mark_read(nid, uid)
        await callback.answer("✓ Прочитано", show_alert=False)

    elif data == "notif:read_all":
        mark_all_read(uid)
        await callback.message.edit_text("✅ Все уведомления прочитаны.")
