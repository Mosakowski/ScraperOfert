import csv
import json
import sqlite3
import yaml
from pathlib import Path
from typing import Dict, Any, List

from scraper_ofert_tv.storage import get_connection, now_iso

def export_missing_specs(db_path: Path = None):
    conn = get_connection(db_path) if db_path else get_connection()
    cursor = conn.cursor()
    
    # Znajdz oferty z wykrytym brandem i modelem (ale niezbyt generycznym),
    # ktore nie maja wpisu w model_specs, ALBO wpis istnieje ale brakuje kluczowych pol.
    # Posortuj malejaco po ilosci ofert.
    
    cursor.execute("""
        SELECT o.brand, o.model as raw_model
        FROM offers o
        WHERE o.brand IS NOT NULL AND o.model IS NOT NULL
    """)
    rows = cursor.fetchall()
    
    # We need to compute normalized_model exactly as we do when querying
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
    
    missing_list = []
    
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
            if not spec['screen_size_inches']: missing_fields.append('screen_size_inches')
            
        if missing_fields:
            missing_list.append({
                'brand': brand,
                'model': model,
                'normalized_model': normalized,
                'offers_count': g['offers_count'],
                'example_title': g['example_title'],
                'example_url': g['example_url'],
                'current_detected_size': g['example_size'],
                'current_detected_technology': g['example_tech'],
                'current_detected_resolution': g['example_res'],
                'missing_fields': ",".join(missing_fields)
            })
            
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / 'missing_model_specs.csv'
    
    if not missing_list:
        print("Brak modeli do uzupelnienia specyfikacji.")
        return
        
    keys = missing_list[0].keys()
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(missing_list)
        
    print(f"Wyeksportowano {len(missing_list)} brakujacych modeli do {out_path}")
    conn.close()

def import_model_specs(yaml_path: str, db_path: Path = None):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    if not isinstance(data, list):
        print("Błąd: Plik YAML musi zawierać listę.")
        return
        
    conn = get_connection(db_path) if db_path else get_connection()
    cursor = conn.cursor()
    now = now_iso()
    
    added = 0
    updated = 0
    skipped = 0
    
    def _norm(m):
        return "".join(c.lower() for c in m if c.isalnum())
        
    for item in data:
        brand = (item.get('brand') or '').lower()
        model = item.get('model')
        if not brand or not model:
            skipped += 1
            continue
            
        normalized = _norm(model)
        size = item.get('screen_size_inches')
        tech = item.get('technology')
        res = item.get('resolution')
        year = item.get('year')
        series = item.get('series')
        src_url = item.get('source_url')
        src_name = item.get('source_name')
        conf = float(item.get('spec_confidence', 0.8))
        if conf < 0 or conf > 1:
            conf = 0.8
        notes = item.get('notes')
        
        cursor.execute("SELECT * FROM model_specs WHERE brand = ? AND normalized_model = ?", (brand, normalized))
        existing = cursor.fetchone()
        
        if existing:
            # Update only if new value is not empty or overwrite explicitly?
            # User requirement: "nie nadpisywac lepszych danych pustymi wartosciami"
            new_size = size if size else existing['screen_size_inches']
            new_tech = tech if tech else existing['technology']
            new_res = res if res else existing['resolution']
            new_year = year if year else existing['year']
            new_series = series if series else existing['series']
            new_src_url = src_url if src_url else existing['source_url']
            new_src_name = src_name if src_name else existing['source_name']
            new_conf = conf if conf else existing['spec_confidence']
            new_notes = notes if notes else existing['notes']
            
            cursor.execute("""
                UPDATE model_specs SET 
                screen_size_inches = ?, technology = ?, resolution = ?,
                year = ?, series = ?, source_url = ?, source_name = ?,
                spec_confidence = ?, notes = ?, updated_at = ?
                WHERE brand = ? AND normalized_model = ?
            """, (new_size, new_tech, new_res, new_year, new_series, new_src_url, new_src_name, new_conf, new_notes, now, brand, normalized))
            updated += 1
        else:
            cursor.execute("""
                INSERT INTO model_specs 
                (brand, model, normalized_model, screen_size_inches, technology, resolution, year, series, source_url, source_name, spec_confidence, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (brand, model, normalized, size, tech, res, year, series, src_url, src_name, conf, notes, now, now))
            added += 1
            
    conn.commit()
    conn.close()
    
    print(f"Import zakończony. Dodano: {added}, Zaktualizowano: {updated}, Pominięto: {skipped}")
