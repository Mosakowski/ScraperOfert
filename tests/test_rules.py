import pytest
from scraper_ofert_tv.rules import evaluate_rules
from scraper_ofert_tv.migrations import apply_migrations

@pytest.fixture
def db_with_rules(tmp_path):
    db_path = tmp_path / "test_rules.sqlite"
    apply_migrations(db_path)
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def test_evaluate_rules(db_with_rules):
    # Regula opisowa bazowa to np. uszkodzona matryca = reject
    normalized = {}
    detail = {
        'full_title': 'Telewizor LG',
        'description': 'Telewizor dziala ale ma zbita matryca. Nie nadaje sie do ogledzin.'
    }
    
    matched, actions = evaluate_rules(db_with_rules, normalized, detail)
    
    # "zbita matryca" -> uszkodzona matryca (jezeli taka regula jest w seeds, a jest "uszkodzon|zbit|rozbit")
    assert len(matched) > 0
    assert "reject" in actions

def test_evaluate_rules_no_match(db_with_rules):
    normalized = {}
    detail = {
        'full_title': 'Telewizor LG LED',
        'description': 'Sprzedam super telewizor w idealnym stanie.'
    }
    
    matched, actions = evaluate_rules(db_with_rules, normalized, detail)
    assert len(matched) == 0
    assert len(actions) == 0
