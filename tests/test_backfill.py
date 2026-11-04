import pytest
import sqlite3
import json
from scraper_ofert_tv.storage import now_iso
from scraper_ofert_tv.normalization import normalize_offer_data
from scraper_ofert_tv.comparison import generate_comparable_key, calculate_confidence

def test_backfill_logic():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    with open('src/scraper_ofert_tv/schema.sql', 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())
        
    try:
        cursor.execute("ALTER TABLE offers ADD COLUMN normalization_diagnostics_json TEXT")
    except sqlite3.OperationalError:
        pass
        
    now = now_iso()
    cursor.execute("""
        INSERT INTO offers (id, url, url_hash, system_status, first_seen_at, last_seen_at, created_at, updated_at)
        VALUES (1, 'http://olx.pl/1', 'hash1', 'new', ?, ?, ?, ?)
    """, (now, now, now, now))
    
    cursor.execute("""
        INSERT INTO offer_snapshots (offer_id, scan_mode, title, description, params_json, scraped_at)
        VALUES (1, 'detail_fetch', 'Telewizor Samsung QE55Q60T', 'Stan bdb', ?, ?)
    """, (json.dumps({"Marka": "Samsung", "Przekątna ekranu": "55 cali"}), now))
    
    conn.commit()
    
    # Symulacja backfill
    cursor.execute("""
        SELECT o.id, o.raw_price, o.price_pln, o.is_free, o.negotiable, o.olx_size_bucket, o.raw_location,
               s.title, s.description, s.params_json
        FROM offers o
        JOIN offer_snapshots s ON s.offer_id = o.id
        WHERE s.scan_mode = 'detail_fetch'
    """)
    rows = cursor.fetchall()
    
    for row in rows:
        offer_id = row['id']
        offer_dict = {
            'raw_price': row['raw_price'], 'price_pln': row['price_pln'], 'is_free': row['is_free'],
            'negotiable': row['negotiable'], 'olx_size_bucket': row['olx_size_bucket'], 'raw_location': row['raw_location']
        }
        detail_dict = {
            'full_title': row['title'], 'description': row['description'],
            'params': json.loads(row['params_json']) if row['params_json'] else {}
        }
        normalized = normalize_offer_data(offer_dict, detail_dict)
        comp_key = generate_comparable_key(normalized)
        conf = calculate_confidence(normalized, comp_key)
        
        cursor.execute("""
            UPDATE offers 
            SET brand = ?, model = ?, technology = ?, resolution = ?, detected_size_inches = ?,
                comparable_key = ?, comparison_confidence = ?, 
                normalization_diagnostics_json = ?
            WHERE id = ?
        """, (
            normalized.get('brand'), normalized.get('model_name'), normalized.get('technology'), 
            normalized.get('resolution'), normalized.get('size_inches'),
            comp_key, str(conf), json.dumps(normalized.get('diagnostics', {})), offer_id
        ))
        
    conn.commit()
    
    cursor.execute("SELECT brand, model, detected_size_inches, comparable_key, normalization_diagnostics_json FROM offers WHERE id = 1")
    res = cursor.fetchone()
    
    assert res['brand'] == 'samsung'
    assert res['model'] == 'QE55Q60T'
    assert res['detected_size_inches'] == 55
    assert 'qe55q60t' in res['comparable_key']
    
    diag = json.loads(res['normalization_diagnostics_json'])
    assert diag['model_source'] == 'title'
