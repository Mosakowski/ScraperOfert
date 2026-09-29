import sqlite3
from typing import List, Dict, Any
from scraper_ofert_tv.storage import get_connection, now_iso

def add_to_queue(conn: sqlite3.Connection, offer_id: int, reason: str, priority: int = 100):
    """
    Dodaje oferte do kolejki detali, o ile nie jest juz w kolejce ze statusem pending.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM details_queue WHERE offer_id = ? AND status IN ('pending', 'processing')",
        (offer_id,)
    )
    if cursor.fetchone():
        return # Juz jest w kolejce
        
    cursor.execute(
        """INSERT INTO details_queue (offer_id, reason, priority, status, created_at, updated_at) 
           VALUES (?, ?, ?, 'pending', ?, ?)""",
        (offer_id, reason, priority, now_iso(), now_iso())
    )
    conn.commit()

def get_pending_tasks(conn: sqlite3.Connection, limit: int = 10) -> List[Dict[str, Any]]:
    """Pobiera zadania z kolejki detali po priorytecie."""
    cursor = conn.cursor()
    # Zakladamy, ze nizszy priority to wyzszy waznoscia albo odwrotnie? 
    # Ustalmy ze wyzszy priorytet (100) jest pobierany najpierw (ORDER BY priority DESC).
    # Omijamy te z available_after w przyszlosci
    now = now_iso()
    cursor.execute(
        """SELECT * FROM details_queue 
           WHERE status = 'pending' AND (available_after IS NULL OR available_after <= ?)
           ORDER BY priority DESC, created_at ASC 
           LIMIT ?""",
        (now, limit)
    )
    return [dict(row) for row in cursor.fetchall()]

def mark_task_processing(conn: sqlite3.Connection, task_id: int):
    conn.execute(
        "UPDATE details_queue SET status = 'processing', updated_at = ? WHERE id = ?",
        (now_iso(), task_id)
    )
    conn.commit()

def mark_task_done(conn: sqlite3.Connection, task_id: int):
    now = now_iso()
    conn.execute(
        "UPDATE details_queue SET status = 'done', updated_at = ?, finished_at = ? WHERE id = ?",
        (now, now, task_id)
    )
    conn.commit()

def mark_task_failed(conn: sqlite3.Connection, task_id: int, error: str, retry_after_iso: str = None):
    cursor = conn.cursor()
    cursor.execute("SELECT attempts, max_attempts FROM details_queue WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    attempts = row['attempts'] + 1
    status = 'pending' if attempts < row['max_attempts'] else 'failed'
    
    now = now_iso()
    cursor.execute(
        """UPDATE details_queue 
           SET status = ?, attempts = ?, last_error = ?, available_after = ?, updated_at = ?
           WHERE id = ?""",
        (status, attempts, error, retry_after_iso, now, task_id)
    )
    conn.commit()

def mark_task_skipped(conn: sqlite3.Connection, task_id: int, reason: str):
    now = now_iso()
    conn.execute(
        "UPDATE details_queue SET status = 'skipped', last_error = ?, updated_at = ?, finished_at = ? WHERE id = ?",
        (reason, now, now, task_id)
    )
    conn.commit()
