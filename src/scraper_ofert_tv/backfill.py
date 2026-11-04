import logging
import json
from scraper_ofert_tv.storage import get_connection, now_iso
from scraper_ofert_tv.normalization import normalize_offer_data
from scraper_ofert_tv.comparison import generate_comparable_key, calculate_confidence

logger = logging.getLogger(__name__)

def run_backfill():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Dodanie kolumny, jesli nie istnieje
    try:
        cursor.execute("ALTER TABLE offers ADD COLUMN normalization_diagnostics_json TEXT")
        conn.commit()
    except Exception as e:
        if "duplicate column name" not in str(e).lower():
            logger.warning(f"Nie dodano kolumny: {e}")
            
    # Load model_specs into cache
    cursor.execute("SELECT * FROM model_specs")
    specs_cache = {}
    for r in cursor.fetchall():
        specs_cache[(r['brand'].lower(), r['normalized_model'])] = dict(r)

    # Pobierzmy wszystkie oferty, ktore maja przynajmniej jeden snapshot
    # Wybieramy najnowszy snapshot z 'detail_fetch' dla kazdej oferty.
    
    cursor.execute("""
        SELECT o.id, o.raw_price, o.price_pln, o.is_free, o.negotiable, o.olx_size_bucket, o.raw_location,
               s.title, s.description, s.params_json
        FROM offers o
        JOIN offer_snapshots s ON s.offer_id = o.id
        WHERE s.scan_mode = 'detail_fetch'
          AND s.id = (SELECT MAX(id) FROM offer_snapshots WHERE offer_id = o.id AND scan_mode = 'detail_fetch')
    """)
    
    rows = cursor.fetchall()
    updated = 0
    now = now_iso()
    
    for row in rows:
        offer_id = row['id']
        offer_dict = {
            'raw_price': row['raw_price'],
            'price_pln': row['price_pln'],
            'is_free': row['is_free'],
            'negotiable': row['negotiable'],
            'olx_size_bucket': row['olx_size_bucket'],
            'raw_location': row['raw_location']
        }
        
        detail_dict = {
            'full_title': row['title'],
            'description': row['description'],
            'params': json.loads(row['params_json']) if row['params_json'] else {}
        }
        
        normalized = normalize_offer_data(offer_dict, detail_dict, specs_cache)
        comp_key = generate_comparable_key(normalized)
        confidence = calculate_confidence(normalized, comp_key)
        
        # aktualizacja tylko normalizacji
        cursor.execute("""
            UPDATE offers 
            SET brand = ?, model = ?, technology = ?, resolution = ?, detected_size_inches = ?,
                comparable_key = ?, comparison_confidence = ?, 
                normalization_diagnostics_json = ?, updated_at = ?
            WHERE id = ?
        """, (
            normalized.get('brand'), normalized.get('model_name'), normalized.get('technology'), 
            normalized.get('resolution'), normalized.get('size_inches'),
            comp_key, str(confidence), json.dumps(normalized.get('diagnostics', {})),
            now, offer_id
        ))
        updated += 1
        
    conn.commit()
    conn.close()
    
    print(f"Zakonczono backfill normalizacji. Zaktualizowano {updated} ofert.")
