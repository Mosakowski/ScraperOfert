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
import os
import json

logger = logging.getLogger(__name__)

class Scanner:
    def __init__(self):
        self.settings = SettingsService()
        self.rate_limiter = RateLimiter(
            requests_per_minute=self.settings.get_rate_limit_settings().get("requests_per_minute", 30),
            delay_listings=self.settings.get_rate_limit_settings().get("delay_between_requests", 2)
        )
        scraper_settings = self.settings.get_scraper_settings()
        if scraper_settings.get("fetch_backend") == "playwright":
            from scraper_ofert_tv.browser_scraper import BrowserScraper
            self.scraper = BrowserScraper(self.rate_limiter)
        else:
            self.scraper = ListingScraper(self.rate_limiter)
        
    def run_scan(self, mode: str, specific_profile: str = None):
        conn = get_connection()
        
        run_id = create_search_run(conn, mode)
        
        profiles = self.settings.get_search_profiles(enabled_only=True)
        if specific_profile:
            profiles = [p for p in profiles if p["id"] == specific_profile]
            
        global_filters = self.settings.get_global_filters()
        
        total_new_offers = 0
        total_known_offers = 0
        total_seen_offers = 0
        profile_results = []
        
        for profile in profiles:
            profile_filters = profile.get("filters") or {}
            profile_mode = profile_filters.get("mode", mode)
            if profile_mode == "national":
                mode_settings = self.settings.get_national_scan_settings()
                location = None
                radius = None
            else:
                mode_settings = self.settings.get_lodz_alerts_settings()
                location = profile_filters.get("location") or mode_settings.get("location", "lodz")
                radius = int(profile_filters.get("radius_km") or mode_settings.get("radius_km", 50))
            mode_max_pages = int(mode_settings.get("max_pages_per_profile", 25))
            profile_max_pages = min(int(profile.get("max_pages") or mode_max_pages), mode_max_pages)
            profile_result = self._scan_profile(
                conn=conn,
                run_id=run_id,
                mode=profile_mode,
                profile=profile,
                global_filters=global_filters,
                location=location,
                radius_km=radius,
                max_pages=profile_max_pages
            )
            
            profile_results.append(profile_result)
            total_new_offers += profile_result["offers_new"]
            total_known_offers += profile_result["offers_known"]
            total_seen_offers += profile_result["offers_seen"]
            
            if self.rate_limiter.is_run_limit_reached():
                logger.info("Osiagnieto globalny limit zapytan. Przerywam.")
                break

        if self.rate_limiter.is_run_limit_reached():
            run_status = "partial"
            run_stop_reason = "run_limit_reached"
        elif profile_results and all(r["status"] in ("failed", "temporarily_blocked") for r in profile_results):
            run_status = "failed"
            reasons = sorted({r["stop_reason"] for r in profile_results if r["stop_reason"]})
            run_stop_reason = ";".join(reasons) if reasons else "all_profiles_failed"
        elif any(r["status"] in ("failed", "temporarily_blocked") for r in profile_results):
            run_status = "partial"
            reasons = sorted({r["stop_reason"] for r in profile_results if r["status"] in ("failed", "temporarily_blocked") and r["stop_reason"]})
            run_stop_reason = ";".join(reasons) if reasons else "some_profiles_failed"
        elif not profile_results:
            run_status = "skipped"
            run_stop_reason = "no_enabled_profiles"
        else:
            run_status = "success"
            reasons = sorted({r["stop_reason"] for r in profile_results if r["stop_reason"]})
            run_stop_reason = ";".join(reasons) if reasons else None
                
        update_search_run(
            conn, 
            run_id, 
            run_status,
            profiles_total=len([p for p in profiles if p.get("enabled")]),
            profiles_done=len(profile_results),
            offers_seen=total_seen_offers,
            offers_new=total_new_offers,
            offers_known=total_known_offers,
            stop_reason=run_stop_reason
        )
        conn.close()
        self.scraper.close()
        
    def _scan_profile(self, conn, run_id, mode, profile, global_filters, location, radius_km, max_pages):
        profile_filters = profile.get("filters") or {}
        profile_price_min = profile_filters.get("price_min")
        profile_price_max = profile_filters.get("price_max")
        if profile_price_min is None:
            profile_price_min = global_filters.get("price_min")
        if profile_price_max is None:
            profile_price_max = global_filters.get("price_max")
        olx_filters = profile_filters.get("olx_filters") or {}
        start_url = build_olx_search_url(
            mode=mode,
            location=location,
            radius_km=radius_km,
            price_min=profile_price_min,
            price_max=profile_price_max,
            seller_type=profile_filters.get("seller_type", global_filters.get("seller_type")),
            condition=profile_filters.get("condition", global_filters.get("condition")),
            page=1,
            category_path=profile.get("category_path"),
            olx_filters=olx_filters,
            query=profile_filters.get("query")
        )
        
        legacy_profile_id = profile.get("legacy_size_profile_id") or "laptops_all"
        profile_run_id = create_search_profile_run(
            conn, run_id, legacy_profile_id, mode, start_url, search_profile_id=profile["id"]
        )
        
        current_url = start_url
        page_num = 1
        new_offers_count = 0
        known_offers_count = 0
        seen_offers_count = 0
        
        # Ochrona przed nieskonczona petla
        seen_urls_this_run = set()
        
        stop_reason = None
        status = "success"
        all_warnings = []
        
        while page_num <= max_pages:
            html, error, diag_info = self.scraper.fetch_listing(current_url)
            
            if error:
                if diag_info:
                    os.makedirs("debug/listings", exist_ok=True)
                    base_filename = f"debug/listings/error_{run_id}_{profile['id']}_{page_num}"
                    
                    # Save HTML
                    with open(f"{base_filename}.html", "w", encoding="utf-8") as f:
                        f.write(diag_info.get("body", ""))
                        
                    # Save JSON metadata
                    json_data = {
                        "url": diag_info.get("url"),
                        "status_code": diag_info.get("status_code"),
                        "request_headers": diag_info.get("request_headers"),
                        "response_headers": diag_info.get("response_headers"),
                        "error_reason": error
                    }
                    with open(f"{base_filename}.json", "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=2)

                if error in ("captcha_detected", "rate_limited", "forbidden_403"):
                    stop_reason = "blocked_403" if error == "forbidden_403" else "blocked"
                    status = "temporarily_blocked"
                elif error == "not_found":
                    stop_reason = "no_more_pages"
                else:
                    stop_reason = f"error_{error}"
                    status = "failed"
                break
                
            if not html:
                break
                
            offers, next_url, warnings = parse_listing(html, base_url="https://www.olx.pl")
            if warnings:
                all_warnings.extend(warnings)
            seen_offers_count += len(offers)
            
            if not offers:
                if seen_offers_count > 0:
                    stop_reason = "no_more_offers_on_next_page"
                else:
                    stop_reason = "no_offers_on_page"
                # Diagnostic mode
                os.makedirs("debug/listings", exist_ok=True)
                diag_filename = f"debug/listings/run_{profile_run_id}_page_{page_num}.html"
                with open(diag_filename, "w", encoding="utf-8") as f:
                    f.write(html)
                diag_info = {
                    "url": current_url,
                    "profile_id": profile["id"],
                    "mode": mode,
                    "page": page_num,
                    "warnings": warnings
                }
                with open(diag_filename.replace(".html", ".json"), "w", encoding="utf-8") as f:
                    json.dump(diag_info, f, indent=2)
                break
                
            # Sprawdzenie czy utknelismy na tej samej stronie
            page_offer_urls = tuple(sorted([o['url'] for o in offers]))
            if page_offer_urls in seen_urls_this_run:
                stop_reason = "repeated_page"
                break
            seen_urls_this_run.add(page_offer_urls)
            
            page_new = 0
            
            for offer_data in offers:
                offer_data['olx_size_bucket'] = olx_filters.get("search[filter_enum_size][0]")
                offer_data['category_id'] = profile["category_id"]
                offer_data['attributes_json'] = "{}"
                
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
                    priority = 300 if mode == "lodz_alerts" else 100
                    add_to_queue(conn, offer_id, "new_offer", priority)
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
                snapshot_data['size_profile_id'] = legacy_profile_id
                snapshot_data['category_id'] = profile["category_id"]
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
                    price_min=profile_price_min,
                    price_max=profile_price_max,
                    seller_type=profile_filters.get("seller_type", global_filters.get("seller_type")),
                    condition=profile_filters.get("condition", global_filters.get("condition")),
                    page=page_num,
                    category_path=profile.get("category_path"),
                    olx_filters=olx_filters,
                    query=profile_filters.get("query")
                )
                
            # Zatrzymaj jesli np. wszystko znane (opcjonalny warunek z PRD)
            if page_new == 0 and page_num > 2:
                # Jesli 2 strony z rzedu sa puste (same stare), konczymy
                stop_reason = "all_offers_known"
                # W MVP nie musi przerywac, ale PRD mowi "brak nowych ofert jako warunek stopu"
                break
                
        if not stop_reason:
            stop_reason = "max_pages_reached"
            
        warnings_json = json.dumps(all_warnings) if all_warnings else None
            
        conn.execute(
            """UPDATE search_profile_runs 
               SET status = ?, pages_fetched = ?, offers_new = ?, offers_known = ?, finished_at = ?, stop_reason = ?, parser_warnings_json = ?
               WHERE id = ?""",
            (status, min(page_num, max_pages), new_offers_count, known_offers_count, now_iso(), stop_reason, warnings_json, profile_run_id)
        )
        conn.commit()
        conn.execute(
            "UPDATE search_profile_runs SET offers_seen = ? WHERE id = ?",
            (seen_offers_count, profile_run_id)
        )
        conn.commit()
        return {
            "status": status,
            "stop_reason": stop_reason,
            "offers_seen": seen_offers_count,
            "offers_new": new_offers_count,
            "offers_known": known_offers_count,
        }
