import sqlite3
import statistics
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
    # 2. system_status != 'rejected' (o ile to zostalo wczesniej zdefiniowane, jesli nie, po prostu exclude rejected)
    # 3. price_pln > 0
    # 4. posiadajace comparable_key
    cursor.execute("""
        SELECT comparable_key, price_pln 
        FROM offers 
        WHERE price_pln > 0 
          AND comparable_key IS NOT NULL 
          AND comparable_key != ''
          AND (system_status != 'rejected' OR system_status IS NULL)
          AND gone_at IS NULL
    """)
    rows = cursor.fetchall()
    
    # Grupowanie cen
    market_data = {}
    for row in rows:
        key = row['comparable_key']
        price = row['price_pln']
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
            
        # 1. UPSERT do comparable_groups (szukamy pierwszej oferty by wyciagnac metadane)
        cursor.execute("""
            SELECT brand, model, detected_size_inches, technology, resolution
            FROM offers
            WHERE comparable_key = ? LIMIT 1
        """, (key,))
        meta = cursor.fetchone()
        if meta:
            cursor.execute("""
                INSERT OR IGNORE INTO comparable_groups
                (comparable_key, brand, model, detected_size_inches, technology, resolution, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (key, meta['brand'], meta['model'], meta['detected_size_inches'], meta['technology'], meta['resolution'], now, now))
            
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
            """, (price_min, price_avg, price_median, price_p25, price_p75, count, now, 'high', key))
        else:
            cursor.execute("""
                INSERT INTO market_price_references (
                    comparable_key, min_price_pln,
                    avg_price_pln, median_price_pln,
                    p25_price_pln, p75_price_pln,
                    offers_count, calculated_at, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (key, price_min, price_avg, price_median, price_p25, price_p75, count, now, 'high'))
            
    conn.commit()
