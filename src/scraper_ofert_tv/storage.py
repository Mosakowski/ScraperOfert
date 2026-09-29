import sqlite3
import shutil
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Sciezka domyslna, moze byc nadpisana przy inicjalizacji
DEFAULT_DB_PATH = Path("data/offers.sqlite")

def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Zwraca polaczenie do bazy danych."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Wlaczamy foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def now_iso() -> str:
    """Obecny czas w formacie ISO UTC."""
    return datetime.now(timezone.utc).isoformat()

def create_search_run(conn: sqlite3.Connection, mode: str) -> int:
    """Tworzy nowy wpis w search_runs i zwraca jego ID."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO search_runs (mode, status, started_at) VALUES (?, ?, ?)",
        (mode, "running", now_iso())
    )
    conn.commit()
    return cursor.lastrowid

def update_search_run(conn: sqlite3.Connection, run_id: int, status: str, **kwargs):
    """Aktualizuje wpis search_run."""
    fields = ["status = ?", "finished_at = ?"]
    values = [status, now_iso() if status != "running" else None]
    
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        values.append(v)
        
    values.append(run_id)
    
    query = f"UPDATE search_runs SET {', '.join(fields)} WHERE id = ?"
    conn.execute(query, values)
    conn.commit()

def create_search_profile_run(conn: sqlite3.Connection, run_id: int, profile_id: str, mode: str, search_url: str) -> int:
    """Tworzy nowy przebieg pojedynczego profilu."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO search_profile_runs 
           (search_run_id, size_profile_id, mode, status, search_url, started_at) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_id, profile_id, mode, "running", search_url, now_iso())
    )
    conn.commit()
    return cursor.lastrowid

def upsert_offer(conn: sqlite3.Connection, offer_data: dict) -> int:
    """Dodaje nowa oferte lub aktualizuje istniejaca (np. timestamp ostatniego widzenia). Zwraca ID."""
    cursor = conn.cursor()
    
    url_hash = offer_data.get('url_hash')
    olx_offer_id = offer_data.get('olx_offer_id')
    canonical_url = offer_data.get('canonical_url')
    
    # 1. Deduplikacja: szukamy istniejacej oferty
    query = "SELECT id FROM offers WHERE url_hash = ?"
    params = [url_hash]
    
    if olx_offer_id:
        query += " OR olx_offer_id = ?"
        params.append(olx_offer_id)
        
    if canonical_url:
        query += " OR canonical_url = ?"
        params.append(canonical_url)
        
    cursor.execute(query, params)
    row = cursor.fetchone()
    
    now = now_iso()
    
    if row:
        # Aktualizacja
        offer_id = row['id']
        update_fields = ["last_seen_at = ?", "updated_at = ?"]
        update_values = [now, now]
        
        # Opcjonalnie mozna aktualizowac inne pola jesli sie zmienily np. cena
        if 'price_pln' in offer_data:
            update_fields.append("price_pln = ?")
            update_values.append(offer_data['price_pln'])
            
        update_values.append(offer_id)
        update_query = f"UPDATE offers SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(update_query, update_values)
    else:
        # Wstawienie nowej
        fields = ["created_at", "updated_at", "first_seen_at", "last_seen_at"]
        values = [now, now, now, now]
        for k, v in offer_data.items():
            fields.append(k)
            values.append(v)
            
        placeholders = ", ".join(["?"] * len(values))
        insert_query = f"INSERT INTO offers ({', '.join(fields)}) VALUES ({placeholders})"
        cursor.execute(insert_query, values)
        offer_id = cursor.lastrowid

    conn.commit()
    return offer_id

def create_offer_snapshot(conn: sqlite3.Connection, snapshot_data: dict) -> int:
    """Zapisuje zrzut danych oferty."""
    snapshot_data['scraped_at'] = snapshot_data.get('scraped_at', now_iso())
    
    fields = list(snapshot_data.keys())
    values = list(snapshot_data.values())
    placeholders = ", ".join(["?"] * len(values))
    
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO offer_snapshots ({', '.join(fields)}) VALUES ({placeholders})", values)
    conn.commit()
    return cursor.lastrowid

def record_price_history(conn: sqlite3.Connection, offer_id: int, price_pln: int, raw_price: str, snapshot_id: int = None):
    """Zapisuje historie ceny, jesli sie zmienila."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price_pln FROM offer_price_history WHERE offer_id = ? ORDER BY detected_at DESC LIMIT 1",
        (offer_id,)
    )
    row = cursor.fetchone()
    
    if row and row['price_pln'] == price_pln:
        # Cena sie nie zmienila, wiec nie tworzymy nowego wpisu
        return
        
    cursor.execute(
        """INSERT INTO offer_price_history (offer_id, price_pln, raw_price, detected_at, source_snapshot_id) 
           VALUES (?, ?, ?, ?, ?)""",
        (offer_id, price_pln, raw_price, now_iso(), snapshot_id)
    )
    conn.commit()

def backup_database(db_path: Path = DEFAULT_DB_PATH, backups_dir: Path = Path("data/backups")):
    """Tworzy kopie bezpieczenstwa bazy danych."""
    if not db_path.exists():
        return None
        
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backups_dir / f"offers_{timestamp}.sqlite"
    
    shutil.copy2(db_path, backup_path)
    return backup_path
