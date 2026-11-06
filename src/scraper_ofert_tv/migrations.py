import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

from scraper_ofert_tv.storage import get_connection

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def apply_migrations(db_path: Path = None):
    """Odczytuje plik schema.sql i uruchamia na bazie."""
    conn = get_connection(db_path) if db_path else get_connection()
    
    # Check if schema_migrations table exists, if not run everything
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
    schema_exists = cursor.fetchone() is not None

    if not schema_exists:
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_script = f.read()
        
        # Wykonaj caly schemat
        cursor.executescript(schema_script)
        
        # Oznacz migracje jako wykonana
        cursor.execute(
            "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
            (1, "initial_schema", now_iso())
        )
        
        # Seed Settings
        default_settings = {
            "global_filters": {
                "price_min": 300,
                "price_max": 700,
                "seller_type": "private",
                "condition": "used"
            }
        }
        cursor.execute(
            "INSERT INTO settings (key, value_json, description, updated_at) VALUES (?, ?, ?, ?)",
            ("global_filters", json.dumps(default_settings["global_filters"]), "Globalne filtry (cena, typ sprzedawcy, stan)", now_iso())
        )
        
        # Seed Size Profiles
        profiles = [
            ("lt_30", "Mniejszy niz 30 cali", "lt-30", None, 29, 1, 1),
            ("30_39", "30-39 cali", "30-39", 30, 39, 1, 2),
            ("40_49", "40-49 cali", "40-49", 40, 49, 1, 3),
            ("50_59", "50-59 cali", "50-59", 50, 59, 1, 4),
            ("60_69", "60-69 cali", "60-69", 60, 69, 1, 5),
            ("70_79", "70-79 cali", "70-79", 70, 79, 1, 6),
            ("gt_80", "Wiekszy niz 80 cali", "gt-80", 80, None, 1, 7)
        ]
        cursor.executemany(
            """INSERT INTO size_profiles 
               (id, label, olx_size_value, min_inches, max_inches, enabled, sort_order, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], now_iso(), now_iso()) for p in profiles]
        )
        
        # Seed Rules
        rules = [
            ("damaged_matrix", 1, "red_flag", "high", "Uszkodzona matryca", "title,description", "phrase", json.dumps(["uszkodzona matryca", "zbita matryca", "pasy na ekranie", "peknieta matryca"]), -80.0, "reject"),
            ("no_image", 1, "exclude", "critical", "Brak obrazu", "title,description", "phrase", json.dumps(["brak obrazu", "czarny ekran"]), -100.0, "reject"),
            ("no_remote", 1, "warning", "low", "Brak pilota", "title,description", "phrase", json.dumps(["brak pilota", "bez pilota"]), -10.0, "flag"),
            ("no_stand", 1, "warning", "low", "Brak podstawy", "title,description", "phrase", json.dumps(["brak podstawy", "bez nogi", "bez podstawki"]), -10.0, "flag"),
            ("oled", 1, "positive", "medium", "OLED", "title,description,parameters", "phrase", json.dumps(["oled"]), 20.0, "flag"),
            ("four_k", 1, "positive", "low", "4K", "title,description,parameters", "phrase", json.dumps(["4k", "uhd", "ultra hd"]), 10.0, "flag"),
            ("service_offer", 1, "exclude", "critical", "Usluga serwisowa", "title,description", "phrase", json.dumps(["naprawa telewizorow", "serwis telewizorow", "wymiana matryc"]), -100.0, "reject"),
        ]
        cursor.executemany(
            """INSERT INTO description_rules 
               (id, enabled, category, severity, label, applies_to, match_mode, patterns_json, score_delta, action, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], now_iso(), now_iso()) for r in rules]
        )
        
        conn.commit()

    # Migration 2: model_specs
    cursor.execute("SELECT 1 FROM schema_migrations WHERE version=2")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_specs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              brand TEXT NOT NULL,
              model TEXT NOT NULL,
              normalized_model TEXT NOT NULL,
              screen_size_inches INTEGER,
              technology TEXT,
              resolution TEXT,
              year INTEGER,
              series TEXT,
              source_url TEXT,
              source_name TEXT,
              spec_confidence REAL,
              notes TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              UNIQUE(brand, normalized_model)
            )
        """)
        cursor.execute(
            "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
            (2, "add_model_specs", now_iso())
        )
        conn.commit()

    # Migration 3: categories, reusable monitoring profiles and typed attributes.
    cursor.execute("SELECT 1 FROM schema_migrations WHERE version=3")
    if not cursor.fetchone():
        def add_column(table: str, column: str, definition: str):
            columns = {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}
            if column not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
              id TEXT PRIMARY KEY,
              label TEXT NOT NULL,
              path TEXT NOT NULL,
              domain TEXT NOT NULL,
              allowed_filter_params_json TEXT NOT NULL DEFAULT '[]',
              enabled INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS search_profiles (
              id TEXT PRIMARY KEY,
              category_id TEXT NOT NULL,
              label TEXT NOT NULL,
              enabled INTEGER NOT NULL DEFAULT 1,
              filters_json TEXT NOT NULL DEFAULT '{}',
              max_pages INTEGER NOT NULL DEFAULT 5,
              interval_hours INTEGER NOT NULL DEFAULT 0,
              priority INTEGER NOT NULL DEFAULT 100,
              legacy_size_profile_id TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(category_id) REFERENCES categories(id)
            );
            CREATE INDEX IF NOT EXISTS idx_search_profiles_category_enabled
              ON search_profiles(category_id, enabled, priority);
        """)
        add_column("offers", "category_id", "TEXT NOT NULL DEFAULT 'televisions'")
        add_column("offers", "attributes_json", "TEXT NOT NULL DEFAULT '{}'")
        add_column("offer_snapshots", "category_id", "TEXT NOT NULL DEFAULT 'televisions'")
        add_column("comparable_groups", "category_id", "TEXT NOT NULL DEFAULT 'televisions'")
        add_column("description_rules", "product_category_id", "TEXT")
        add_column("search_profile_runs", "search_profile_id", "TEXT")
        add_column("size_profiles", "category_id", "TEXT NOT NULL DEFAULT 'televisions'")
        add_column("model_specs", "product_category_id", "TEXT NOT NULL DEFAULT 'televisions'")
        add_column("model_specs", "attributes_json", "TEXT NOT NULL DEFAULT '{}'")

        from scraper_ofert_tv.categories import CATEGORY_DEFINITIONS
        now = now_iso()
        for category_id, definition in CATEGORY_DEFINITIONS.items():
            cursor.execute("""
                INSERT OR IGNORE INTO categories
                (id, label, path, domain, allowed_filter_params_json, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (category_id, definition["label"], definition["path"], definition["domain"],
                  json.dumps(definition["allowed_filter_params"]), now, now))

        # Keep the old size profile IDs and history intact; expose each as a reusable TV search profile.
        tv_profiles = cursor.execute("SELECT * FROM size_profiles ORDER BY sort_order").fetchall()
        for row in tv_profiles:
            filters = {"olx_filters": {"search[filter_enum_size][0]": row["olx_size_value"]}}
            cursor.execute("UPDATE size_profiles SET category_id='televisions' WHERE id=?", (row["id"],))
            cursor.execute("""
                INSERT OR IGNORE INTO search_profiles
                (id, category_id, label, enabled, filters_json, max_pages, interval_hours, priority,
                 legacy_size_profile_id, created_at, updated_at)
                VALUES (?, 'televisions', ?, ?, ?, 25, 0, ?, ?, ?, ?)
            """, (row["id"], row["label"], row["enabled"], json.dumps(filters),
                  row["sort_order"], row["id"], now, now))

        # A legacy lookup row preserves the NOT NULL size_profile_id foreign key in old scan history.
        cursor.execute("""
            INSERT OR IGNORE INTO size_profiles
            (id, label, olx_size_value, min_inches, max_inches, enabled, sort_order, created_at, updated_at, category_id)
            VALUES ('laptops_all', 'Wszystkie laptopy', '', NULL, NULL, 1, 100, ?, ?, 'laptops')
        """, (now, now))
        cursor.execute("""
            INSERT OR IGNORE INTO search_profiles
            (id, category_id, label, enabled, filters_json, max_pages, interval_hours, priority,
             legacy_size_profile_id, created_at, updated_at)
            VALUES ('laptops_all', 'laptops', 'Laptopy · cała Polska', 1, '{}', 5, 0, 100,
                    'laptops_all', ?, ?)
        """, (now, now))

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_category_status ON offers(category_id, system_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_category_comparable ON offers(category_id, comparable_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_category ON offer_snapshots(category_id, scraped_at)")
        cursor.execute("UPDATE offer_snapshots SET category_id='televisions'")
        cursor.execute("UPDATE comparable_groups SET category_id='televisions'")
        cursor.execute("UPDATE description_rules SET product_category_id='televisions'")
        laptop_rules = [
            ("laptop_parts_exclude", "Części lub akcesoria zamiast laptopa", ["bateria do laptopa", "matryca do laptopa", "klawiatura do laptopa", "obudowa do laptopa", "części do laptopa", "zasilacz do laptopa"], "reject", -100.0),
            ("laptop_damaged", "Uszkodzony laptop", ["uszkodzony laptop", "na części", "nie działa", "nie uruchamia się", "uszkodzona matryca"], "reject", -70.0),
        ]
        for rule_id, label, patterns, action, score_delta in laptop_rules:
            cursor.execute("""
                INSERT OR IGNORE INTO description_rules
                (id, enabled, category, severity, label, applies_to, match_mode, patterns_json,
                 score_delta, action, product_category_id, created_at, updated_at)
                VALUES (?, 1, 'red_flag', 'high', ?, 'title,description', 'phrase', ?, ?, ?, 'laptops', ?, ?)
            """, (rule_id, label, json.dumps(patterns, ensure_ascii=False), score_delta, action, now, now))
        cursor.execute("""
            INSERT INTO schema_migrations (version, name, applied_at)
            VALUES (3, 'add_product_categories_and_search_profiles', ?)
        """, (now,))
        conn.commit()
        
    conn.close()
