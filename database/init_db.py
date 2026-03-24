from database.db import get_connection


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            telegram_id     INTEGER PRIMARY KEY,
            name            TEXT NOT NULL,
            location_slug   TEXT NOT NULL DEFAULT 'silver_city',
            current_region_slug TEXT NOT NULL DEFAULT 'valley_of_emotions',
            current_district_slug TEXT NOT NULL DEFAULT 'market_square',
            gold            INTEGER NOT NULL DEFAULT 120,
            level           INTEGER NOT NULL DEFAULT 1,
            experience      INTEGER NOT NULL DEFAULT 0,
            energy          INTEGER NOT NULL DEFAULT 12,
            birth_cooldown_actions INTEGER NOT NULL DEFAULT 0,
            strength        INTEGER NOT NULL DEFAULT 1,
            agility         INTEGER NOT NULL DEFAULT 1,
            intellect       INTEGER NOT NULL DEFAULT 1,
            stat_points     INTEGER NOT NULL DEFAULT 0,
            gatherer_level  INTEGER NOT NULL DEFAULT 1,
            gatherer_exp    INTEGER NOT NULL DEFAULT 0,
            hunter_level    INTEGER NOT NULL DEFAULT 1,
            hunter_exp      INTEGER NOT NULL DEFAULT 0,
            geologist_level INTEGER NOT NULL DEFAULT 1,
            geologist_exp   INTEGER NOT NULL DEFAULT 0,
            alchemist_level INTEGER NOT NULL DEFAULT 1,
            alchemist_exp   INTEGER NOT NULL DEFAULT 0,
            merchant_level  INTEGER NOT NULL DEFAULT 1,
            merchant_exp    INTEGER NOT NULL DEFAULT 0,
            bag_capacity    INTEGER NOT NULL DEFAULT 12,
            hp              INTEGER NOT NULL DEFAULT 30,
            max_hp          INTEGER NOT NULL DEFAULT 30,
            is_defeated     INTEGER NOT NULL DEFAULT 0,
            injury_turns    INTEGER NOT NULL DEFAULT 0,
            daily_streak    INTEGER NOT NULL DEFAULT 0,
            last_login_date TEXT NOT NULL DEFAULT '',
            season_pass_active INTEGER NOT NULL DEFAULT 0,
            season_points   INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS player_monsters (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id     INTEGER NOT NULL,
            name            TEXT NOT NULL,
            rarity          TEXT NOT NULL DEFAULT 'common',
            mood            TEXT NOT NULL DEFAULT 'instinct',
            monster_type    TEXT NOT NULL DEFAULT 'void',
            hp              INTEGER NOT NULL DEFAULT 10,
            max_hp          INTEGER NOT NULL DEFAULT 10,
            current_hp      INTEGER NOT NULL DEFAULT 10,
            attack          INTEGER NOT NULL DEFAULT 3,
            level           INTEGER NOT NULL DEFAULT 1,
            experience      INTEGER NOT NULL DEFAULT 0,
            is_active       INTEGER NOT NULL DEFAULT 0,
            infection_type  TEXT,
            infection_stage INTEGER NOT NULL DEFAULT 0,
            distortion      INTEGER NOT NULL DEFAULT 0,
            source_type     TEXT NOT NULL DEFAULT 'wild',
            evolution_stage INTEGER NOT NULL DEFAULT 0,
            evolution_from  TEXT,
            abilities       TEXT NOT NULL DEFAULT '[]',
            combo_mutation  TEXT,
            is_listed       INTEGER NOT NULL DEFAULT 0,
            list_price      INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS player_emotions (
            telegram_id     INTEGER PRIMARY KEY,
            rage            INTEGER NOT NULL DEFAULT 0,
            fear            INTEGER NOT NULL DEFAULT 0,
            instinct        INTEGER NOT NULL DEFAULT 0,
            inspiration     INTEGER NOT NULL DEFAULT 0,
            sadness         INTEGER NOT NULL DEFAULT 0,
            joy             INTEGER NOT NULL DEFAULT 0,
            disgust         INTEGER NOT NULL DEFAULT 0,
            surprise        INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS player_items (
            telegram_id     INTEGER NOT NULL,
            item_slug       TEXT NOT NULL,
            amount          INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, item_slug)
        );


        CREATE TABLE IF NOT EXISTS player_bags (
            telegram_id     INTEGER NOT NULL,
            bag_slug        TEXT NOT NULL,
            bag_name        TEXT NOT NULL,
            capacity        INTEGER NOT NULL,
            source          TEXT NOT NULL DEFAULT 'shop',
            is_equipped     INTEGER NOT NULL DEFAULT 0,
            sell_price      INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (telegram_id, bag_slug)
        );

        CREATE TABLE IF NOT EXISTS player_resources (
            telegram_id     INTEGER NOT NULL,
            slug            TEXT NOT NULL,
            amount          INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, slug)
        );

        CREATE TABLE IF NOT EXISTS player_quests (
            telegram_id     INTEGER NOT NULL,
            quest_id        TEXT NOT NULL,
            progress        INTEGER NOT NULL DEFAULT 0,
            completed       INTEGER NOT NULL DEFAULT 0,
            active          INTEGER NOT NULL DEFAULT 0,
            source          TEXT NOT NULL DEFAULT 'starter',
            PRIMARY KEY (telegram_id, quest_id)
        );

        CREATE TABLE IF NOT EXISTS player_story (
            telegram_id     INTEGER NOT NULL,
            story_id        TEXT NOT NULL,
            explore_count   INTEGER NOT NULL DEFAULT 0,
            win_count       INTEGER NOT NULL DEFAULT 0,
            visited         INTEGER NOT NULL DEFAULT 0,
            completed       INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, story_id)
        );

        CREATE TABLE IF NOT EXISTS player_story_index (
            telegram_id     INTEGER PRIMARY KEY,
            current_index   INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS player_codex (
            telegram_id     INTEGER NOT NULL,
            monster_name    TEXT NOT NULL,
            PRIMARY KEY (telegram_id, monster_name)
        );

        CREATE TABLE IF NOT EXISTS player_relics (
            telegram_id     INTEGER NOT NULL,
            relic_slug      TEXT NOT NULL,
            PRIMARY KEY (telegram_id, relic_slug)
        );

        CREATE TABLE IF NOT EXISTS player_craft_quests (
            telegram_id     INTEGER NOT NULL,
            quest_id        TEXT NOT NULL,
            progress        INTEGER NOT NULL DEFAULT 0,
            completed       INTEGER NOT NULL DEFAULT 0,
            craft_key       TEXT NOT NULL DEFAULT '',
            count           INTEGER NOT NULL DEFAULT 1,
            title           TEXT NOT NULL DEFAULT '',
            reward_gold     INTEGER NOT NULL DEFAULT 0,
            reward_exp      INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, quest_id)
        );

        CREATE TABLE IF NOT EXISTS player_extra_quests (
            telegram_id     INTEGER NOT NULL,
            quest_id        TEXT NOT NULL,
            progress        INTEGER NOT NULL DEFAULT 0,
            completed       INTEGER NOT NULL DEFAULT 0,
            action_type     TEXT NOT NULL DEFAULT '',
            count           INTEGER NOT NULL DEFAULT 1,
            title           TEXT NOT NULL DEFAULT '',
            reward_gold     INTEGER NOT NULL DEFAULT 0,
            reward_exp      INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, quest_id)
        );

        CREATE TABLE IF NOT EXISTS player_board_quests (
            telegram_id     INTEGER NOT NULL,
            quest_id        TEXT NOT NULL,
            progress        INTEGER NOT NULL DEFAULT 0,
            completed       INTEGER NOT NULL DEFAULT 0,
            action_type     TEXT NOT NULL DEFAULT '',
            count           INTEGER NOT NULL DEFAULT 1,
            title           TEXT NOT NULL DEFAULT '',
            reward_gold     INTEGER NOT NULL DEFAULT 0,
            reward_exp      INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, quest_id)
        );

        CREATE TABLE IF NOT EXISTS player_guild_quests (
            telegram_id     INTEGER NOT NULL,
            quest_id        TEXT NOT NULL,
            progress        INTEGER NOT NULL DEFAULT 0,
            completed       INTEGER NOT NULL DEFAULT 0,
            guild_key       TEXT NOT NULL DEFAULT '',
            action_type     TEXT NOT NULL DEFAULT '',
            count           INTEGER NOT NULL DEFAULT 1,
            title           TEXT NOT NULL DEFAULT '',
            reward_gold     INTEGER NOT NULL DEFAULT 0,
            reward_exp      INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, quest_id)
        );

        CREATE TABLE IF NOT EXISTS player_city_orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id     INTEGER NOT NULL,
            order_slug      TEXT NOT NULL,
            title           TEXT NOT NULL,
            goal_text       TEXT NOT NULL,
            reward_gold     INTEGER NOT NULL,
            reward_exp      INTEGER NOT NULL,
            status          TEXT NOT NULL DEFAULT 'active',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pending_encounters (
            telegram_id     INTEGER PRIMARY KEY,
            data            TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS player_action_flags (
            telegram_id     INTEGER PRIMARY KEY,
            data            TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS player_ui (
            telegram_id     INTEGER PRIMARY KEY,
            screen          TEXT NOT NULL DEFAULT 'main',
            context_data    TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS market_items (
            item_slug       TEXT PRIMARY KEY,
            base_price      INTEGER NOT NULL DEFAULT 10,
            demand          REAL NOT NULL DEFAULT 0.0,
            updated_at      REAL NOT NULL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS market_monsters_npc (
            monster_slug    TEXT PRIMARY KEY,
            base_price      INTEGER NOT NULL DEFAULT 90,
            demand          REAL NOT NULL DEFAULT 0.0,
            updated_at      REAL NOT NULL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS city_resource_markets (
            city_slug       TEXT NOT NULL,
            resource_slug   TEXT NOT NULL,
            base_price      INTEGER NOT NULL DEFAULT 6,
            stock           REAL NOT NULL DEFAULT 8.0,
            target_stock    REAL NOT NULL DEFAULT 8.0,
            updated_at      REAL NOT NULL DEFAULT 0.0,
            PRIMARY KEY (city_slug, resource_slug)
        );

        CREATE TABLE IF NOT EXISTS player_pvp (
            telegram_id     INTEGER PRIMARY KEY,
            wins            INTEGER NOT NULL DEFAULT 0,
            losses          INTEGER NOT NULL DEFAULT 0,
            rating          INTEGER NOT NULL DEFAULT 1000
        );

        CREATE TABLE IF NOT EXISTS pvp_challenges (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            challenger_id   INTEGER NOT NULL,
            target_id       INTEGER NOT NULL,
            status          TEXT NOT NULL DEFAULT 'pending',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guilds (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            leader_id       INTEGER NOT NULL,
            description     TEXT NOT NULL DEFAULT '',
            treasury_gold   INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guild_members (
            guild_id        INTEGER NOT NULL,
            telegram_id     INTEGER NOT NULL,
            role            TEXT NOT NULL DEFAULT 'member',
            joined_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (guild_id, telegram_id)
        );

        CREATE TABLE IF NOT EXISTS daily_tasks (
            telegram_id     INTEGER NOT NULL,
            task_date       TEXT NOT NULL,
            task_id         TEXT NOT NULL,
            description     TEXT NOT NULL DEFAULT '',
            action_type     TEXT NOT NULL DEFAULT '',
            target          INTEGER NOT NULL DEFAULT 1,
            reward_gold     INTEGER NOT NULL DEFAULT 30,
            progress        INTEGER NOT NULL DEFAULT 0,
            completed       INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, task_date, task_id)
        );

        CREATE TABLE IF NOT EXISTS player_season_pass (
            telegram_id     INTEGER NOT NULL,
            season_id       INTEGER NOT NULL DEFAULT 1,
            task_id         TEXT NOT NULL,
            progress        INTEGER NOT NULL DEFAULT 0,
            completed       INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, season_id, task_id)
        );

        CREATE TABLE IF NOT EXISTS analytics_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id     INTEGER NOT NULL,
            event           TEXT NOT NULL,
            data            TEXT NOT NULL DEFAULT '{}',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_analytics_event ON analytics_events(event);
        CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_monsters_user ON player_monsters(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_monsters_listed ON player_monsters(is_listed);
        CREATE INDEX IF NOT EXISTS idx_quests_user ON player_quests(telegram_id);
        CREATE TABLE IF NOT EXISTS player_grid_exploration (
            telegram_id   INTEGER NOT NULL,
            location_slug TEXT    NOT NULL,
            grid_data     TEXT    NOT NULL DEFAULT '{}',
            PRIMARY KEY (telegram_id, location_slug)
        );

        CREATE TABLE IF NOT EXISTS player_exploration (
            telegram_id   INTEGER NOT NULL,
            location_slug TEXT    NOT NULL,
            pct           INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, location_slug)
        );

        CREATE TABLE IF NOT EXISTS player_bestiary (
            telegram_id     INTEGER NOT NULL,
            creature_name   TEXT    NOT NULL,
            creature_type   TEXT    NOT NULL DEFAULT 'wildlife',
            encounter_count INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (telegram_id, creature_name)
        );

        CREATE TABLE IF NOT EXISTS player_weekly_quests (
            telegram_id   INTEGER NOT NULL,
            location_slug TEXT    NOT NULL,
            week_key      TEXT    NOT NULL,
            quest_slug    TEXT    NOT NULL,
            progress      INTEGER NOT NULL DEFAULT 0,
            completed     INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (telegram_id, location_slug, week_key)
        );
        CREATE TABLE IF NOT EXISTS player_dungeon_progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id     INTEGER NOT NULL,
    dungeon_slug    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'available',
    cleared_at      TEXT,
    cooldown_until  TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (telegram_id, dungeon_slug)
);
        """)
        conn.commit()

    # Добавляем новые колонки для картографа если БД уже существует
    for _col, _def in [("cartographer_level", "1"), ("cartographer_exp", "0")]:
        try:
            with get_connection() as conn:
                conn.execute(f"ALTER TABLE players ADD COLUMN {_col} INTEGER DEFAULT {_def}")
                conn.commit()
        except Exception:
            pass
