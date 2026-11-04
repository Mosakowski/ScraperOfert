import pytest
from pathlib import Path

from scraper_ofert_tv.settings_service import SettingsService
from scraper_ofert_tv.migrations import apply_migrations

@pytest.fixture
def memory_db_settings(tmp_path):
    db_path = tmp_path / "test_settings.sqlite"
    apply_migrations(db_path)
    return db_path

def test_get_global_filters(memory_db_settings):
    service = SettingsService(memory_db_settings)
    filters = service.get_global_filters()
    assert filters.get("price_min", 300) == 300
    assert filters.get("price_max", 700) == 700
    assert filters.get("seller_type", "private") == "private"
    assert filters.get("condition", "used") == "used"

def test_get_size_profiles(memory_db_settings):
    service = SettingsService(memory_db_settings)
    profiles = service.get_size_profiles()
    assert len(profiles) == 7
    ids = [p['id'] for p in profiles]
    assert "40_49" in ids
    
def test_set_setting(memory_db_settings):
    service = SettingsService(memory_db_settings)
    service.set_setting("rate_limit", {"requests_per_minute": 60})
    settings = service.get_rate_limit_settings()
    assert settings["requests_per_minute"] == 60
