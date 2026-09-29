import pytest
from scraper_ofert_tv.alerts import process_alerts
from scraper_ofert_tv.migrations import apply_migrations
from scraper_ofert_tv.storage import now_iso

@pytest.fixture
def db_with_alert_data(tmp_path):
    db_path = tmp_path / "test_alerts.sqlite"
    apply_migrations(db_path)
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    now = now_iso()
    
    # 1. Oferta z Lodzi ktora jest super okazja
    conn.execute("""
        INSERT INTO offers (
            id, url_hash, comparable_key, price_pln, system_status, city,
            first_seen_at, last_seen_at, created_at, updated_at, url, source
        ) VALUES (1, 'hash1', 'lg_55', 1000, 'opportunity', 'Łódź', ?, ?, ?, ?, 'http', 'olx')
    """, (now, now, now, now))
    
    conn.execute("""
        INSERT INTO offer_scores (
            offer_id, score, system_status, reference_price_pln, estimated_profit_pln, 
            market_discount_percent, comparison_confidence, comparable_offers_count, calculated_at
        ) VALUES (1, 80, 'opportunity', 3000, 1950, 66.0, '0.9', 5, ?)
    """, (now,))
    
    # 2. Oferta z Lodzi ktora jest opportunity, ale slabe confidence
    conn.execute("""
        INSERT INTO offers (
            id, url_hash, comparable_key, price_pln, system_status, city,
            first_seen_at, last_seen_at, created_at, updated_at, url, source
        ) VALUES (2, 'hash2', 'lg_55', 1000, 'opportunity', 'Łódź', ?, ?, ?, ?, 'http', 'olx')
    """, (now, now, now, now))
    
    conn.execute("""
        INSERT INTO offer_scores (
            offer_id, score, system_status, reference_price_pln, estimated_profit_pln, 
            market_discount_percent, comparison_confidence, comparable_offers_count, calculated_at
        ) VALUES (2, 40, 'opportunity', 3000, 1950, 66.0, '0.5', 5, ?)
    """, (now,))
    
    conn.commit()
    return conn

def test_process_alerts(db_with_alert_data):
    process_alerts(db_with_alert_data)
    
    cursor = db_with_alert_data.cursor()
    cursor.execute("SELECT * FROM alert_events")
    alerts = cursor.fetchall()
    
    assert len(alerts) == 1
    assert alerts[0]['offer_id'] == 1
    assert alerts[0]['alert_type'] == 'lodz_opportunity'
