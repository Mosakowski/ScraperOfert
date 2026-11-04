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

    def fetch_detail(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[dict]]:
        if self.rate_limiter.is_details_limit_reached():
            return None, "detail_limit_reached", None

        self.rate_limiter.wait_backoff()
        self.rate_limiter.wait_for_detail()

        try:
            response = self.client.get(url)
            diag_info = {
                "url": str(response.url),
                "status_code": response.status_code,
                "request_headers": dict(response.request.headers),
                "response_headers": dict(response.headers),
                "body": response.text
            }
            
            if response.status_code == 200:
                html = response.text
                self.rate_limiter.clear_errors()
                return html, None, diag_info
                
            elif response.status_code == 404:
                # Ogloszenie usuniete
                return None, "not_found", diag_info
            
            elif response.status_code == 429:
                self.rate_limiter.record_error()
                return None, "rate_limited", diag_info
                
            elif response.status_code == 410:
                return None, "gone", diag_info
                
            elif response.status_code >= 500:
                self.rate_limiter.record_error()
                return None, f"server_error_{response.status_code}", diag_info
                
            else:
                self.rate_limiter.record_error()
                return None, f"unexpected_status_{response.status_code}", diag_info
                
        except httpx.RequestError as e:
            self.rate_limiter.record_error()
            logger.error(f"Request error for {url}: {e}")
            return None, "network_error", None
            
    def close(self):
        self.client.close()
