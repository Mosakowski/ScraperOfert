import pytest
import sqlite3
import os
from scraper_ofert_tv.storage import get_connection
from scraper_ofert_tv.scanner import Scanner

# Mock the ListingScraper so it returns our fixture HTML
class MockListingScraper:
    def __init__(self, *args, **kwargs):
        pass
    def fetch_listing(self, url):
        # We only want to process one page
        if "page=" in url or "page" in url:
            return None, "not_found", {}
        with open("tests/fixtures/real_listing_mock.html", "r", encoding="utf-8") as f:
            return f.read(), None, {}
    def close(self):
        pass

def test_scanner_integration(monkeypatch, tmp_path):
    # Setup test DB
    db_path = tmp_path / "test.sqlite"
    conn = get_connection(db_path)
    
    # Run migrations
    from scraper_ofert_tv.migrations import apply_migrations
    apply_migrations(db_path)
    
    # Seed size profiles and settings so scanner has something to scan
    from scraper_ofert_tv.settings_service import SettingsService
    service = SettingsService(db_path)
    service.set_setting("global_filters", {})
    service.set_setting("national_scan", {"enabled": True, "max_pages_per_profile": 1})
    
    # Enable just one profile for speed
    conn.execute("UPDATE size_profiles SET enabled = 0")
    conn.execute("UPDATE size_profiles SET enabled = 1 WHERE id = '40_49'")
    conn.commit()

    # Patch scanner components
    monkeypatch.setattr("scraper_ofert_tv.scanner.get_connection", lambda: get_connection(db_path))
    monkeypatch.setattr("scraper_ofert_tv.scanner.ListingScraper", MockListingScraper)
    
    # Run scanner
    scanner = Scanner()
    # Explicitly set settings service to use test DB
    scanner.settings = service
    scanner.run_scan("national", specific_profile="40_49")
    
    # Assertions
    # 1. Sprawdz czy ofera zostala zapisana do offers
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM offers")
    assert cursor.fetchone()[0] == 1
    
    cursor.execute("SELECT * FROM offers LIMIT 1")
    offer = cursor.fetchone()
    assert offer['title'] == 'Telewizor LG OLED 55 cali'
    assert offer['price_pln'] == 1500
    assert offer['url'] == 'https://www.olx.pl/d/oferta/telewizor-lg-oled-55-cali-ID12345.html'
    
    # 2. Sprawdz czy powstal snapshot
    cursor.execute("SELECT count(*) FROM offer_snapshots")
    assert cursor.fetchone()[0] == 1
    
    # 3. Sprawdz czy trafilo do kolejki detali
    cursor.execute("SELECT count(*) FROM details_queue WHERE offer_id = ?", (offer['id'],))
    assert cursor.fetchone()[0] == 1
    
    # 4. Sprawdz czy parser_warnings zostaly uzupelnione
    cursor.execute("SELECT parser_warnings_json FROM search_profile_runs LIMIT 1")
    warnings = cursor.fetchone()[0]
    assert warnings is not None
    assert "Uzyto heurystyki awaryjnej dla linkow /d/oferta/" in warnings
