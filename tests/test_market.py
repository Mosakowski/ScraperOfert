import pytest
from scraper_ofert_tv.market import recalculate_market
from scraper_ofert_tv.migrations import apply_migrations
from scraper_ofert_tv.storage import now_iso

@pytest.fixture
def db_with_offers(tmp_path):
    db_path = tmp_path / "test_market.sqlite"
    apply_migrations(db_path)
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Dodajmy kilka testowych ofert dla klucza "lg_55_oled_4k"
    now = now_iso()
    offers = [
        ("hash1", "lg", "oled", "4k", 55, 3000, "new"),
        ("hash2", "lg", "oled", "4k", 55, 3200, "new"),
        ("hash3", "lg", "oled", "4k", 55, 2900, "new"),
        ("hash4", "lg", "oled", "4k", 55, 4000, "new"), # Odchylenie, ale nadal valid
        ("hash5", "lg", "oled", "4k", 55, 1000, "rejected"), # To powinno byc zignorowane
        ("hash6", "samsung", "qled", "4k", 65, 5000, "new"),
    ]
    
    for h, brand, tech, res, size, price, sys_stat in offers:
        conn.execute("""
            INSERT INTO offers (
                url_hash, brand, technology, resolution, detected_size_inches, price_pln, system_status, 
                first_seen_at, last_seen_at, created_at, updated_at, url, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (h, brand, tech, res, size, price, sys_stat, now, now, now, now,
              f'https://www.olx.pl/d/oferta/telewizor-{brand}-CID99-ID{h}.html', 'olx'))

    conn.execute("UPDATE offers SET attributes_json = ?", ('{"sale_format":"single"}',))
    conn.execute("""INSERT INTO offer_snapshots (offer_id, scan_mode, scraped_at)
                    SELECT id, 'detail_fetch', ? FROM offers""", (now,))
    
    conn.commit()
    return conn

def test_recalculate_market(db_with_offers):
    recalculate_market(db_with_offers)
    
    cursor = db_with_offers.cursor()
    cursor.execute("SELECT * FROM market_price_references WHERE comparable_key = 'lg_55_oled_4k'")
    ref = cursor.fetchone()
    
    assert ref is not None
    assert ref['offers_count'] == 4 # Poniewaz rejected jest zignorowane
    assert ref['min_price_pln'] == 2900
    # Srednia z [2900, 3000, 3200, 4000] = 3275
    assert ref['avg_price_pln'] == 3275
    # Mediana z [2900, 3000, 3200, 4000] = (3000+3200)/2 = 3100
    assert ref['median_price_pln'] == 3100
    
    # p25 (index 1) = 3000
    assert ref['p25_price_pln'] == 3000
    
    cursor.execute("SELECT * FROM market_price_references WHERE comparable_key = 'samsung_65_qled_4k'")
    ref2 = cursor.fetchone()
    assert ref2['offers_count'] == 1
    assert float(ref2['confidence']) == 0.3
    assert ref2['median_price_pln'] == 5000


def test_bundle_does_not_change_market_reference(db_with_offers):
    now = now_iso()
    db_with_offers.execute("""INSERT INTO offers
        (url_hash, brand, technology, resolution, detected_size_inches, price_pln,
         system_status, first_seen_at, last_seen_at, created_at, updated_at, url, source, attributes_json)
        VALUES ('bundle', 'lg', 'oled', '4k', 55, 10000, 'review_bundle', ?, ?, ?, ?, 'bundle', 'olx', ?)
    """, (now, now, now, now, '{"sale_format":"bundle_multiple"}'))
    offer_id = db_with_offers.execute("SELECT id FROM offers WHERE url_hash='bundle'").fetchone()[0]
    db_with_offers.execute("INSERT INTO offer_snapshots (offer_id, scan_mode, scraped_at) VALUES (?, 'detail_fetch', ?)", (offer_id, now))
    db_with_offers.commit()
    recalculate_market(db_with_offers)
    row = db_with_offers.execute("SELECT offers_count,median_price_pln FROM market_price_references WHERE comparable_key='lg_55_oled_4k'").fetchone()
    assert tuple(row) == (4, 3100)
