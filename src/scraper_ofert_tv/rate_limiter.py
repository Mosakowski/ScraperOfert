import time
import random

class RateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 30,
        delay_listings: float = 2.0,
        delay_details: float = 3.0,
        jitter_factor: float = 0.5,
        max_requests_per_run: int = 500,
        max_details_per_run: int = 200
    ):
        self.requests_per_minute = requests_per_minute
        self.delay_listings = delay_listings
        self.delay_details = delay_details
        self.jitter_factor = jitter_factor
        
        self.max_requests_per_run = max_requests_per_run
        self.max_details_per_run = max_details_per_run
        
        self.requests_this_run = 0
        self.details_this_run = 0
        
        self.consecutive_errors = 0
        
    def _sleep_with_jitter(self, base_delay: float):
        jitter = base_delay * self.jitter_factor
        actual_delay = base_delay + random.uniform(-jitter, jitter)
        actual_delay = max(0.1, actual_delay)  # Nie schodzimy ponizej 0.1s
        time.sleep(actual_delay)
        
    def wait_for_listing(self):
        self.requests_this_run += 1
        self._sleep_with_jitter(self.delay_listings)
        
    def wait_for_detail(self):
        self.requests_this_run += 1
        self.details_this_run += 1
        self._sleep_with_jitter(self.delay_details)
        
    def record_error(self):
        self.consecutive_errors += 1
        
    def clear_errors(self):
        self.consecutive_errors = 0
        
    def get_backoff_time(self) -> float:
        """Zwraca czas opoznienia po bledach."""
        if self.consecutive_errors == 0:
            return 0.0
        # Wykladnicze wydluzanie np. 2, 4, 8...
        return min(60.0, 2 ** self.consecutive_errors)
        
    def wait_backoff(self):
        backoff = self.get_backoff_time()
        if backoff > 0:
            time.sleep(backoff)
            
    def is_run_limit_reached(self) -> bool:
        return self.requests_this_run >= self.max_requests_per_run
        
    def is_details_limit_reached(self) -> bool:
        return self.details_this_run >= self.max_details_per_run
