import logging
import json
from scraper_ofert_tv.storage import get_connection, now_iso
from scraper_ofert_tv.normalization import normalize_offer_data
from scraper_ofert_tv.comparison import generate_comparable_keys, calculate_normalization_confidence

logger = logging.getLogger(__name__)

def run_backfill(db_path=None):
    conn = get_connection(db_path) if db_path else get_connection()
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
        SELECT o.id, o.category_id, o.title AS current_title, o.raw_title AS current_raw_title,
               o.raw_price, o.price_pln, o.is_free, o.negotiable, o.olx_size_bucket, o.raw_location,
               s.title AS detail_title, s.description, s.params_json
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
            'full_title': row['detail_title'],
            'description': row['description'],
            'params': json.loads(row['params_json']) if row['params_json'] else {}
        }
        
        category_id = row['category_id'] or 'televisions'
        normalized = normalize_offer_data(offer_dict, detail_dict, specs_cache, category_id=category_id)
        keys = generate_comparable_keys(normalized, category_id=category_id)
        comp_key = keys.get('A') or next(iter(keys.values()), None)
        confidence = calculate_normalization_confidence(normalized, category_id=category_id)
        detail_title = (row['detail_title'] or '').strip()
        if not detail_title or len(detail_title) > 120:
            detail_title = None
        
        # aktualizacja tylko normalizacji
        cursor.execute("""
            UPDATE offers 
            SET title = COALESCE(?, title), raw_title = COALESCE(?, raw_title),
                brand = ?, model = ?, technology = ?, resolution = ?, detected_size_inches = ?,
                attributes_json = ?, condition_value = COALESCE(?, condition_value),
                comparable_key = ?, comparison_confidence = ?, 
                normalization_diagnostics_json = ?, updated_at = ?
            WHERE id = ?
        """, (
            detail_title, detail_title,
            normalized.get('brand'), normalized.get('model_name'), normalized.get('technology'), 
            normalized.get('resolution'), normalized.get('size_inches'),
            json.dumps(normalized.get('attributes', {}), ensure_ascii=False), normalized.get('condition_value'),
            comp_key, str(confidence), json.dumps(normalized.get('diagnostics', {})),
            now, offer_id
        ))
        updated += 1
        
    conn.commit()
    conn.close()
    
    print(f"Zakonczono backfill normalizacji. Zaktualizowano {updated} ofert.")
