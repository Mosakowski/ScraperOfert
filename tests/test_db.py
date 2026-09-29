import pytest
from pathlib import Path
import sqlite3

from scraper_ofert_tv.migrations import apply_migrations
from scraper_ofert_tv.storage import (
    get_connection,
    create_search_run,
    create_search_profile_run,
    upsert_offer,
    create_offer_snapshot,
    record_price_history,
    backup_database
)

@pytest.fixture
def memory_db(tmp_path):
    """Tworzy baze w pamieci/tymczasowym pliku dla testow."""
    db_path = tmp_path / "test_offers.sqlite"
    apply_migrations(db_path)
    return db_path

def test_migrations(memory_db):
    """Testuje czy po migracji tabele i dane domyslne istnieja."""
    conn = get_connection(memory_db)
    cursor = conn.cursor()
    
    # Sprawdz czy sa reguly
    cursor.execute("SELECT count(*) as count FROM description_rules")
    rules_count = cursor.fetchone()['count']
    assert rules_count > 0

    # Sprawdz ustawienia
    cursor.execute("SELECT value_json FROM settings WHERE key = 'global_filters'")
    assert cursor.fetchone() is not None

def test_deduplication(memory_db):
    """Testuje deduplikacje ofery przy upsertcie."""
    conn = get_connection(memory_db)
    
    offer_1 = {
        'url': 'https://olx.pl/oferta/1',
        'url_hash': 'hash_1',
        'olx_offer_id': 'olx_1',
        'title': 'Telewizor 1',
        'price_pln': 500
    }
    
    # Pierwsze wstawienie
    id_1 = upsert_offer(conn, offer_1)
    assert id_1 > 0
    
    # Próba wstawienia duplikatu (po url_hash / olx_offer_id)
    offer_2 = {
        'url': 'https://olx.pl/oferta/1',
        'url_hash': 'hash_1', # ten sam hash
        'olx_offer_id': 'olx_1', # to samo ID
        'title': 'Telewizor 1 - zmieniony tytul',
        'price_pln': 450
    }
    id_2 = upsert_offer(conn, offer_2)
    
    assert id_1 == id_2 # Powinno to byc to samo ID (aktualizacja)
    
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) as count FROM offers")
    count = cursor.fetchone()['count']
    assert count == 1
    
    # Sprawdzenie aktualizacji ceny
    cursor.execute("SELECT price_pln FROM offers WHERE id = ?", (id_1,))
    price = cursor.fetchone()['price_pln']
    assert price == 450
