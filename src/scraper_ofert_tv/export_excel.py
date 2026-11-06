import sqlite3
import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from scraper_ofert_tv.storage import now_iso

def export_to_excel(conn: sqlite3.Connection, output_dir: Path):
    os.makedirs(output_dir, exist_ok=True)
    
    # Tworzymy plik
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_file = output_dir / "oferty_olx_latest.xlsx"
    archive_file = output_dir / f"oferty_olx_{timestamp}.xlsx"
    legacy_tv_file = output_dir / "oferty_tv_latest.xlsx"
    
    wb = Workbook()
    
    # Arkusz 1: Lodz alerty (jesli jest, dajemy na poczatek zeby przykuc uwage)
    ws_alerts = wb.active
    ws_alerts.title = "Lodz alerty"
    _write_lodz_alerts(conn, ws_alerts)
    
    # Arkusz 2: Lodz kandydaci (diagnostyka)
    ws_lodz_cand = wb.create_sheet("Lodz kandydaci")
    _write_lodz_candidates(conn, ws_lodz_cand)
    
    # Arkusz 3: Oferty
    ws_offers = wb.create_sheet("Oferty")
    _write_offers(conn, ws_offers)
    
    # Arkusz 3: Baza cen
    ws_market = wb.create_sheet("Baza cen")
    _write_market(conn, ws_market)
    
    # Arkusz: Pokrycie rynku
    ws_coverage = wb.create_sheet("Pokrycie rynku")
    _write_market_coverage(conn, ws_coverage)
    
    # Arkusz 4: Historia skanow
    ws_runs = wb.create_sheet("Historia skanow")
    _write_scans(conn, ws_runs)
    
    # Arkusz 5: Braki specyfikacji
    ws_missing = wb.create_sheet("Braki specyfikacji modeli")
    _write_missing_specs(conn, ws_missing)
    
    # Formatowanie (zamrozenie naglowkow, filtry, itp.)
    for ws in wb.worksheets:
        _format_sheet(ws)
        
    wb.save(latest_file)
    wb.save(archive_file)
    shutil.copy2(latest_file, legacy_tv_file)
    
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
        
def _write_lodz_candidates(conn, ws):
    headers = [
        "Tytuł", "Cena (PLN)", "Score", "Status", "Zysk (PLN)", "Rabat (%)", 
        "Cena ref. (PLN)", "Klucz", "Pewność", 
        "Model", "Źródło modelu", "Technologia", "Źródło technologii",
        "Liczba ofert ref.", "Powód niskiego conf.", "Scoring Reasons", "Użyto model_specs", "Rule Flags", "URL"
    ]
    ws.append(headers)
    
    cursor = conn.cursor()
    cursor.execute("SELECT value_json FROM settings WHERE key = 'scoring_settings'")
    row = cursor.fetchone()
    import json
    scoring_settings = json.loads(row['value_json']) if row else {}
    min_score = float(scoring_settings.get("show_lodz_candidates_min_score", 0.0))
    
    lodz_condition = """
        (o.city LIKE '%lodz%' OR o.city LIKE '%łódź%' OR 
         o.raw_location LIKE '%lodz%' OR o.raw_location LIKE '%łódź%' OR 
         o.raw_location LIKE '%lodzkie%' OR o.raw_location LIKE '%łódzkie%' OR
         EXISTS (SELECT 1 FROM offer_snapshots os WHERE os.offer_id = o.id AND os.scan_mode = 'lodz_alerts'))
    """
    
    query = f"""
        SELECT 
            o.title, o.price_pln, s.score, o.system_status, s.estimated_profit_pln, 
            s.market_discount_percent, s.reference_price_pln, o.comparable_key, 
            s.comparable_offers_count, s.comparison_confidence, s.scoring_reasons_json,
            (SELECT GROUP_CONCAT(rm.rule_id, ', ') FROM rule_matches rm WHERE rm.offer_id = o.id) as rule_flags,
            o.url, o.brand, o.model, o.technology, o.normalization_diagnostics_json
        FROM offers o
        JOIN offer_scores s ON s.offer_id = o.id
        WHERE {lodz_condition} AND s.score >= ?
        ORDER BY s.score DESC, s.estimated_profit_pln DESC
        LIMIT 100
    """
    cursor.execute(query, (min_score,))
    for r in cursor.fetchall():
        conf_str = r['comparison_confidence']
        try:
            conf = float(conf_str) if conf_str else 0.0
        except:
            conf = 0.0
            
        reasons = []
        if conf < 0.7:
            if not r['brand']:
                reasons.append("brak marki")
            if not r['model']:
                reasons.append("brak modelu")
            if not r['technology']:
                reasons.append("brak technologii")
            
            comp_key = r['comparable_key'] or ""
            if len(comp_key.split('_')) <= 2:
                reasons.append("klucz zbyt ogólny")
                
            comp_count = r['comparable_offers_count'] or 0
            if comp_count < 10:
                reasons.append(f"mała próbka (N={comp_count})")
                
        low_conf_reason = ", ".join(reasons)
        
        diag = {}
        if r['normalization_diagnostics_json']:
            diag = json.loads(r['normalization_diagnostics_json'])
            
        model_val = r['model'] or "BRAK"
        model_src = diag.get('model_source', "none")
        if not r['model']: model_src = "brak wzorca"
        
        tech_val = r['technology'] or "BRAK"
        tech_src = diag.get('technology_source', "none")
        if not r['technology']: tech_src = "brak słowa kluczowego"
        
        used_specs = "Tak" if diag.get('model_specs_used') else "Nie"
        
        ws.append([
            r['title'], r['price_pln'], r['score'], r['system_status'], 
            r['estimated_profit_pln'], r['market_discount_percent'], 
            r['reference_price_pln'], r['comparable_key'], r['comparison_confidence'],
            model_val, model_src, tech_val, tech_src,
            r['comparable_offers_count'], low_conf_reason, 
            r['scoring_reasons_json'], used_specs, r['rule_flags'], r['url']
        ])

def _write_offers(conn, ws):
    headers = ["ID", "Kategoria", "Status", "Tytuł", "Cena (PLN)", "Miasto", "Parametry", "Marka", "Model", "Klucz", "Pewność", "URL"]
    ws.append(headers)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, c.label AS category, o.system_status, o.title, o.price_pln, o.city,
               o.detected_size_inches, o.attributes_json, o.brand, o.model, o.comparable_key,
               o.comparison_confidence, o.url
        FROM offers o LEFT JOIN categories c ON c.id=o.category_id
        ORDER BY id DESC LIMIT 5000
    """)
    for r in cursor.fetchall():
        ws.append([
            r['id'], r['category'], r['system_status'], r['title'], r['price_pln'], r['city'],
            r['attributes_json'] or (f"{r['detected_size_inches']} cali" if r['detected_size_inches'] else ""),
            r['brand'], r['model'], r['comparable_key'], r['comparison_confidence'], r['url']
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

def _write_market_coverage(conn, ws):
    headers = [
        "Klucz", "Liczba ofert (National)", "Mediana", "P25", "P75",
        "Pewność (Confidence)", "Liczba ofert (Łódź)"
    ]
    ws.append(headers)
    
    lodz_condition = """
        (o.city LIKE '%lodz%' OR o.city LIKE '%łódź%' OR 
         o.raw_location LIKE '%lodz%' OR o.raw_location LIKE '%łódź%' OR 
         o.raw_location LIKE '%lodzkie%' OR o.raw_location LIKE '%łódzkie%' OR
         EXISTS (SELECT 1 FROM offer_snapshots os WHERE os.offer_id = o.id AND os.scan_mode = 'lodz_alerts'))
    """
    
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT 
            m.comparable_key, m.offers_count, m.median_price_pln, 
            m.p25_price_pln, m.p75_price_pln, m.confidence,
            (SELECT COUNT(*) FROM offers o WHERE o.comparable_key = m.comparable_key AND {lodz_condition}) as lodz_count
        FROM market_price_references m
        ORDER BY m.offers_count DESC
    """)
    for r in cursor.fetchall():
        ws.append([
            r['comparable_key'], r['offers_count'], r['median_price_pln'],
            r['p25_price_pln'], r['p75_price_pln'], r['confidence'], r['lodz_count']
        ])
        
def _write_scans(conn, ws):
    headers = [
        "ID", "Tryb", "Status", "Profile total", "Profile done",
        "Oferty widziane", "Oferty nowe", "Oferty znane",
        "Start", "Koniec", "Powod stopu"
    ]
    ws.append(headers)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, mode, status, profiles_total, profiles_done, offers_seen,
               offers_new, offers_known, started_at, finished_at, stop_reason
        FROM search_runs
        ORDER BY id DESC LIMIT 100
    """)
    for r in cursor.fetchall():
        ws.append([
            r['id'], r['mode'], r['status'], r['profiles_total'], r['profiles_done'],
            r['offers_seen'], r['offers_new'], r['offers_known'],
            r['started_at'], r['finished_at'], r['stop_reason']
        ])

def _write_missing_specs(conn, ws):
    headers = ["Marka", "Model", "Znormalizowany", "Liczba ofert", "Tytuł przykładowy", "Braki", "Obecny Rozmiar", "Obecna Tech", "Obecna Res", "URL przykładowy"]
    ws.append(headers)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.brand, o.model as raw_model
        FROM offers o
        WHERE o.brand IS NOT NULL AND o.model IS NOT NULL
    """)
    def _norm(m):
        return "".join(c.lower() for c in m if c.isalnum())
        
    cursor.execute("SELECT brand, normalized_model, technology, resolution, screen_size_inches FROM model_specs")
    specs = {}
    for r in cursor.fetchall():
        specs[(r['brand'].lower(), r['normalized_model'])] = r
        
    cursor.execute("""
        SELECT 
            o.brand, 
            o.model,
            COUNT(o.id) as offers_count,
            MIN(s.title) as example_title,
            MIN(o.url) as example_url,
            MIN(o.detected_size_inches) as example_size,
            MIN(o.technology) as example_tech,
            MIN(o.resolution) as example_res
        FROM offers o
        LEFT JOIN offer_snapshots s ON s.offer_id = o.id
        WHERE o.brand IS NOT NULL AND o.model IS NOT NULL
        GROUP BY o.brand, o.model
        ORDER BY offers_count DESC
    """)
    groups = cursor.fetchall()
    
    for g in groups:
        brand = g['brand'].lower()
        model = g['model']
        normalized = _norm(model)
        
        spec = specs.get((brand, normalized))
        missing_fields = []
        if not spec:
            missing_fields = ['all']
        else:
            if not spec['technology']: missing_fields.append('technology')
            if not spec['resolution']: missing_fields.append('resolution')
            if not spec['screen_size_inches']: missing_fields.append('size')
            
        if missing_fields:
            ws.append([
                brand, model, normalized, g['offers_count'], g['example_title'],
                ", ".join(missing_fields), g['example_size'], g['example_tech'], g['example_res'], g['example_url']
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
