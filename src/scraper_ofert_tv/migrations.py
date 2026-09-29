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

    conn.close()
