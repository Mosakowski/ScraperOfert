import sqlite3
from datetime import datetime, timezone

from scraper_ofert_tv.details_queue import get_pending_tasks
from scraper_ofert_tv.offer_relevance import eligible_for_details
from scraper_ofert_tv.response_status import classify_response


def test_gone_page_with_embedded_captcha_configuration_is_not_a_challenge():
    html = '<script>{"captchaSiteKey":"abc"}</script><div>Ogłoszenie niedostępne</div>'
    assert classify_response(410, html) == "gone"
    assert classify_response(404, html) == "not_found"
    assert classify_response(200, html) is None
    assert classify_response(200, '<iframe src="/captcha/challenge"></iframe>') == "captcha_detected"


def test_relevance_excludes_other_departments_and_extended_search():
    assert eligible_for_details("televisions", "https://www.olx.pl/d/oferta/telewizor-tv-CID99-ID123.html")
    assert not eligible_for_details("televisions", "https://www.olx.pl/d/oferta/bransoletka-CID87-ID123.html")
    assert not eligible_for_details("televisions", "https://www.olx.pl/d/oferta/czytnik-ebook-CID99-ID123.html")
    assert not eligible_for_details("televisions", "https://www.olx.pl/d/oferta/steam-deck-lcd-CID99-ID123.html")
    assert not eligible_for_details("televisions", "https://www.otomoto.pl/osobowe/oferta/ford.html")
    assert not eligible_for_details("laptops", "https://www.olx.pl/d/oferta/laptop-CID99-ID123.html?reason=extended_search_no_results_last_resort")
    assert eligible_for_details("furniture", "https://www.olx.pl/d/oferta/sofa-CID628-ID123.html")


def test_queue_skips_unrelated_and_prioritizes_fresh_untried():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE offers (id INTEGER PRIMARY KEY, category_id TEXT, url TEXT, gone_at TEXT, last_seen_at TEXT,
            city TEXT, raw_location TEXT);
        CREATE TABLE details_queue (id INTEGER PRIMARY KEY, offer_id INTEGER, status TEXT, attempts INTEGER,
            priority INTEGER, created_at TEXT, available_after TEXT, last_error TEXT, finished_at TEXT, updated_at TEXT);
        CREATE TABLE offer_snapshots (offer_id INTEGER, scan_mode TEXT);
    """)
    now = datetime.now(timezone.utc).isoformat()
    for ident, cid, attempts, created in ((1, "99", 1, "2026-11-01"),
                                           (2, "87", 0, "2026-11-20"),
                                           (3, "99", 0, "2026-11-21")):
        conn.execute("INSERT INTO offers VALUES (?, 'televisions', ?, NULL, ?, NULL, NULL)",
                     (ident, f"https://www.olx.pl/d/oferta/telewizor-CID{cid}-ID{ident}.html", now))
        conn.execute("INSERT INTO details_queue VALUES (?, ?, 'pending', ?, 100, ?, NULL, NULL, NULL, NULL)",
                     (ident, ident, attempts, created))
    tasks = get_pending_tasks(conn, 10)
    assert [task["id"] for task in tasks] == [3, 1]
    assert conn.execute("SELECT status FROM details_queue WHERE id=2").fetchone()[0] == "skipped"
