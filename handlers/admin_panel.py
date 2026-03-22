"""
admin_panel.py — Полноценная inline-панель администратора.
Все действия через кнопки. Ввод данных через ForceReply.
"""
import time
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ForceReply
from database.repositories import (
    get_player, _update_player_field, reset_player_state,
    get_connection, update_player_location,
)
from game.analytics_service import (
    get_online_stats, get_level_distribution, get_inactive_players,
    get_top_players, get_new_players, render_analytics_text,
    log_admin_action, get_admin_log,
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


# ── Состояния диалогов ────────────────────────────────────────────────────────
# {uid: {"step": "...", "data": {...}}}
_admin_states: dict[int, dict] = {}


# ── Клавиатуры ────────────────────────────────────────────────────────────────

def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Игроки",       callback_data="adm:players"),
         InlineKeyboardButton(text="📊 Аналитика",   callback_data="adm:analytics")],
        [InlineKeyboardButton(text="💤 Неактивные",   callback_data="adm:inactive:7"),
         InlineKeyboardButton(text="🏆 Топы",         callback_data="adm:tops")],
        [InlineKeyboardButton(text="📣 Рассылки",     callback_data="adm:broadcasts"),
         InlineKeyboardButton(text="🔔 Уведомление",  callback_data="adm:notif_menu")],
        [InlineKeyboardButton(text="📋 Лог действий", callback_data="adm:log"),
         InlineKeyboardButton(text="⚙️ Управление",  callback_data="adm:manage")],
        [InlineKeyboardButton(text="❌ Закрыть",      callback_data="adm:close")],
    ])


def manage_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Найти игрока",   callback_data="adm:find_player"),
         InlineKeyboardButton(text="💰 Выдать золото",  callback_data="adm:give_gold")],
        [InlineKeyboardButton(text="⚡ Выдать энергию", callback_data="adm:give_energy"),
         InlineKeyboardButton(text="❤️ Вылечить",       callback_data="adm:heal_player")],
        [InlineKeyboardButton(text="🔄 Сбросить",       callback_data="adm:reset_player"),
         InlineKeyboardButton(text="🚫 Бан",            callback_data="adm:ban_player")],
        [InlineKeyboardButton(text="✅ Разбан",          callback_data="adm:unban_player"),
         InlineKeyboardButton(text="📍 Телепорт",       callback_data="adm:teleport")],
        [InlineKeyboardButton(text="⬅️ Назад",          callback_data="adm:main")],
    ])


def analytics_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💤 3 дня",  callback_data="adm:inactive:3"),
         InlineKeyboardButton(text="💤 7 дней", callback_data="adm:inactive:7"),
         InlineKeyboardButton(text="💤 14 дней",callback_data="adm:inactive:14")],
        [InlineKeyboardButton(text="🆕 Новые игроки", callback_data="adm:new_players")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")],
    ])


def broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать рассылку", callback_data="adm:bc_create")],
        [InlineKeyboardButton(text="📋 История",          callback_data="adm:bc_list")],
        [InlineKeyboardButton(text="⬅️ Назад",            callback_data="adm:main")],
    ])


def segment_kb() -> InlineKeyboardMarkup:
    rows = []
    items = list(SEGMENT_LABELS.items())
    for i in range(0, len(items), 2):
        row = []
        for code, label in items[i:i+2]:
            row.append(InlineKeyboardButton(text=label, callback_data=f"adm:bc_seg:{code}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="adm:broadcasts")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _back_to_manage() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:manage")]
    ])


# ── Команда /admin ────────────────────────────────────────────────────────────

async def admin_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return
    await message.answer("🛠 Админ-панель Monster Emotions", reply_markup=admin_main_kb())


# ── Главный callback ──────────────────────────────────────────────────────────

async def admin_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer("⛔ Нет доступа.")
        return
    await callback.answer()
    data = callback.data

    # ── Навигация ──
    if data == "adm:main":
        await _edit(callback, "🛠 Админ-панель", admin_main_kb())

    elif data == "adm:close":
        try:
            await callback.message.delete()
        except Exception:
            pass

    # ── Аналитика ──
    elif data == "adm:analytics":
        await _edit(callback, render_analytics_text(), analytics_kb())

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
                    f"ID:{p['telegram_id']} | {last} ({p['days_absent']}д)"
                )
            text = "\n".join(lines)
        rows = [
            [InlineKeyboardButton(text="📣 Разослать им", callback_data=f"adm:bc_to_inactive:{days}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:analytics")],
        ]
        await _edit(callback, text[:4000], InlineKeyboardMarkup(inline_keyboard=rows))

    elif data == "adm:tops":
        tops = get_top_players(by="level", limit=10)
        lines = ["🏆 Топ-10 по уровню\n"]
        for i, p in enumerate(tops, 1):
            lines.append(f"{i}. {p['name']} — ур.{p['level']} | {p['gold']}з | ID:{p['telegram_id']}")
        tops_gold = get_top_players(by="gold", limit=5)
        lines.append("\n💰 Топ-5 по золоту")
        for i, p in enumerate(tops_gold, 1):
            lines.append(f"{i}. {p['name']} — {p['gold']}з")
        await _edit(callback, "\n".join(lines),
                    InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")]]))

    elif data == "adm:new_players":
        players = get_new_players(limit=15)
        import datetime
        lines = [f"🆕 Новые игроки ({len(players)})\n"]
        for p in players:
            reg = datetime.datetime.fromtimestamp(p["created_at_ts"]).strftime("%d.%m %H:%M") if p.get("created_at_ts") else "?"
            lines.append(f"• {p['name']} ур.{p['level']} | {reg} | ID:{p['telegram_id']}")
        await _edit(callback, "\n".join(lines),
                    InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:analytics")]]))

    # ── Управление игроками ──
    elif data == "adm:manage":
        await _edit(callback, "⚙️ Управление игроками", manage_kb())

    # Каждое действие — запрашивает ID через ForceReply
    elif data in ("adm:find_player", "adm:give_gold", "adm:give_energy",
                  "adm:heal_player", "adm:reset_player", "adm:ban_player",
                  "adm:unban_player", "adm:teleport", "adm:notif_menu"):
        _admin_states[uid] = {"step": data}
        prompts = {
            "adm:find_player":    "🔍 Введи ID игрока:",
            "adm:give_gold":      "💰 Введи: ID СУММА\n(например: 123456 500)",
            "adm:give_energy":    "⚡ Введи: ID КОЛИЧЕСТВО\n(например: 123456 5)",
            "adm:heal_player":    "❤️ Введи ID игрока для лечения монстра:",
            "adm:reset_player":   "🔄 Введи ID игрока для ПОЛНОГО сброса:",
            "adm:ban_player":     "🚫 Введи ID игрока для бана:",
            "adm:unban_player":   "✅ Введи ID игрока для разбана:",
            "adm:teleport":       "📍 Введи: ID ЛОКАЦИЯ\n(например: 123456 dark_forest)",
            "adm:notif_menu":     "🔔 Введи: ID Заголовок | Текст сообщения",
        }
        await callback.message.answer(
            prompts[data],
            reply_markup=ForceReply(selective=True, input_field_placeholder="Введи ответ...")
        )

    # ── Рассылки ──
    elif data == "adm:broadcasts":
        anns = get_announcements(limit=5)
        text = "📣 Рассылки\n\n"
        if anns:
            import datetime
            for a in anns:
                dt = datetime.datetime.fromtimestamp(a["created_at"]).strftime("%d.%m %H:%M")
                text += f"• [{dt}] {a['title']} → {a['segment_type']} ({a['sent_count']} отправлено)\n"
        else:
            text += "Рассылок пока нет."
        await _edit(callback, text, broadcast_kb())

    elif data == "adm:bc_create":
        _admin_states[uid] = {"step": "bc_title"}
        await callback.message.answer(
            "📝 Создание рассылки\nВведи заголовок:",
            reply_markup=ForceReply(selective=True, input_field_placeholder="Заголовок рассылки...")
        )

    elif data.startswith("adm:bc_seg:"):
        segment = data.split(":", 2)[-1]
        state = _admin_states.get(uid, {})
        title = state.get("title", "Объявление")
        text_body = state.get("text", "")
        ann = create_announcement(uid, title, text_body, segment)
        sent = send_announcement(ann["id"])
        log_admin_action(uid, "broadcast", detail=f"seg={segment} sent={sent}")
        await callback.message.answer(
            f"✅ Рассылка отправлена!\n"
            f"Сегмент: {SEGMENT_LABELS.get(segment, segment)}\n"
            f"Отправлено: {sent} игрокам"
        )
        _admin_states.pop(uid, None)

    elif data.startswith("adm:bc_to_inactive:"):
        days = data.split(":")[-1]
        _admin_states[uid] = {"step": "bc_title", "segment_override": f"inactive_{days}d"}
        await callback.message.answer(
            f"📣 Рассылка неактивным {days}+ дней\nВведи заголовок:",
            reply_markup=ForceReply(selective=True, input_field_placeholder="Заголовок...")
        )

    elif data == "adm:bc_list":
        anns = get_announcements(limit=10)
        import datetime
        lines = ["📋 История рассылок\n"]
        for a in anns:
            dt = datetime.datetime.fromtimestamp(a["created_at"]).strftime("%d.%m %H:%M")
            lines.append(f"[{dt}] {a['title']} ({a['sent_count']} получили)")
        await _edit(callback, "\n".join(lines) if anns else "Рассылок нет.",
                    InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:broadcasts")]]))

    # ── Лог ──
    elif data == "adm:log":
        logs = get_admin_log(limit=15)
        import datetime
        lines = ["📋 Действия админов\n"]
        for l in logs:
            dt = datetime.datetime.fromtimestamp(l["created_at"]).strftime("%d.%m %H:%M")
            lines.append(f"[{dt}] admin:{l['admin_id']} → {l['action']} {l.get('detail','')}")
        await _edit(callback, "\n".join(lines)[:4000],
                    InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:main")]]))

    # ── Подтверждение опасных действий ──
    elif data.startswith("adm:confirm_reset:"):
        target_id = int(data.split(":")[-1])
        p = get_player(target_id)
        if p:
            reset_player_state(target_id, name=p.name)
            from game.player_service import ensure_starter_monster as _esm
            _esm(target_id)
            log_admin_action(uid, "reset_player", "player", target_id)
            await callback.message.answer(f"✅ Игрок {p.name} (ID:{target_id}) сброшен.")
        await _edit(callback, "⚙️ Управление", manage_kb())

    elif data.startswith("adm:confirm_ban:"):
        target_id = int(data.split(":")[-1])
        with get_connection() as conn:
            conn.execute("UPDATE players SET is_banned=1 WHERE telegram_id=?", (target_id,))
            conn.commit()
        log_admin_action(uid, "ban", "player", target_id)
        await callback.message.answer(f"🚫 Игрок {target_id} заблокирован.")
        await _edit(callback, "⚙️ Управление", manage_kb())

    elif data.startswith("adm:cancel_action"):
        await _edit(callback, "⚙️ Управление", manage_kb())


# ── Обработчик ForceReply ответов ─────────────────────────────────────────────

async def admin_reply_handler(message: Message) -> bool:
    """Обрабатывает ответы на ForceReply от админа."""
    uid = message.from_user.id
    if not is_admin(uid):
        return False

    state = _admin_states.get(uid)
    if not state:
        return False

    step = state.get("step", "")
    text = (message.text or "").strip()

    # ── Найти игрока ──
    if step == "adm:find_player":
        _admin_states.pop(uid, None)
        try:
            target_id = int(text)
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        import datetime
        with get_connection() as conn:
            row = conn.execute("SELECT last_active_at, created_at_ts, is_banned FROM players WHERE telegram_id=?", (target_id,)).fetchone()
        last = datetime.datetime.fromtimestamp(row["last_active_at"]).strftime("%d.%m.%Y %H:%M") if row and row["last_active_at"] else "никогда"
        created = datetime.datetime.fromtimestamp(row["created_at_ts"]).strftime("%d.%m.%Y") if row and row["created_at_ts"] else "?"
        banned = "🚫 ЗАБАНЕН" if row and row["is_banned"] else "✅ Активен"
        # Кнопки действий для этого игрока
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Выдать 100з",  callback_data=f"adm:quick_gold:{target_id}:100"),
             InlineKeyboardButton(text="💰 Выдать 500з",  callback_data=f"adm:quick_gold:{target_id}:500")],
            [InlineKeyboardButton(text="⚡ Полная энергия", callback_data=f"adm:quick_energy:{target_id}"),
             InlineKeyboardButton(text="❤️ Вылечить",     callback_data=f"adm:quick_heal:{target_id}")],
            [InlineKeyboardButton(text="🔄 Сбросить",     callback_data=f"adm:confirm_reset:{target_id}"),
             InlineKeyboardButton(text="🚫 Бан",           callback_data=f"adm:confirm_ban:{target_id}")],
            [InlineKeyboardButton(text="⬅️ Назад",        callback_data="adm:manage")],
        ])
        await message.answer(
            f"👤 {p.name} (ID:{target_id})\n"
            f"Уровень: {p.level} | Золото: {p.gold}\n"
            f"HP: {p.hp}/{p.max_hp} | Энергия: {p.energy}\n"
            f"Локация: {p.location_slug}\n"
            f"Последний вход: {last}\n"
            f"Зарегистрирован: {created}\n"
            f"Статус: {banned}",
            reply_markup=kb
        )
        return True

    # ── Выдать золото ──
    elif step == "adm:give_gold":
        _admin_states.pop(uid, None)
        parts = text.split()
        if len(parts) < 2:
            await message.answer("Формат: ID СУММА")
            return True
        try:
            target_id, amount = int(parts[0]), int(parts[1])
        except ValueError:
            await message.answer("Неверный формат.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        _update_player_field(target_id, gold=p.gold + amount)
        create_notification(target_id, "🎁 Подарок", f"Тебе выдано {amount} золота от администрации.")
        log_admin_action(uid, "give_gold", "player", target_id, f"+{amount}z")
        await message.answer(f"✅ {p.name} получил {amount}з (итого {p.gold+amount}з)")
        return True

    # ── Выдать энергию ──
    elif step == "adm:give_energy":
        _admin_states.pop(uid, None)
        parts = text.split()
        if len(parts) < 2:
            await message.answer("Формат: ID КОЛИЧЕСТВО")
            return True
        try:
            target_id, amount = int(parts[0]), int(parts[1])
        except ValueError:
            await message.answer("Неверный формат.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        _update_player_field(target_id, energy=min(p.energy + amount, 20))
        log_admin_action(uid, "give_energy", "player", target_id, f"+{amount}")
        await message.answer(f"✅ {p.name} получил {amount} энергии")
        return True

    # ── Вылечить монстра ──
    elif step == "adm:heal_player":
        _admin_states.pop(uid, None)
        try:
            target_id = int(text)
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        from database.repositories import heal_active_monster
        heal_active_monster(target_id)
        await message.answer(f"✅ Монстр игрока {target_id} вылечен.")
        return True

    # ── Сброс игрока ──
    elif step == "adm:reset_player":
        _admin_states.pop(uid, None)
        try:
            target_id = int(text)
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        # Подтверждение
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"⚠️ Да, сбросить {p.name}", callback_data=f"adm:confirm_reset:{target_id}"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel_action")],
        ])
        await message.answer(f"Сбросить игрока {p.name} (ур.{p.level})? Все данные будут удалены!", reply_markup=kb)
        return True

    # ── Бан ──
    elif step == "adm:ban_player":
        _admin_states.pop(uid, None)
        try:
            target_id = int(text)
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        p = get_player(target_id)
        if not p:
            await message.answer(f"Игрок {target_id} не найден.")
            return True
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🚫 Да, заблокировать {p.name}", callback_data=f"adm:confirm_ban:{target_id}"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel_action")],
        ])
        await message.answer(f"Заблокировать {p.name}?", reply_markup=kb)
        return True

    # ── Разбан ──
    elif step == "adm:unban_player":
        _admin_states.pop(uid, None)
        try:
            target_id = int(text)
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        with get_connection() as conn:
            conn.execute("UPDATE players SET is_banned=0 WHERE telegram_id=?", (target_id,))
            conn.commit()
        log_admin_action(uid, "unban", "player", target_id)
        await message.answer(f"✅ Игрок {target_id} разблокирован.")
        return True

    # ── Телепорт ──
    elif step == "adm:teleport":
        _admin_states.pop(uid, None)
        parts = text.split()
        if len(parts) < 2:
            await message.answer("Формат: ID ЛОКАЦИЯ")
            return True
        try:
            target_id = int(parts[0])
        except ValueError:
            await message.answer("Неверный ID.")
            return True
        slug = parts[1]
        update_player_location(target_id, slug)
        log_admin_action(uid, "teleport", "player", target_id, f"to={slug}")
        await message.answer(f"✅ Игрок {target_id} телепортирован в {slug}.")
        return True

    # ── Уведомление игроку ──
    elif step == "adm:notif_menu":
        _admin_states.pop(uid, None)
        parts = text.split("|", 1)
        first = parts[0].strip().split(" ", 1)
        if len(first) < 2:
            await message.answer("Формат: ID Заголовок | Текст")
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

    # ── Рассылка: заголовок ──
    elif step == "bc_title":
        seg_override = state.get("segment_override")
        _admin_states[uid] = {"step": "bc_text", "title": text, "segment_override": seg_override}
        await message.answer(
            f"📝 Заголовок: {text}\n\nТеперь введи текст рассылки:",
            reply_markup=ForceReply(selective=True, input_field_placeholder="Текст рассылки...")
        )
        return True

    # ── Рассылка: текст ──
    elif step == "bc_text":
        title = state.get("title", "Объявление")
        seg_override = state.get("segment_override")
        if seg_override:
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
            await message.answer("Выбери сегмент получателей:", reply_markup=segment_kb())
        return True

    return False


# ── Быстрые действия из карточки игрока ──────────────────────────────────────

async def admin_quick_callback(callback: CallbackQuery):
    """Быстрые действия: выдать золото, энергию, вылечить прямо из карточки игрока."""
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer("⛔ Нет доступа.")
        return
    data = callback.data
    await callback.answer()

    if data.startswith("adm:quick_gold:"):
        parts = data.split(":")
        target_id, amount = int(parts[2]), int(parts[3])
        p = get_player(target_id)
        if p:
            _update_player_field(target_id, gold=p.gold + amount)
            create_notification(target_id, "🎁 Подарок", f"Тебе выдано {amount} золота.")
            log_admin_action(uid, "quick_gold", "player", target_id, f"+{amount}z")
            await callback.message.answer(f"✅ {p.name} получил {amount}з")

    elif data.startswith("adm:quick_energy:"):
        target_id = int(data.split(":")[-1])
        p = get_player(target_id)
        if p:
            _update_player_field(target_id, energy=12)
            log_admin_action(uid, "quick_energy", "player", target_id)
            await callback.message.answer(f"✅ Энергия {p.name} восстановлена")

    elif data.startswith("adm:quick_heal:"):
        target_id = int(data.split(":")[-1])
        from database.repositories import heal_active_monster
        heal_active_monster(target_id)
        log_admin_action(uid, "quick_heal", "player", target_id)
        await callback.message.answer(f"✅ Монстр игрока {target_id} вылечен")


# ── Хендлер уведомлений игрока ────────────────────────────────────────────────

async def player_notifications_handler(message: Message):
    uid = message.from_user.id
    notifs = get_notifications(uid)
    if not notifs:
        await message.answer("🔔 Нет уведомлений.")
        return
    import datetime
    lines = [f"🔔 Уведомления ({len(notifs)})\n"]
    rows = []
    for n in notifs[:10]:
        icon = "🔵" if not n["is_read"] else "⚪"
        dt = datetime.datetime.fromtimestamp(n["created_at"]).strftime("%d.%m %H:%M")
        lines.append(f"{icon} [{dt}] {n['title']}\n  {n['text'][:100]}")
    rows.append([InlineKeyboardButton(text="✅ Прочитать все", callback_data="notif:read_all")])
    await message.answer("\n\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


async def notification_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    data = callback.data
    await callback.answer()
    if data == "notif:read_all":
        mark_all_read(uid)
        try:
            await callback.message.edit_text("✅ Все уведомления прочитаны.")
        except Exception:
            pass


# ── Вспомогательные ───────────────────────────────────────────────────────────

async def _edit(callback: CallbackQuery, text: str, kb: InlineKeyboardMarkup):
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
