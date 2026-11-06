import sqlite3
import statistics
import json
from typing import List, Dict, Any
from scraper_ofert_tv.storage import get_connection, now_iso

def recalculate_market(conn: sqlite3.Connection):
    """
    Przelicza grupowanie i mediany referencyjne na podstawie
    wszystkich NIE odrzuconych ofert w bazie.
    """
    cursor = conn.cursor()
    
    # Pobieramy oferty do wyliczen:
    # 1. status != 'inactive'
    from scraper_ofert_tv.comparison import generate_comparable_keys
    
    # Wyczyść stare referencje, aby uniknąć legacy
    cursor.execute("UPDATE offer_scores SET market_reference_id = NULL")
    cursor.execute("DELETE FROM market_price_references")
    
    cursor.execute("""
        SELECT brand, model, technology, resolution, detected_size_inches, olx_size_bucket,
               price_pln, category_id, attributes_json
        FROM offers 
        WHERE price_pln > 0 
          AND (system_status != 'rejected' OR system_status IS NULL)
          AND gone_at IS NULL
    """)
    rows = cursor.fetchall()
    
    # Grupowanie cen
    market_data = {}
    for row in rows:
        category_id = row["category_id"] or "televisions"
        normalized = {
            'brand': row['brand'],
            'model_name': row['model'],
            'technology': row['technology'],
            'resolution': row['resolution'],
            'size_inches': row['detected_size_inches'],
            'native_olx_bucket': row['olx_size_bucket'],
            'attributes': json.loads(row["attributes_json"] or "{}")
        }
        keys = generate_comparable_keys(normalized, category_id=category_id)
        price = row['price_pln']
        for k_level, key in keys.items():
            if key not in market_data:
                market_data[key] = []
            market_data[key].append(price)
        
    # Zapis do market_price_references
    now = now_iso()
    for key, prices in market_data.items():
        if not prices:
            continue
            
        prices.sort()
        count = len(prices)
        price_min = min(prices)
        price_max = max(prices)
        price_avg = int(sum(prices) / count)
        price_median = int(statistics.median(prices))
        
        # p25 (dolny kwartyl)
        if count >= 4:
            idx_p25 = int(count * 0.25)
            price_p25 = prices[idx_p25]
        else:
            price_p25 = price_min
            
        # p75 (gorny kwartyl)
        if count >= 4:
            idx_p75 = int(count * 0.75)
            price_p75 = prices[idx_p75]
        else:
            price_p75 = price_max
            
        if count >= 10:
            market_sample_confidence = 1.0
        elif count >= 5:
            market_sample_confidence = 0.8
        elif count >= 3:
            market_sample_confidence = 0.6
        else:
            market_sample_confidence = 0.3
        conf_str = str(market_sample_confidence)
            
        # 1. UPSERT do comparable_groups
        cursor.execute("""
            INSERT OR IGNORE INTO comparable_groups
            (comparable_key, category_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (key, key.split("|", 1)[0] if "|" in key else "televisions", now, now))
        
        # Upsert do bazy
        cursor.execute("SELECT id FROM market_price_references WHERE comparable_key = ?", (key,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE market_price_references 
                SET min_price_pln = ?, 
                    avg_price_pln = ?, median_price_pln = ?,
                    p25_price_pln = ?, p75_price_pln = ?,
                    offers_count = ?, calculated_at = ?, confidence = ?
                WHERE comparable_key = ?
            """, (price_min, price_avg, price_median, price_p25, price_p75, count, now, conf_str, key))
        else:
            cursor.execute("""
                INSERT INTO market_price_references (
                    comparable_key, min_price_pln,
                    avg_price_pln, median_price_pln,
                    p25_price_pln, p75_price_pln,
                    offers_count, calculated_at, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (key, price_min, price_avg, price_median, price_p25, price_p75, count, now, conf_str))
            
    conn.commit()
