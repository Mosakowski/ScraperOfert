from typing import Tuple, Optional
import logging
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from scraper_ofert_tv.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class BrowserScraper:
    def __init__(self, rate_limiter: RateLimiter = None):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.playwright = sync_playwright().start()
        # Otwieramy przegladarke bez zbednych bajerow
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pl-PL",
            viewport={"width": 1920, "height": 1080}
        )

    def fetch_listing(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[dict]]:
        """
        Pobiera HTML z URL za pomoca przegladarki.
        Zwraca: (HTML jako string lub None, string z bledem/powodem zablokowania lub None, dict z info diagnostycznym)
        """
        if self.rate_limiter.is_run_limit_reached():
            return None, "run_limit_reached", None

        self.rate_limiter.wait_backoff()
        self.rate_limiter.wait_for_listing()

        page = self.context.new_page()
        
        diag_info = {
            "url": url,
            "status_code": 0,
            "request_headers": {},
            "response_headers": {},
            "body": ""
        }

        try:
            # Rejestrujemy status kodu z odpowiedzi glownego dokumentu
            status_code = [200]
            def handle_response(response):
                if response.url == url:
                    status_code[0] = response.status
                    diag_info["response_headers"] = response.headers
            
            page.on("response", handle_response)
            
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if response:
                status = response.status
                diag_info["status_code"] = status
                diag_info["request_headers"] = response.request.headers
            else:
                status = status_code[0]
                diag_info["status_code"] = status
            
            html = page.content()
            diag_info["body"] = html
            
            html_lower = html.lower()
            
            if status in (403, 401) or "forbidden" in html_lower or "access denied" in html_lower:
                self.rate_limiter.record_error()
                page.close()
                return None, "forbidden_403", diag_info
                
            if status != 200 and ("datadome" in html_lower or "captcha" in html_lower or "akces zablokowany" in html_lower):
                self.rate_limiter.record_error()
                page.close()
                return None, "captcha_detected", diag_info
                
            if status == 404:
                page.close()
                return None, "not_found", diag_info
                
            if status == 429:
                self.rate_limiter.record_error()
                page.close()
                return None, "rate_limited", diag_info
                
            if status >= 500:
                self.rate_limiter.record_error()
                page.close()
                return None, f"server_error_{status}", diag_info
                
            # Neutralne klikniecie consent popup (ONET_CMP) jesli przyslania, aczkolwiek dla samego HTML moze to nie byc konieczne
            try:
                if page.locator("button#onetrust-accept-btn-handler").is_visible(timeout=1000):
                    page.locator("button#onetrust-accept-btn-handler").click()
                    page.wait_for_timeout(1000)
            except Exception:
                pass
                
            # Pobieramy ostateczny HTML
            html = page.content()
            diag_info["body"] = html
            
            self.rate_limiter.clear_errors()
            page.close()
            return html, None, diag_info

        except PlaywrightTimeoutError:
            self.rate_limiter.record_error()
            logger.error(f"Playwright timeout for {url}")
            page.close()
            return None, "timeout_error", diag_info
        except Exception as e:
            self.rate_limiter.record_error()
            logger.error(f"Playwright error for {url}: {e}")
            page.close()
            return None, "browser_error", diag_info

    def fetch_detail(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[dict]]:
        """
        Pobiera HTML strony detali za pomoca przegladarki.
        Zwraca: (HTML jako string lub None, string z bledem/powodem zablokowania lub None, dict z info diagnostycznym)
        """
        if self.rate_limiter.is_details_limit_reached():
            return None, "detail_limit_reached", None

        self.rate_limiter.wait_backoff()
        self.rate_limiter.wait_for_detail()

        page = self.context.new_page()
        
        diag_info = {
            "url": url,
            "status_code": 0,
            "request_headers": {},
            "response_headers": {},
            "body": ""
        }

        try:
            status_code = [200]
            def handle_response(response):
                if response.url == url:
                    status_code[0] = response.status
                    diag_info["response_headers"] = response.headers
            
            page.on("response", handle_response)
            
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if response:
                status = response.status
                diag_info["status_code"] = status
                diag_info["request_headers"] = response.request.headers
            else:
                status = status_code[0]
                diag_info["status_code"] = status
            
            html = page.content()
            diag_info["body"] = html
            html_lower = html.lower()
            
            if status in (403, 401) or "forbidden" in html_lower or "access denied" in html_lower:
                self.rate_limiter.record_error()
                page.close()
                return None, "forbidden_403", diag_info
                
            if status != 200 and ("datadome" in html_lower or "captcha" in html_lower or "akces zablokowany" in html_lower):
                self.rate_limiter.record_error()
                page.close()
                return None, "captcha_detected", diag_info
                
            if status == 404:
                page.close()
                return None, "not_found", diag_info
                
            if status == 410:
                page.close()
                return None, "gone", diag_info
                
            if status == 429:
                self.rate_limiter.record_error()
                page.close()
                return None, "rate_limited", diag_info
                
            if status >= 500:
                self.rate_limiter.record_error()
                page.close()
                return None, f"server_error_{status}", diag_info
                
            try:
                if page.locator("button#onetrust-accept-btn-handler").is_visible(timeout=1000):
                    page.locator("button#onetrust-accept-btn-handler").click()
                    page.wait_for_timeout(1000)
            except Exception:
                pass
                
            # Nie klikamy numeru telefonu/emaila bo nie chcemy pobierac danych kontaktowych (zgodnie ze specyfikacja).
                
            html = page.content()
            diag_info["body"] = html
            
            self.rate_limiter.clear_errors()
            page.close()
            return html, None, diag_info

        except PlaywrightTimeoutError:
            self.rate_limiter.record_error()
            logger.error(f"Playwright timeout for details {url}")
            page.close()
            return None, "timeout_error", diag_info
        except Exception as e:
            self.rate_limiter.record_error()
            logger.error(f"Playwright error for details {url}: {e}")
            page.close()
            return None, "browser_error", diag_info

    def close(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()
