import logging
from scraper_ofert_tv.storage import (
    get_connection,
    create_search_run,
    update_search_run,
    create_search_profile_run,
    upsert_offer,
    create_offer_snapshot,
    now_iso
)
from scraper_ofert_tv.settings_service import SettingsService
from scraper_ofert_tv.olx_urls import build_olx_search_url
from scraper_ofert_tv.rate_limiter import RateLimiter
from scraper_ofert_tv.listing_scraper import ListingScraper
from scraper_ofert_tv.listing_parser import parse_listing
from scraper_ofert_tv.details_queue import add_to_queue

logger = logging.getLogger(__name__)

class Scanner:
    def __init__(self):
        self.settings = SettingsService()
        self.rate_limiter = RateLimiter(
            requests_per_minute=self.settings.get_rate_limit_settings().get("requests_per_minute", 30),
            delay_listings=self.settings.get_rate_limit_settings().get("delay_between_requests", 2)
        )
        self.scraper = ListingScraper(self.rate_limiter)
        
    def run_scan(self, mode: str, specific_profile: str = None):
        conn = get_connection()
        
        run_id = create_search_run(conn, mode)
        
        profiles = self.settings.get_size_profiles()
        if specific_profile:
            profiles = [p for p in profiles if p["id"] == specific_profile]
            
        global_filters = self.settings.get_global_filters()
        
        if mode == "national":
            mode_settings = self.settings.get_national_scan_settings()
            location = None
            radius = None
        else:
            mode_settings = self.settings.get_lodz_alerts_settings()
            location = mode_settings.get("location", "lodz")
            radius = mode_settings.get("radius_km", 50)
            
        max_pages = mode_settings.get("max_pages_per_profile", 25)
        
        total_new_offers = 0
        total_known_offers = 0
        
        for profile in profiles:
            if not profile.get("enabled"):
                continue
                
            profile_new, profile_known = self._scan_profile(
                conn=conn,
                run_id=run_id,
                mode=mode,
                profile=profile,
                global_filters=global_filters,
                location=location,
                radius_km=radius,
                max_pages=max_pages
            )
            
            total_new_offers += profile_new
            total_known_offers += profile_known
            
            if self.rate_limiter.is_run_limit_reached():
                logger.info("Osiagnieto globalny limit zapytan. Przerywam.")
                break
                
        update_search_run(
            conn, 
            run_id, 
            "success" if not self.rate_limiter.is_run_limit_reached() else "partial",
            offers_new=total_new_offers,
            offers_known=total_known_offers
        )
        conn.close()
        self.scraper.close()
        
    def _scan_profile(self, conn, run_id, mode, profile, global_filters, location, radius_km, max_pages):
        start_url = build_olx_search_url(
            mode=mode,
            location=location,
            radius_km=radius_km,
            price_min=global_filters.get("price_min"),
            price_max=global_filters.get("price_max"),
            seller_type=global_filters.get("seller_type"),
            condition=global_filters.get("condition"),
            size_filter=profile.get("olx_size_value"),
            page=1
        )
        
        profile_run_id = create_search_profile_run(conn, run_id, profile["id"], mode, start_url)
        
        current_url = start_url
        page_num = 1
        new_offers_count = 0
        known_offers_count = 0
        
        # Ochrona przed nieskonczona petla
        seen_urls_this_run = set()
        
        stop_reason = None
        status = "success"
        
        while page_num <= max_pages:
            html, error = self.scraper.fetch_listing(current_url)
            
            if error:
                if error == "captcha_detected" or error == "rate_limited":
                    stop_reason = "blocked"
                    status = "temporarily_blocked"
                elif error == "not_found":
                    stop_reason = "no_more_pages"
                else:
                    stop_reason = f"error_{error}"
                    status = "failed"
                break
                
            if not html:
                break
                
            offers, next_url = parse_listing(html, base_url="https://www.olx.pl")
            
            if not offers:
                stop_reason = "no_offers_on_page"
                break
                
            # Sprawdzenie czy utknelismy na tej samej stronie
            page_offer_urls = tuple(sorted([o['url'] for o in offers]))
            if page_offer_urls in seen_urls_this_run:
                stop_reason = "repeated_page"
                break
            seen_urls_this_run.add(page_offer_urls)
            
            page_new = 0
            
            for offer_data in offers:
                offer_data['olx_size_bucket'] = profile.get("olx_size_value")
                
                # Zapis do offers
                offer_id = upsert_offer(conn, offer_data)
                
                # Sprawdzenie czy oferta juz istniala (sprawdzamy czy powstal snapshot, lub mozemy policzyc z return value)
                # Dla uproszczenia (bo MVP), jesli oferta wchodzi pierwszy raz to jest "new", jesli juz tam byla, "known".
                # Storage.py robi upsert. Musimy odroznic INSERT od UPDATE.
                cursor = conn.cursor()
                cursor.execute("SELECT created_at, updated_at FROM offers WHERE id = ?", (offer_id,))
                row = cursor.fetchone()
                
                if row['created_at'] == row['updated_at']:
                    page_new += 1
                    new_offers_count += 1
                    # Dodaj do kolejki detali (nowa oferta)
                    add_to_queue(conn, offer_id, "new_offer", 100)
                else:
                    known_offers_count += 1
                    # Jesli zmienila sie cena, tu mozna dodac check i wrzucic na detale z "price_changed"
                
                # Zapis snapshotu
                snapshot_data = offer_data.copy()
                snapshot_data.pop('url_hash', None)
                snapshot_data.pop('olx_offer_id', None)
                snapshot_data.pop('is_free', None)
                snapshot_data.pop('raw_title', None)
                snapshot_data['offer_id'] = offer_id
                snapshot_data['search_run_id'] = run_id
                snapshot_data['search_profile_run_id'] = profile_run_id
                snapshot_data['scan_mode'] = mode
                snapshot_data['size_profile_id'] = profile["id"]
                snapshot_data['listing_page_url'] = current_url
                snapshot_data['listing_page_number'] = page_num
                
                snapshot_id = create_offer_snapshot(conn, snapshot_data)
                
            if next_url:
                current_url = next_url
                page_num += 1
            else:
                # Fallback jesli parser nie znajdzie linku
                page_num += 1
                current_url = build_olx_search_url(
                    mode=mode,
                    location=location,
                    radius_km=radius_km,
                    price_min=global_filters.get("price_min"),
                    price_max=global_filters.get("price_max"),
                    seller_type=global_filters.get("seller_type"),
                    condition=global_filters.get("condition"),
                    size_filter=profile.get("olx_size_value"),
                    page=page_num
                )
                
            # Zatrzymaj jesli np. wszystko znane (opcjonalny warunek z PRD)
            if page_new == 0 and page_num > 2:
                # Jesli 2 strony z rzedu sa puste (same stare), konczymy
                stop_reason = "all_offers_known"
                # W MVP nie musi przerywac, ale PRD mowi "brak nowych ofert jako warunek stopu"
                break
                
        if not stop_reason:
            stop_reason = "max_pages_reached"
            
        conn.execute(
            """UPDATE search_profile_runs 
               SET status = ?, pages_fetched = ?, offers_new = ?, offers_known = ?, finished_at = ?, stop_reason = ? 
               WHERE id = ?""",
            (status, min(page_num, max_pages), new_offers_count, known_offers_count, now_iso(), stop_reason, profile_run_id)
        )
        conn.commit()
        return new_offers_count, known_offers_count
