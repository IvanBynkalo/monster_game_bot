# Monster Emotions Bot — v3.0

Telegram RPG-бот с монстрами, которые мутируют под влиянием эмоций.

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Задать переменные окружения
export BOT_TOKEN="your_bot_token_here"
export ADMIN_IDS="123456789"   # Telegram ID администраторов через запятую

# 3. Запустить
python bot.py
```

База данных создаётся автоматически в `data/game.db` при первом запуске.

## Новые команды в v3.0

| Команда | Описание |
|---------|----------|
| `/daily` | Ежедневные задания и streak |
| `/top` | Таблица лидеров по уровню |
| `/pvp` | Твоя PvP-статистика |
| `/challenge <id>` | Вызвать игрока на бой |
| `/pvp_top` | PvP-рейтинг |
| `/guild` | Твоя гильдия / список гильдий |
| `/create_guild <имя>` | Создать гильдию (200з, ур.5+) |
| `/join_guild <id>` | Вступить в гильдию |
| `/leave_guild` | Покинуть гильдию |
| `/guild_raid <boss>` | Совместный рейд гильдии |
| `/market` | P2P-рынок монстров |
| `/sell_monster <id> <цена>` | Выставить монстра на продажу |
| `/buy_monster <id>` | Купить монстра у игрока |
| `/delist <id>` | Снять монстра с продажи |
| `/my_listings` | Мои лоты на рынке |
| `/stars_shop` | Магазин Telegram Stars |
| `/buy_stars <slug>` | Купить товар за Stars |
| `/season` | Сезонный пасс |
| `/buy_season_pass` | Купить сезонный пасс (300 Stars) |
| `/analytics` | Статистика (только админ) |

## Структура проекта

```
monster_game_bot/
├── bot.py                    # Точка входа, регистрация хендлеров
├── config.py                 # BOT_TOKEN, ADMIN_IDS
├── requirements.txt
├── data/                     # SQLite база данных (создаётся автоматически)
│   └── game.db
├── database/
│   ├── db.py                 # Подключение SQLite
│   ├── init_db.py            # Создание таблиц
│   ├── models.py             # Dataclass Player, Location
│   └── repositories.py      # Весь доступ к данным (SQLite)
├── game/
│   ├── emotion_service.py    # 8 эмоций, начисление по событиям
│   ├── infection_service.py  # Заражение + 12 комбо-мутаций
│   ├── emotion_birth_service.py  # Процедурное рождение монстров
│   ├── evolution_service.py  # Эволюция с сохранением в БД
│   ├── encounter_service.py  # Бой с типами и комбо-бонусами
│   ├── pvp_service.py        # PvP-арена
│   ├── guild_service.py      # Гильдии и рейды
│   ├── daily_service.py      # Ежедневные задания, streak, лидерборд
│   ├── season_pass_service.py # Сезонный пасс
│   ├── p2p_market_service.py # P2P-рынок монстров
│   ├── stars_shop.py         # Telegram Stars IAP
│   └── location_rules.py     # Замки прогрессии по локациям
├── handlers/                 # Telegram-хендлеры
├── keyboards/                # Клавиатуры
└── utils/
    ├── cooldown.py           # Антиспам
    ├── notifier.py           # Push-уведомления
    ├── analytics.py          # Аналитика событий
    ├── logger.py             # Логирование
    ├── battle_state.py       # Состояние боя
    └── board_orders.py       # Городские заказы
```

## Монетизация

- **Telegram Stars** — флаконы эмоций, энергия, слоты, сезонный пасс
- **P2P-рынок** — комиссия 8% с каждой сделки
- **Сезонный пасс** — 300 Stars, двойные награды за задания

## Архитектура данных

Все данные хранятся в SQLite с WAL-режимом.
При перезапуске бота ничего не теряется.
БД автоматически создаётся при первом запуске.
