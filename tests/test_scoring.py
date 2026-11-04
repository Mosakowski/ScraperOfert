import pytest
from scraper_ofert_tv.scoring import score_offers
from scraper_ofert_tv.migrations import apply_migrations
from scraper_ofert_tv.storage import now_iso

@pytest.fixture
def db_with_scoring_data(tmp_path):
    db_path = tmp_path / "test_scoring.sqlite"
    apply_migrations(db_path)
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    now = now_iso()
    
    # 1. Referencja cenowa
    conn.execute("""
        INSERT INTO market_price_references (
            comparable_key, min_price_pln, avg_price_pln, median_price_pln,
            p25_price_pln, p75_price_pln, offers_count, calculated_at, confidence
        ) VALUES ('lg_55_oled_4k', 2500, 3000, 3100, 2800, 3500, 5, ?, '0.8')
    """, (now,))
    
    # 2. Oferta dobra (okazja)
    conn.execute("""
        INSERT INTO offers (
            id, url_hash, brand, technology, resolution, detected_size_inches, price_pln, system_status,
            first_seen_at, last_seen_at, created_at, updated_at, url, source, comparison_confidence
        ) VALUES (1, 'hash1', 'lg', 'oled', '4k', 55, 2000, 'new', ?, ?, ?, ?, 'http', 'olx', '1.0')
    """, (now, now, now, now))
    
    # 3. Oferta z uszkodzeniem (reject)
    conn.execute("""
        INSERT INTO offers (
            id, url_hash, brand, technology, resolution, detected_size_inches, price_pln, system_status,
            first_seen_at, last_seen_at, created_at, updated_at, url, source, comparison_confidence
        ) VALUES (2, 'hash2', 'lg', 'oled', '4k', 55, 500, 'new', ?, ?, ?, ?, 'http', 'olx', '1.0')
    """, (now, now, now, now))
    conn.execute("INSERT INTO rule_matches (offer_id, rule_id, category, severity, action, score_delta, matched_at) VALUES (2, 'broken', 'red_flag', 'high', 'reject', -100, ?)", (now,))

    # 4. Oferta weak match
    conn.execute("""
        INSERT INTO offers (
            id, url_hash, brand, technology, resolution, detected_size_inches, price_pln, system_status,
            first_seen_at, last_seen_at, created_at, updated_at, url, source, comparison_confidence
        ) VALUES (3, 'hash3', 'lg', 'oled', '4k', 55, 1500, 'weak_match', ?, ?, ?, ?, 'http', 'olx', '0.2')
    """, (now, now, now, now))
    
    conn.commit()
    return conn

def test_score_offers(db_with_scoring_data):
    score_offers(db_with_scoring_data)
    
    cursor = db_with_scoring_data.cursor()
    
    # Sprawdz 1 (Okazja) - (3100-2000)/3100 = 35% rabat. Profit: 3100-2000-50 = 1050.
    cursor.execute("SELECT * FROM offers WHERE id = 1")
    offer1 = cursor.fetchone()
    assert offer1['system_status'] == 'opportunity'
    
    # Sprawdz 2 (Reject)
    cursor.execute("SELECT * FROM offers WHERE id = 2")
    offer2 = cursor.fetchone()
    assert offer2['system_status'] == 'rejected'
    
    # Sprawdz 3 (Weak Match - nie powinno stac sie okazja pomimo ceny 1500)
    cursor.execute("SELECT * FROM offers WHERE id = 3")
    offer3 = cursor.fetchone()
    assert offer3['system_status'] == 'weak_match'
