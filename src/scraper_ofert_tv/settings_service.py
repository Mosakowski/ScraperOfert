import json
import yaml
from pathlib import Path
from scraper_ofert_tv.storage import get_connection, now_iso

class SettingsService:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path

    def get_setting(self, key: str, default=None):
        conn = get_connection(self.db_path) if self.db_path else get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value_json FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['value_json'])
        return default

    def set_setting(self, key: str, value: dict, description: str = ""):
        conn = get_connection(self.db_path) if self.db_path else get_connection()
        cursor = conn.cursor()
        
        # Upsert
        cursor.execute("SELECT key FROM settings WHERE key = ?", (key,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE settings SET value_json = ?, description = ?, updated_at = ? WHERE key = ?",
                (json.dumps(value), description, now_iso(), key)
            )
        else:
            cursor.execute(
                "INSERT INTO settings (key, value_json, description, updated_at) VALUES (?, ?, ?, ?)",
                (key, json.dumps(value), description, now_iso())
            )
            
        conn.commit()
        conn.close()

    def get_global_filters(self):
        return self.get_setting("global_filters", {})

    def get_national_scan_settings(self):
        return self.get_setting("national_scan", {"enabled": True, "max_pages_per_profile": 25})

    def get_lodz_alerts_settings(self):
        return self.get_setting("lodz_alerts", {"enabled": True, "location": "lodz", "radius_km": 50, "max_pages_per_profile": 5})

    def get_rate_limit_settings(self):
        return self.get_setting("rate_limit", {"requests_per_minute": 30, "delay_between_requests": 2})

    def get_scraper_settings(self):
        return self.get_setting("scraper_settings", {"fetch_backend": "httpx"})
        
    def get_scoring_settings(self):
        return self.get_setting("scoring_settings", {})

    def get_size_profiles(self):
        conn = get_connection(self.db_path) if self.db_path else get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM size_profiles ORDER BY sort_order")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
        
    def export_to_yaml(self, path: Path):
        data = {
            "global_filters": self.get_global_filters(),
            "modes": {
                "national": self.get_national_scan_settings(),
                "lodz_alerts": self.get_lodz_alerts_settings()
            },
            "rate_limit": self.get_rate_limit_settings(),
            "scraper_settings": self.get_scraper_settings(),
            "scoring_settings": self.get_scoring_settings(),
            "size_profiles": self.get_size_profiles()
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
            
    def import_from_yaml(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        if "global_filters" in data:
            self.set_setting("global_filters", data["global_filters"])
        if "modes" in data:
            if "national" in data["modes"]:
                self.set_setting("national_scan", data["modes"]["national"])
            if "lodz_alerts" in data["modes"]:
                self.set_setting("lodz_alerts", data["modes"]["lodz_alerts"])
        if "rate_limit" in data:
            self.set_setting("rate_limit", data["rate_limit"])
        if "scraper_settings" in data:
            self.set_setting("scraper_settings", data["scraper_settings"])
        if "scoring_settings" in data:
            self.set_setting("scoring_settings", data["scoring_settings"])
            
        if "size_profiles" in data:
            conn = get_connection(self.db_path) if self.db_path else get_connection()
            cursor = conn.cursor()
            for sp in data["size_profiles"]:
                # Prosty upsert (dla uproszczenia pomijamy czesc pol w demo)
                cursor.execute(
                    "UPDATE size_profiles SET label=?, olx_size_value=?, enabled=? WHERE id=?",
                    (sp.get('label'), sp.get('olx_size_filter') or sp.get('olx_size_value'), sp.get('enabled', 1), sp.get('id'))
                )
            conn.commit()
            conn.close()
