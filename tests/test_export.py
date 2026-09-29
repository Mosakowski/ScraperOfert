import pytest
import os
from pathlib import Path
from scraper_ofert_tv.export_excel import export_to_excel
from scraper_ofert_tv.migrations import apply_migrations
import openpyxl

@pytest.fixture
def db_for_export(tmp_path):
    db_path = tmp_path / "test_export.sqlite"
    apply_migrations(db_path)
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def test_export_to_excel(db_for_export, tmp_path):
    output_dir = tmp_path / "output"
    export_to_excel(db_for_export, output_dir)
    
    latest_file = output_dir / "oferty_tv_latest.xlsx"
    assert latest_file.exists()
    
    wb = openpyxl.load_workbook(latest_file)
    assert len(wb.sheetnames) == 4
    assert "Lodz alerty" in wb.sheetnames
    assert "Oferty" in wb.sheetnames
    assert "Baza cen" in wb.sheetnames
    assert "Historia skanow" in wb.sheetnames
    
    ws_alerts = wb["Lodz alerty"]
    assert ws_alerts["A1"].value == "ID Alertu"
