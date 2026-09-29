import sqlite3
import os
from pathlib import Path
from datetime import datetime, timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from scraper_ofert_tv.storage import now_iso

def export_to_excel(conn: sqlite3.Connection, output_dir: Path):
    os.makedirs(output_dir, exist_ok=True)
    
    # Tworzymy plik
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_file = output_dir / "oferty_tv_latest.xlsx"
    archive_file = output_dir / f"oferty_tv_{timestamp}.xlsx"
    
    wb = Workbook()
    
    # Arkusz 1: Lodz alerty (jesli jest, dajemy na poczatek zeby przykuc uwage)
    ws_alerts = wb.active
    ws_alerts.title = "Lodz alerty"
    _write_lodz_alerts(conn, ws_alerts)
    
    # Arkusz 2: Oferty
    ws_offers = wb.create_sheet("Oferty")
    _write_offers(conn, ws_offers)
    
    # Arkusz 3: Baza cen
    ws_market = wb.create_sheet("Baza cen")
    _write_market(conn, ws_market)
    
    # Arkusz 4: Historia skanow
    ws_runs = wb.create_sheet("Historia skanow")
    _write_scans(conn, ws_runs)
    
    # Formatowanie (zamrozenie naglowkow, filtry, itp.)
    for ws in wb.worksheets:
        _format_sheet(ws)
        
    wb.save(latest_file)
    wb.save(archive_file)
    
    # Zapisujemy log do bazy
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO export_runs (
            export_type, status, output_path, archived_path,
            rows_offers, rows_lodz_alerts, rows_market, rows_scan_history,
            started_at, finished_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'excel', 'success', str(latest_file), str(archive_file),
        ws_offers.max_row - 1, ws_alerts.max_row - 1, ws_market.max_row - 1, ws_runs.max_row - 1,
        now_iso(), now_iso()
    ))
    conn.commit()

def _write_lodz_alerts(conn, ws):
    headers = ["ID Alertu", "Tytuł", "URL", "Score", "Zysk (PLN)", "Rabat (%)", "Cena ref. (PLN)", "Cena oferty (PLN)", "Data alertu"]
    ws.append(headers)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, o.title, o.url, a.score, a.estimated_profit_pln, a.market_discount_percent,
               a.reference_price_pln, a.offer_price_pln, a.first_created_at
        FROM alert_events a
        JOIN offers o ON a.offer_id = o.id
        ORDER BY a.id DESC
    """)
    for r in cursor.fetchall():
        ws.append([
            r['id'], r['title'], r['url'], r['score'], r['estimated_profit_pln'], 
            r['market_discount_percent'], r['reference_price_pln'], r['offer_price_pln'], r['first_created_at']
        ])
        
def _write_offers(conn, ws):
    headers = ["ID", "Status", "Tytuł", "Cena (PLN)", "Miasto", "Rozmiar", "Marka", "Model", "Klucz", "Pewność", "URL"]
    ws.append(headers)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, system_status, title, price_pln, city, detected_size_inches, brand, model, comparable_key, comparison_confidence, url
        FROM offers
        ORDER BY id DESC LIMIT 5000
    """)
    for r in cursor.fetchall():
        ws.append([
            r['id'], r['system_status'], r['title'], r['price_pln'], r['city'], 
            r['detected_size_inches'], r['brand'], r['model'], r['comparable_key'], r['comparison_confidence'], r['url']
        ])

def _write_market(conn, ws):
    headers = ["Klucz", "Liczba ofert", "Mediana", "Średnia", "P25", "P75", "Data obliczenia"]
    ws.append(headers)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT comparable_key, offers_count, median_price_pln, avg_price_pln, p25_price_pln, p75_price_pln, calculated_at
        FROM market_price_references
        ORDER BY offers_count DESC
    """)
    for r in cursor.fetchall():
        ws.append([
            r['comparable_key'], r['offers_count'], r['median_price_pln'], r['avg_price_pln'], 
            r['p25_price_pln'], r['p75_price_pln'], r['calculated_at']
        ])
        
def _write_scans(conn, ws):
    headers = ["ID", "Tryb", "Status", "L. Ofert Nowych", "L. Ofert Wygasłych", "Start", "Koniec", "Powód stopu"]
    ws.append(headers)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, mode, status, offers_new, offers_known, started_at, finished_at, stop_reason
        FROM search_runs
        ORDER BY id DESC LIMIT 100
    """)
    for r in cursor.fetchall():
        ws.append([
            r['id'], r['mode'], r['status'], r['offers_new'], r['offers_known'], 
            r['started_at'], r['finished_at'], r['stop_reason']
        ])

def _format_sheet(ws):
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    # Formatuj naglowek
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        
    # Zamrozenie naglowka
    ws.freeze_panes = "A2"
    
    # Dodaj auto-filtr
    if ws.max_row > 1:
        # Get column letter for max col
        from openpyxl.utils import get_column_letter
        max_col_letter = get_column_letter(ws.max_column)
        ws.auto_filter.ref = f"A1:{max_col_letter}{ws.max_row}"
        
    # Znajdz kolumne "URL" we wszystkich wierszach, i zrob link
    url_col_idx = None
    for idx, cell in enumerate(ws[1]):
        if cell.value == "URL":
            url_col_idx = idx + 1
            break
            
    if url_col_idx:
        blue_font = Font(color="0000FF", underline="single")
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row=row, column=url_col_idx)
            if cell.value:
                cell.hyperlink = cell.value
                cell.font = blue_font
