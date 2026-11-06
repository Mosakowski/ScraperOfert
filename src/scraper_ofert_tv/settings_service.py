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

    def get_categories(self, enabled_only: bool = True):
        conn = get_connection(self.db_path) if self.db_path else get_connection()
        query = "SELECT * FROM categories"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY label"
        rows = [dict(row) for row in conn.execute(query).fetchall()]
        conn.close()
        for row in rows:
            row["allowed_filter_params"] = json.loads(row.pop("allowed_filter_params_json", "[]"))
        return rows

    def get_search_profiles(self, enabled_only: bool = False):
        conn = get_connection(self.db_path) if self.db_path else get_connection()
        query = """
            SELECT p.*, c.label AS category_label, c.path AS category_path,
                   c.domain AS category_domain, c.allowed_filter_params_json
            FROM search_profiles p JOIN categories c ON c.id = p.category_id
        """
        if enabled_only:
            query += " WHERE p.enabled = 1 AND c.enabled = 1"
        query += " ORDER BY p.priority DESC, c.label, p.label"
        rows = [dict(row) for row in conn.execute(query).fetchall()]
        conn.close()
        for row in rows:
            row["filters"] = json.loads(row.pop("filters_json", "{}"))
            row["allowed_filter_params"] = json.loads(row.pop("allowed_filter_params_json", "[]"))
        return rows

    def save_search_profile(self, profile_id: str, category_id: str, label: str,
                            filters: dict, max_pages: int = 5, enabled: int = 1, interval_hours: int = 0):
        conn = get_connection(self.db_path) if self.db_path else get_connection()
        category = conn.execute("SELECT id, allowed_filter_params_json FROM categories WHERE id=? AND enabled=1", (category_id,)).fetchone()
        if not category:
            conn.close()
            raise ValueError("Nieznana lub wyłączona kategoria OLX")
        allowed = set(json.loads(category["allowed_filter_params_json"] or "[]"))
        requested = set((filters.get("olx_filters") or {}).keys())
        if not requested.issubset(allowed):
            conn.close()
            raise ValueError("Profil używa filtra, którego nie skonfigurowano dla kategorii")
        max_pages = max(1, min(int(max_pages), 100))
        interval_hours = max(0, min(int(interval_hours), 168))
        now = now_iso()
        conn.execute("""
            INSERT INTO search_profiles
              (id, category_id, label, enabled, filters_json, max_pages, interval_hours,
               priority, legacy_size_profile_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 100, NULL, ?, ?)
            ON CONFLICT(id) DO UPDATE SET category_id=excluded.category_id,
              label=excluded.label, enabled=excluded.enabled, filters_json=excluded.filters_json,
              max_pages=excluded.max_pages, interval_hours=excluded.interval_hours, updated_at=excluded.updated_at
        """, (profile_id, category_id, label, enabled, json.dumps(filters), max_pages, interval_hours, now, now))
        conn.commit()
        conn.close()

    def save_category(self, category_id: str, label: str, path: str, allowed_filter_params: list[str]):
        conn = get_connection(self.db_path) if self.db_path else get_connection()
        now = now_iso()
        conn.execute("""
            INSERT INTO categories
              (id, label, path, domain, allowed_filter_params_json, enabled, created_at, updated_at)
            VALUES (?, ?, ?, 'generic', ?, 1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET label=excluded.label, path=excluded.path,
              allowed_filter_params_json=excluded.allowed_filter_params_json,
              enabled=1, updated_at=excluded.updated_at
        """, (category_id, label, path, json.dumps(allowed_filter_params), now, now))
        conn.commit()
        conn.close()
        
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
