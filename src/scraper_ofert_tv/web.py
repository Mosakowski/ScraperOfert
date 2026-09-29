from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import os
import sqlite3
import subprocess

from scraper_ofert_tv.storage import get_connection

app = FastAPI(title="Scraper Ofert TV - Panel Webowy")

base_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(base_dir / "templates"))
app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")

def run_cli_command(command: str):
    import sys
    parts = command.split()
    if not parts:
        return
    action = parts[0]
    if action not in ["scan", "recalc-market", "export", "process-details"]:
        return
    args = [sys.executable, "-m", "scraper_ofert_tv"] + parts
    subprocess.Popen(args)

@app.get("/")
def index(request: Request):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Alert Lodz
    cursor.execute("""
        SELECT a.id, a.offer_id, o.title, o.price_pln, a.score, a.estimated_profit_pln, o.url, a.status
        FROM alert_events a
        JOIN offers o ON a.offer_id = o.id
        ORDER BY a.id DESC LIMIT 20
    """)
    alerts = [dict(r) for r in cursor.fetchall()]
    
    # Skan historia
    cursor.execute("SELECT * FROM search_runs ORDER BY id DESC LIMIT 10")
    scans = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "alerts": alerts,
            "scans": scans
        }
    )

@app.post("/action/scan")
def run_scan(mode: str = Form(...)):
    if mode not in ["national", "lodz_alerts"]:
        return RedirectResponse(url="/?error=invalid_mode", status_code=303)
    run_cli_command(f"scan --mode {mode}")
    return RedirectResponse(url="/", status_code=303)

@app.post("/action/recalc")
def run_recalc():
    run_cli_command("recalc-market")
    return RedirectResponse(url="/", status_code=303)

@app.post("/action/export")
def run_export():
    run_cli_command("export excel")
    return RedirectResponse(url="/", status_code=303)

@app.post("/action/decision")
def run_decision(alert_id: int = Form(...), decision: str = Form(...)):
    conn = get_connection()
    conn.execute("UPDATE alert_events SET status = ? WHERE id = ?", (decision, alert_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

from scraper_ofert_tv.settings_service import SettingsService

@app.get("/settings")
def get_settings(request: Request):
    service = SettingsService()
    global_filters = service.get_global_filters()
    scheduler = service.get_setting("scheduler", {"national_hours": 12, "lodz_hours": 2, "export_hours": 2})
    scoring = service.get_scoring_settings()
    size_profiles = service.get_size_profiles()
    
    return templates.TemplateResponse(
        request=request,
        name="settings.html", 
        context={
            "request": request,
            "global_filters": global_filters,
            "scheduler": scheduler,
            "scoring": scoring,
            "size_profiles": size_profiles
        }
    )

@app.post("/settings/save")
def save_settings(
    price_min: int = Form(300), price_max: int = Form(700),
    seller_type: str = Form("private"), condition: str = Form("used"),
    national_hours: int = Form(12), lodz_hours: int = Form(2), export_hours: int = Form(2),
    min_discount: float = Form(15.0), min_profit: int = Form(100), min_count: int = Form(3),
    min_score: float = Form(30.0), min_confidence: float = Form(0.7), estimated_costs: int = Form(50),
    suppress_hours: int = Form(24)
):
    service = SettingsService()
    service.set_setting("global_filters", {
        "price_min": price_min, "price_max": price_max, 
        "seller_type": seller_type, "condition": condition
    })
    service.set_setting("scheduler", {
        "national_hours": national_hours, "lodz_hours": lodz_hours, "export_hours": export_hours
    })
    service.set_setting("scoring_settings", {
        "min_discount": min_discount, "min_profit": min_profit, "min_count": min_count,
        "min_score": min_score, "min_confidence": min_confidence,
        "estimated_costs": estimated_costs, "suppress_hours": suppress_hours
    })
    return RedirectResponse(url="/settings", status_code=303)

@app.post("/settings/profile/toggle")
def toggle_profile(profile_id: str = Form(...), enabled: int = Form(...)):
    conn = get_connection()
    conn.execute("UPDATE size_profiles SET enabled = ? WHERE id = ?", (enabled, profile_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/settings", status_code=303)

@app.get("/rules")
def get_rules(request: Request):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM description_rules ORDER BY id DESC")
    rules = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return templates.TemplateResponse(request=request, name="rules.html", context={"request": request, "rules": rules})

@app.post("/rules/add")
def add_rule(
    rule_id: str = Form(...), category: str = Form(...), applies_to: str = Form(...), 
    patterns: str = Form(...), action: str = Form(...), score_delta: int = Form(...)
):
    import json
    from scraper_ofert_tv.storage import now_iso
    conn = get_connection()
    pats = [p.strip() for p in patterns.split(",")]
    now = now_iso()
    conn.execute("""
        INSERT INTO description_rules (id, enabled, category, severity, label, applies_to, match_mode, patterns_json, action, score_delta, created_at, updated_at)
        VALUES (?, 1, ?, 'medium', ?, ?, 'phrase', ?, ?, ?, ?, ?)
    """, (rule_id, category, rule_id, applies_to, json.dumps(pats), action, score_delta, now, now))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/rules", status_code=303)
    
@app.post("/rules/toggle")
def toggle_rule(rule_id: str = Form(...), enabled: int = Form(...)):
    conn = get_connection()
    conn.execute("UPDATE description_rules SET enabled = ? WHERE id = ?", (enabled, rule_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/rules", status_code=303)

@app.post("/rules/test")
def test_rule(text: str = Form(...)):
    from scraper_ofert_tv.rules import evaluate_rules
    conn = get_connection()
    detail = {"description": text, "full_title": text}
    matched, actions = evaluate_rules(conn, {}, detail)
    conn.close()
    
    # Przekazanie wyniku testu do UI to maly hack przez query parameter w MVP
    import urllib.parse
    res = urllib.parse.quote(str(matched))
    return RedirectResponse(url=f"/rules?test_result={res}", status_code=303)
