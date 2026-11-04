import httpx
import logging
import json
import os
import time
from bs4 import BeautifulSoup
from scraper_ofert_tv.olx_urls import build_olx_search_url
from scraper_ofert_tv.settings_service import SettingsService

logger = logging.getLogger(__name__)

def diagnose_olx(profile_id: str, backend: str = "httpx"):
    print(f"=== ROZPOCZYNAM DIAGNOSTYKE OLX DLA PROFILU {profile_id} (Backend: {backend}) ===")
    
    settings = SettingsService()
    profiles = settings.get_size_profiles()
    profile = next((p for p in profiles if p["id"] == profile_id), None)
    if not profile:
        print(f"Blad: Nie znaleziono profilu {profile_id}")
        return
        
    size_filter = profile.get("olx_size_value")
    
    scenarios = [
        {
            "name": "Kategoria TV bez filtrow",
            "url": build_olx_search_url("national", price_min=None, price_max=None, condition=None, seller_type=None, size_filter=None)
        },
        {
            "name": "Kategoria + rozmiar",
            "url": build_olx_search_url("national", price_min=None, price_max=None, condition=None, seller_type=None, size_filter=size_filter)
        },
        {
            "name": "Kategoria + rozmiar + cena",
            "url": build_olx_search_url("national", price_min=300, price_max=700, condition=None, seller_type=None, size_filter=size_filter)
        },
        {
            "name": "Kategoria + rozmiar + cena + used/private",
            "url": build_olx_search_url("national", price_min=300, price_max=700, condition="used", seller_type="private", size_filter=size_filter)
        },
        {
            "name": "Lodz + pelne filtry",
            "url": build_olx_search_url("lodz_alerts", location="lodz", radius_km=50, price_min=300, price_max=700, condition="used", seller_type="private", size_filter=size_filter)
        }
    ]
    
    if backend == "playwright":
        from scraper_ofert_tv.browser_scraper import BrowserScraper
        scraper = BrowserScraper()
    else:
        from scraper_ofert_tv.listing_scraper import ListingScraper
        scraper = ListingScraper()
    
    for idx, scenario in enumerate(scenarios):
        print(f"\n--- Scenariusz {idx+1}: {scenario['name']} ---")
        url = scenario['url']
        print(f"URL: {url}")
        
        try:
            html, error, diag_info = scraper.fetch_listing(url)
            
            if diag_info:
                status = diag_info.get("status_code", 0)
                print(f"Status: {status}")
                
                has_set_cookie = "set-cookie" in diag_info.get("response_headers", {})
                print(f"Set-Cookie header present: {has_set_cookie}")
                
                body = diag_info.get("body", "")
                body_lower = body.lower()
                
                keywords = ["datadome", "captcha", "forbidden", "access denied", "blocked"]
                found_keywords = [kw for kw in keywords if kw in body_lower]
                print(f"Body contains keywords: {found_keywords if found_keywords else 'None'}")
                
                print(f"HTML size: {len(body)} bytes")
                
                soup = BeautifulSoup(body, "html.parser")
                oferta_links = soup.select('a[href*="/d/oferta/"]')
                print(f"Body contains /d/oferta/ links: {len(oferta_links)} found")
                l_card_count = len(soup.select('div[data-cy="l-card"]'))
                print(f"Data-cy l-card count: {l_card_count}")
                
                if status != 200 or error:
                    os.makedirs("debug/listings", exist_ok=True)
                    timestamp = int(time.time())
                    base_filename = f"debug/listings/error_diagnose_{profile_id}_{idx}_{timestamp}"
                    
                    with open(f"{base_filename}.html", "w", encoding="utf-8") as f:
                        f.write(body)
                        
                    meta_json = {
                        "url": diag_info.get("url"),
                        "status_code": status,
                        "request_headers": diag_info.get("request_headers"),
                        "response_headers": diag_info.get("response_headers"),
                        "error_reason": error
                    }
                    with open(f"{base_filename}.json", "w", encoding="utf-8") as f:
                        json.dump(meta_json, f, indent=2)
                    print(f"Saved diagnostic files: {base_filename}.html / .json")
                    
        except Exception as e:
            print(f"Request failed with exception: {e}")
            
    scraper.close()
    print("\n=== KONIEC DIAGNOSTYKI ===")
