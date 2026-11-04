import json
import sqlite3
from typing import Dict, Any, List, Optional
from scraper_ofert_tv.storage import now_iso

def score_offers(conn: sqlite3.Connection):
    """
    Wylicza score dla ofert "new" ktore maja juz detal i przeprowadzona normalizacje (comparable_key is not null),
    oraz dopasowane ceny rynkowe (market_price_references).
    """
    cursor = conn.cursor()
    
    # Bierzemy nowo pobrane lub niescorowane w pelni oferty (system_status == 'new' lub 'weak_match', jesli maja pelne detale)
    # W MVP powiedzmy po prostu: oceniamy wszystko, czego score jeszcze nie zapisano dla najswiezszego reference.
    # Uproszczenie MVP: iteruj po ofertach bez przypisanego score dzisiaj.
    
    cursor.execute("""
        SELECT o.* 
        FROM offers o
        WHERE o.system_status IN ('new', 'weak_match')
          AND o.gone_at IS NULL
          AND o.price_pln > 0
    """)
    offers = cursor.fetchall()
    
    now = now_iso()
    for offer in offers:
        offer_id = offer['id']
        price = offer['price_pln']
        sys_status = offer['system_status']
        
        from scraper_ofert_tv.comparison import generate_comparable_keys, get_strategy_cap, calculate_normalization_confidence
        normalized = {
            'brand': offer['brand'],
            'model_name': offer['model'],
            'technology': offer['technology'],
            'resolution': offer['resolution'],
            'size_inches': offer['detected_size_inches'],
            'native_olx_bucket': offer['olx_size_bucket']
        }
        keys = generate_comparable_keys(normalized)
        
        cursor.execute("SELECT value_json FROM settings WHERE key = 'scoring_settings'")
        setting_row = cursor.fetchone()
        scoring_settings = json.loads(setting_row['value_json']) if setting_row else {}
        min_count = int(scoring_settings.get("min_count", 3))
        
        best_market = None
        best_strategy = None
        
        for strategy in ['A', 'B', 'C', 'D']:
            key = keys.get(strategy)
            if not key: continue
            cursor.execute("SELECT id as market_id, median_price_pln, offers_count, confidence as market_confidence FROM market_price_references WHERE comparable_key = ?", (key,))
            market = cursor.fetchone()
            # Dla strategii A (exact model) również wymagamy min_count
            required_count = min_count
            
            if market and market['offers_count'] >= required_count:
                best_market = market
                best_strategy = strategy
                break
                
        # 1. Sprawdz reguly odrzucajace
        cursor.execute("SELECT * FROM rule_matches WHERE offer_id = ? AND action = 'reject'", (offer_id,))
        rejects = cursor.fetchall()
        if rejects:
            _save_score(conn, offer_id, best_market['market_id'] if best_market else None, 0, "rejected", 
                        best_market['median_price_pln'] if best_market else None, now, reasons=["rule_reject"])
            continue
            
        if not best_market:
            # Nie mamy rynku albo zbyt mala proba
            _save_score(conn, offer_id, None, 0, sys_status, None, now, reasons=["no_market"])
            continue
            
        median_price = best_market['median_price_pln']
        offers_count = best_market['offers_count']
        market_id = best_market['market_id']
        market_sample_confidence = float(best_market['market_confidence']) if best_market else 0.0
        
        strategy_cap = get_strategy_cap(best_strategy) if best_strategy else 0.4
        norm_conf = calculate_normalization_confidence(normalized)
        
        final_comparison_confidence = min(market_sample_confidence, strategy_cap, norm_conf)
        
        # 2. Obliczanie znizek/profitu
        market_discount_percent = ((median_price - price) / median_price) * 100.0 if median_price > 0 else 0
        expected_resale = median_price
        
        # Koszty np. transport, paliwo
        estimated_costs = int(scoring_settings.get("estimated_costs", 50)) 
        
        estimated_profit = expected_resale - price - estimated_costs
        
        # 3. Wyliczenie score (0-100)
        # Podstawą jest procent rabatu, maks. 50 pkt za rabat > 50%
        score = min(50.0, max(0.0, market_discount_percent))
        
        # 4. Modifikatory
        # Za confidence - jesli ponizej 0.5 to duzy spadek
        score = score * (final_comparison_confidence + 0.2)
        
        # Reguly modyfikujace (np flagi z negatywnym delta)
        cursor.execute("SELECT score_delta FROM rule_matches WHERE offer_id = ? AND action = 'flag'", (offer_id,))
        flags = cursor.fetchall()
        for f in flags:
            score += f['score_delta']
            
        score = max(0.0, min(100.0, score))
        
        # 5. Aktualizacja statusu
        min_discount = float(scoring_settings.get("min_discount", 15.0))
        min_profit = float(scoring_settings.get("min_profit", 100))
        min_score = float(scoring_settings.get("min_score", 30.0))
        # confidence threshold and min_count were checked above via offers_count
        
        if sys_status == 'weak_match':
            # weak_match pozostaje weak_match
            final_status = 'weak_match'
        else:
            if score >= min_score and market_discount_percent >= min_discount and estimated_profit >= min_profit:
                final_status = 'opportunity'
            else:
                final_status = 'active'
                
        reasons = [
            f"discount={market_discount_percent:.1f}%", 
            f"profit={estimated_profit}", 
            f"strategy={best_strategy}",
            f"strategy_cap={strategy_cap}",
            f"norm_conf={norm_conf}",
            f"market_conf={market_sample_confidence}"
        ]
        
        # Zaktualizuj klucz comparable_key w offers by odzwierciedlał wybrany rynek
        conn.execute("UPDATE offers SET comparable_key = ? WHERE id = ?", (keys.get(best_strategy), offer_id))
        
        _save_score(conn, offer_id, market_id, score, final_status, median_price, now, reasons,
                   expected_resale, estimated_costs, estimated_profit, market_discount_percent,
                   offers_count, str(final_comparison_confidence))
                   
    conn.commit()

def _save_score(conn, offer_id, market_id, score, status, ref_price, now, reasons,
                expected_resale=None, estimated_costs=None, estimated_profit=None,
                discount_pct=None, comp_count=None, conf_str=None):
    
    # Najpierw update w tabeli offers
    conn.execute("UPDATE offers SET system_status = ?, updated_at = ? WHERE id = ?", (status, now, offer_id))
    
    # Log w offer_scores
    conn.execute("""
        INSERT INTO offer_scores (
            offer_id, market_reference_id, score, system_status,
            reference_price_pln, expected_resale_price_pln, estimated_costs_pln,
            estimated_profit_pln, market_discount_percent, comparable_offers_count,
            comparison_confidence, scoring_reasons_json, calculated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        offer_id, market_id, score, status,
        ref_price, expected_resale, estimated_costs,
        estimated_profit, discount_pct, comp_count,
        conf_str, json.dumps(reasons), now
    ))
