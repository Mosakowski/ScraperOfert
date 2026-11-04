import sqlite3
from pathlib import Path
from scraper_ofert_tv.storage import get_connection, now_iso
from scraper_ofert_tv.migrations import apply_migrations
from scraper_ofert_tv.detail_worker import DetailWorker
import scraper_ofert_tv.storage
import scraper_ofert_tv.details_queue
import os

def test_detail_worker_schema_match(monkeypatch):
    test_db = Path("data/test_worker.sqlite")
    if test_db.exists():
        test_db.unlink()
        
    def mock_get_conn(db_path=None):
        db_path = test_db
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
        
    monkeypatch.setattr(scraper_ofert_tv.storage, "get_connection", mock_get_conn)
    monkeypatch.setattr(scraper_ofert_tv.details_queue, "get_connection", mock_get_conn)
    monkeypatch.setattr("scraper_ofert_tv.detail_worker.get_connection", mock_get_conn)
    
    apply_migrations(test_db)
    conn = mock_get_conn()
    
    # 1. Zasilamy tabele offers
    now = now_iso()
    conn.execute("""
        INSERT INTO offers (source, url, url_hash, first_seen_at, last_seen_at, created_at, updated_at) 
        VALUES ('olx', 'http://example.com/tv', 'hash123', ?, ?, ?, ?)
    """, (now, now, now, now))
    offer_id = conn.cursor().execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # 2. Zasilamy details_queue
    conn.execute("INSERT INTO details_queue (offer_id, reason, created_at, updated_at) VALUES (?, 'test', ?, ?)", (offer_id, now, now))
    conn.commit()
    
    # 3. Mock scraper
    worker = DetailWorker()
    class MockScraper:
        class RateLimiter:
            def is_details_limit_reached(self):
                return False
        def __init__(self):
            self.rate_limiter = self.RateLimiter()
        def fetch_detail(self, url):
            return "<html><head><title>Test TV</title></head><body><h1>TV Samsung 55 cali 4k Oled</h1><div class='css-bgzo2k'>700 zł</div></body></html>", None, {}
        def close(self):
            pass
            
    worker.scraper = MockScraper()
    
    # Przebieg
    worker.work(limit=1)
    
    # Weryfikacja
    cur = conn.cursor()
    cur.execute("SELECT system_status, model, brand, detected_size_inches FROM offers WHERE id = ?", (offer_id,))
    o = cur.fetchone()
    assert o is not None
    
    cur.execute("SELECT count(*) as c FROM offer_snapshots WHERE offer_id = ?", (offer_id,))
    snap = cur.fetchone()
    assert snap['c'] == 1
    
    conn.close()
