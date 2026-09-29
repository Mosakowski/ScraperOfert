import logging
from scraper_ofert_tv.storage import get_connection, now_iso
from scraper_ofert_tv.details_queue import get_pending_tasks, mark_task_processing, mark_task_done, mark_task_failed
from scraper_ofert_tv.detail_scraper import DetailScraper
from scraper_ofert_tv.detail_parser import parse_detail
from scraper_ofert_tv.normalization import normalize_offer_data
from scraper_ofert_tv.comparison import generate_comparable_key, calculate_confidence
from scraper_ofert_tv.rules import evaluate_rules
import json

logger = logging.getLogger(__name__)

class DetailWorker:
    def __init__(self):
        self.scraper = DetailScraper()
        
    def work(self, limit: int = 10):
        conn = get_connection()
        tasks = get_pending_tasks(conn, limit)
        
        for task in tasks:
            if self.scraper.rate_limiter.is_details_limit_reached():
                logger.info("Limit zapytan o detale osiagniety.")
                break
                
            task_id = task['id']
            offer_id = task['offer_id']
            
            mark_task_processing(conn, task_id)
            
            # 1. Pobieramy URL oferty
            cursor = conn.cursor()
            cursor.execute("SELECT url, raw_price, is_free, negotiable, olx_size_bucket, raw_location, price_pln FROM offers WHERE id = ?", (offer_id,))
            offer = cursor.fetchone()
            
            if not offer:
                mark_task_failed(conn, task_id, "offer_not_found_in_db")
                continue
                
            url = offer['url']
            
            # 2. Pobieramy HTML
            html, err = self.scraper.fetch_detail(url)
            
            if err:
                if err == "not_found" or err == "gone":
                    # Ogloszenie juz usuniete. 
                    # Zapisujemy to, i oznaczamy task jako done, bo to stan koncowy
                    conn.execute("UPDATE offers SET gone_at = ?, updated_at = ? WHERE id = ?", (now_iso(), now_iso(), offer_id))
                    conn.commit()
                    mark_task_done(conn, task_id)
                elif err in ["captcha_detected", "rate_limited"]:
                    # Powinnismy sprobowac jeszcze raz, z wiekszym opoznieniem (TODO: backoff details)
                    mark_task_failed(conn, task_id, err)
                    break # Wstrzymujemy procesowanie bo dostalismy bana
                else:
                    mark_task_failed(conn, task_id, err)
                continue
                
            if not html:
                mark_task_failed(conn, task_id, "empty_html")
                continue
                
            # 3. Parsujemy HTML
            detail = parse_detail(html)
            
            # Aktualizacja statusu
            if detail['status'] == 'inactive':
                conn.execute("UPDATE offers SET gone_at = ?, updated_at = ? WHERE id = ?", (now_iso(), now_iso(), offer_id))
            
            # 4. Normalizujemy dane
            normalized = normalize_offer_data(dict(offer), detail)
            
            # 5. Tworzymy klucz i confidence
            comp_key = generate_comparable_key(normalized)
            confidence = calculate_confidence(normalized, comp_key)
            
            # 6. Reguly opisowe
            matched_rules, actions = evaluate_rules(conn, normalized, detail)
            system_status = None
            if "reject" in actions:
                system_status = "rejected"
            elif confidence < 0.3: # Jesli strasznie slabo znormalizowane, to weak match
                system_status = "weak_match"
                
            # Zapis znormalizowanych danych i detali
            now = now_iso()
            # Update offers
            conn.execute("""
                UPDATE offers 
                SET seller_name = ?, seller_profile_url = ?,
                    brand = ?, model = ?, technology = ?, resolution = ?, detected_size_inches = ?,
                    city = ?, district = ?, comparable_key = ?, comparison_confidence = ?, 
                    system_status = COALESCE(?, system_status), updated_at = ?, last_detail_fetch_at = ?
                WHERE id = ?
            """, (
                detail.get('seller_name'), detail.get('seller_url'),
                normalized.get('brand'), normalized.get('model_name'), normalized.get('technology'), 
                normalized.get('resolution'), normalized.get('size_inches'),
                normalized.get('city'), normalized.get('district'),
                comp_key, str(confidence), system_status, now, now, offer_id
            ))
            
            # Create snapshot for descriptive info
            conn.execute("""
                INSERT INTO offer_snapshots
                (offer_id, scan_mode, title, description, params_json, photo_count, main_photo_url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                offer_id, "detail_fetch", detail.get('full_title'), detail.get('description'),
                json.dumps(detail.get('params', {})), detail.get('images_count'),
                detail.get('main_image_url'), now
            ))
            
            # Zapisz dopasowane reguly
            if matched_rules:
                for r in matched_rules:
                    conn.execute("""
                        INSERT INTO rule_matches 
                        (offer_id, rule_id, category, severity, action, score_delta, matched_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (offer_id, r['rule_id'], r['category'], r['severity'], r['action'], r['score_delta'], now))
                                 
            conn.commit()
            
            mark_task_done(conn, task_id)
            
        conn.close()
        self.scraper.close()
