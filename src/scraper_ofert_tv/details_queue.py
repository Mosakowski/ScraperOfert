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

def get_pending_tasks(conn: sqlite3.Connection, limit: int = 10, mode: str = None) -> List[Dict[str, Any]]:
    """Pobiera zadania z kolejki detali po priorytecie."""
    cursor = conn.cursor()
    now = now_iso()
    
    query = """
        SELECT dq.* 
        FROM details_queue dq
        JOIN offers o ON dq.offer_id = o.id
        WHERE dq.status = 'pending' AND (dq.available_after IS NULL OR dq.available_after <= ?)
        ORDER BY 
            CASE WHEN ? = 'lodz_alerts' AND (
                o.city LIKE '%lodz%' OR o.city LIKE '%łódź%' OR 
                o.raw_location LIKE '%lodz%' OR o.raw_location LIKE '%łódź%' OR 
                o.raw_location LIKE '%lodzkie%' OR o.raw_location LIKE '%łódzkie%' OR
                EXISTS (SELECT 1 FROM offer_snapshots os WHERE os.offer_id = o.id AND os.scan_mode = 'lodz_alerts')
            ) THEN 1 ELSE 0 END DESC,
            dq.priority DESC, 
            dq.created_at ASC 
        LIMIT ?
    """
    
    cursor.execute(query, (now, mode, limit))
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
