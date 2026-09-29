import json
import sqlite3
from typing import Dict, Any, List
from scraper_ofert_tv.storage import now_iso

def process_alerts(conn: sqlite3.Connection):
    """
    Znajduje okazje blisko Lodzi z wysokim scorem i generuje alert_events.
    Dla uproszczenia (MVP) sprawdzamy wszystko, co ma system_status = 'opportunity' 
    lub potencjalnie bardzo wysoki score. Wymog z TASKS to:
    "Porownuj lokalne oferty z baza ogolnopolska. Stosuj progi score, rabatu, profitu i confidence."
    Oraz "Tlum powtorzone alerty przez skonfigurowany czas."
    """
    cursor = conn.cursor()
    
    # 1. Pobieramy ustawienia dla lodz_alerts
    # (MVP mock ustawien, bo ustawienia moga byc jeszcze nie w pelni ustandaryzowane w tabeli settings,
    #  choc zrobilismy to, wezmy je dla pewnosci jako hardcode z uzyciem settings_service lub po prostu defaults)
    
    # Definiujemy co uznajemy za lodz_alerts (miasto Lodz, okoliczne, lub w promieniu X km - jesli liczymy z distance_from_lodz_km).
    # MVP: po prostu city='Łódź' lub region='łódzkie' lub dystans z api. Zobaczmy czy w ofercie mamy dystans.
    # Uproszczenie MVP: wszystkie `opportunity`, u ktorych city='Łódź' lub distance_from_lodz_km <= 50
    
    cursor.execute("""
        SELECT o.id as offer_id, s.id as score_id, s.score, s.reference_price_pln, o.price_pln,
               s.estimated_profit_pln, s.market_discount_percent, s.comparison_confidence,
               s.comparable_offers_count, s.scoring_reasons_json
        FROM offers o
        JOIN offer_scores s ON s.offer_id = o.id
        WHERE o.system_status = 'opportunity'
          AND (o.city = 'Łódź' OR o.region = 'łódzkie' OR o.distance_from_lodz_km <= 50)
          AND o.gone_at IS NULL
    """)
    candidates = cursor.fetchall()
    
    now = now_iso()
    for cand in candidates:
        offer_id = cand['offer_id']
        
        # Sprawdz czy mamy juz aktywny alert, ktory nie jest stlumiony (suppressed_until > now)
        cursor.execute("SELECT id, suppressed_until FROM alert_events WHERE offer_id = ? ORDER BY id DESC LIMIT 1", (offer_id,))
        last_alert = cursor.fetchone()
        
        if last_alert:
            suppressed = last_alert['suppressed_until']
            if suppressed and suppressed > now:
                continue # Wciaz tlumimy ten alert
                
        cursor.execute("SELECT value_json FROM settings WHERE key = 'scoring_settings'")
        setting_row = cursor.fetchone()
        scoring_settings = json.loads(setting_row['value_json']) if setting_row else {}
        
        # Progi z ustawien (z domyslnymi fallbackami)
        min_conf = float(scoring_settings.get("min_confidence", 0.7))
        min_count = int(scoring_settings.get("min_count", 3))
        min_score = float(scoring_settings.get("min_score", 35.0))
        min_profit = float(scoring_settings.get("min_profit", 150))
        suppress_hours = int(scoring_settings.get("suppress_hours", 24))
        
        conf = float(cand['comparison_confidence'] or 0.0)
        count = cand['comparable_offers_count'] or 0
        score = cand['score'] or 0.0
        profit = cand['estimated_profit_pln'] or 0
        
        if conf >= min_conf and count >= min_count and score >= min_score and profit >= min_profit:
            # Tworzymy alert
            from datetime import datetime, timedelta, timezone
            suppress_time = (datetime.now(timezone.utc) + timedelta(hours=suppress_hours)).isoformat()
            
            reasons = json.loads(cand['scoring_reasons_json'] or "[]")
            reasons.append("lodz_alert_thresholds_met")
            
            cursor.execute("""
                INSERT INTO alert_events (
                    offer_id, alert_type, status, score, reference_price_pln,
                    offer_price_pln, estimated_profit_pln, market_discount_percent,
                    comparison_confidence, comparable_offers_count, reason_json,
                    first_created_at, last_triggered_at, suppressed_until
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                offer_id, 'lodz_opportunity', 'new', score, cand['reference_price_pln'],
                cand['price_pln'], profit, cand['market_discount_percent'],
                str(conf), count, json.dumps(reasons),
                now, now, suppress_time
            ))
            
    conn.commit()
