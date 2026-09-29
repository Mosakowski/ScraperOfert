import httpx
import logging
from typing import Tuple, Optional
from scraper_ofert_tv.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class DetailScraper:
    def __init__(self, rate_limiter: RateLimiter = None):
        self.client = httpx.Client(
            timeout=15.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            }
        )
        self.rate_limiter = rate_limiter or RateLimiter()

    def fetch_detail(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        if self.rate_limiter.is_details_limit_reached():
            return None, "detail_limit_reached"

        self.rate_limiter.wait_backoff()
        self.rate_limiter.wait_for_detail()

        try:
            response = self.client.get(url)
            
            if response.status_code == 200:
                html = response.text
                if "datadome" in html.lower() or "captcha" in html.lower() or "akces zablokowany" in html.lower():
                    self.rate_limiter.record_error()
                    return None, "captcha_detected"
                self.rate_limiter.clear_errors()
                return html, None
                
            elif response.status_code == 404:
                # Ogloszenie usuniete
                return None, "not_found"
            
            elif response.status_code == 429:
                self.rate_limiter.record_error()
                return None, "rate_limited"
                
            elif response.status_code == 410:
                return None, "gone"
                
            elif response.status_code >= 500:
                self.rate_limiter.record_error()
                return None, f"server_error_{response.status_code}"
                
            else:
                self.rate_limiter.record_error()
                return None, f"unexpected_status_{response.status_code}"
                
        except httpx.RequestError as e:
            self.rate_limiter.record_error()
            logger.error(f"Request error for {url}: {e}")
            return None, "network_error"
            
    def close(self):
        self.client.close()
