from fastapi.testclient import TestClient
from scraper_ofert_tv.web import app
from scraper_ofert_tv.storage import get_connection
import scraper_ofert_tv.storage
from pathlib import Path
import os
import sqlite3

# Tymczasowa baza testowa
TEST_DB = Path("data/test_web.sqlite")
if TEST_DB.exists():
    TEST_DB.unlink()

def mock_get_connection(db_path=None):
    db_path = TEST_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Patch w obu miejscach
scraper_ofert_tv.storage.get_connection = mock_get_connection
import scraper_ofert_tv.web
scraper_ofert_tv.web.get_connection = mock_get_connection
import scraper_ofert_tv.settings_service
scraper_ofert_tv.settings_service.get_connection = mock_get_connection

from scraper_ofert_tv.migrations import apply_migrations
apply_migrations(TEST_DB)

client = TestClient(app)

def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Przegląd · Panel TV" in response.text

def test_settings_page():
    response = client.get("/settings")
    assert response.status_code == 200
    assert "Ustawienia" in response.text
    assert "category-filter-fields" in response.text

def test_rules_page():
    response = client.get("/rules")
    assert response.status_code == 200
    assert "Reguły opisowe" in response.text

def test_save_settings():
    # Smoke test zapisu ustawien
    response = client.post("/settings/save", data={
        "price_min": 350, "price_max": 800,
        "seller_type": "private", "condition": "used",
        "national_hours": 10, "lodz_hours": 3, "export_hours": 1,
        "min_discount": 20.0, "min_profit": 150, "min_count": 5
    })
    assert response.status_code == 200 or response.status_code == 303 # Redirect
    
    # Check if saved
    from scraper_ofert_tv.settings_service import SettingsService
    srv = SettingsService()
    gf = srv.get_global_filters()
    assert gf["price_min"] == 350
    assert gf["price_max"] == 800

def test_add_rule():
    # Clean up first
    conn = mock_get_connection()
    conn.execute("DELETE FROM description_rules WHERE id = 'test_rule_123'")
    conn.commit()
    
    response = client.post("/rules/add", data={
        "rule_id": "test_rule_123",
        "category": "info",
        "applies_to": "title",
        "patterns": "test_pattern,other_pattern",
        "action": "info",
        "score_delta": 5
    })
    assert response.status_code == 200 or response.status_code == 303

    # Verify rule in DB
    c = conn.cursor()
    c.execute("SELECT id FROM description_rules WHERE id = 'test_rule_123'")
    assert c.fetchone() is not None
    conn.execute("DELETE FROM description_rules WHERE id = 'test_rule_123'")
    conn.commit()
    conn.close()

def test_rule_test_endpoint():
    response = client.post("/rules/test", data={"text": "Sprzedam telewizor z test_pattern ok."})
    assert response.status_code == 200 or response.status_code == 303

def test_dashboard_and_offers_accept_category_filter():
    assert client.get("/?category=laptops").status_code == 200
    assert client.get("/offers?category=laptops").status_code == 200

def test_save_category_filter_and_scoring_schema():
    response = client.post("/settings/category/save", data={
        "category_id": "test_printers", "label": "Drukarki testowe",
        "path": "/elektronika/drukarki/",
        "allowed_filter_params_json": '["search[filter_enum_brand][0]"]',
        "filter_schema_json": '[{"key":"search[filter_enum_brand][0]","label":"Marka","type":"select","options":["HP"]}]',
        "attribute_schema_json": '["brand","print_technology"]',
        "scoring_settings_json": '{"min_count":4}',
    }, follow_redirects=False)
    assert response.status_code == 303
    from scraper_ofert_tv.settings_service import SettingsService
    service = SettingsService()
    category = next(item for item in service.get_categories() if item["id"] == "test_printers")
    assert category["filter_schema"][0]["options"] == ["HP"]
    assert service.get_scoring_settings("test_printers")["min_count"] == 4
