from fastapi import FastAPI, Request, Form, BackgroundTasks, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import os
import sqlite3
import subprocess
from urllib.parse import urlencode
import json
import re

from scraper_ofert_tv.storage import get_connection

app = FastAPI(title="Scraper Ofert TV - Panel Webowy")

base_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(base_dir / "templates"))
app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")

OFFER_PAGE_SIZES = (50, 100, 200)

OFFER_SORT_COLUMNS = {
    "title": "o.title",
    "price": "o.price_pln",
    "city": "COALESCE(o.city, o.raw_location)",
    "size": "COALESCE(o.detected_size_inches, 0)",
    "model": "COALESCE(o.brand, '') || ' ' || COALESCE(o.model, '')",
    "score": "s.score",
    "profit": "s.estimated_profit_pln",
    "confidence": "CAST(s.comparison_confidence AS REAL)",
    "status": "o.system_status",
    "seen": "o.last_seen_at",
}

OFFER_STATUS_LABELS = {
    "new": "Nowa",
    "active": "Aktywna",
    "priced": "Wyceniona",
    "opportunity": "Okazja",
    "candidate": "Kandydat",
    "needs_review": "Do sprawdzenia",
    "review_bundle": "Zestaw do sprawdzenia",
    "weak_match": "Słabe dopasowanie",
    "rejected": "Odrzucona",
    "alert": "Alert",
    "alerted": "Zaalertowana",
}

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
def index(request: Request, category: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    categories = [dict(row) for row in cursor.execute("SELECT id,label FROM categories WHERE enabled=1 ORDER BY label").fetchall()]
    category_ids = {row["id"] for row in categories}
    if category not in category_ids:
        category = ""
    
    # Alert Lodz
    cursor.execute("""
        SELECT a.id, a.offer_id, o.title, o.price_pln, a.score, a.estimated_profit_pln, o.url, a.status,
               (SELECT COALESCE(os.main_photo_url, os.listing_thumbnail_url)
                FROM offer_snapshots os
                WHERE os.offer_id = o.id AND COALESCE(os.main_photo_url, os.listing_thumbnail_url) IS NOT NULL
                ORDER BY os.scraped_at DESC, os.id DESC LIMIT 1) AS photo_url
        FROM alert_events a
        JOIN offers o ON a.offer_id = o.id
        WHERE (? IS NULL OR o.category_id=?)
        ORDER BY a.id DESC LIMIT 20
    """, (category or None, category or None))
    alerts = [dict(r) for r in cursor.fetchall()]
    
    # Skan historia
    cursor.execute("""
        SELECT r.* FROM search_runs r
        WHERE (? IS NULL OR EXISTS (
            SELECT 1 FROM search_profile_runs spr
            LEFT JOIN search_profiles p ON p.id=spr.search_profile_id
            LEFT JOIN size_profiles sp ON sp.id=spr.size_profile_id
            WHERE spr.search_run_id=r.id AND COALESCE(p.category_id, sp.category_id, 'televisions')=?
        ))
        ORDER BY r.id DESC LIMIT 6
    """, (category or None, category or None))
    scans = [dict(r) for r in cursor.fetchall()]
    scan_status_labels = {
        "completed": "Zakończony", "success": "Sukces", "partial": "Częściowy",
        "running": "W trakcie", "failed": "Błąd",
    }
    for scan in scans:
        scan["status_label"] = scan_status_labels.get(scan["status"], scan["status"])

    cursor.execute("SELECT COUNT(*) AS total FROM offers WHERE gone_at IS NULL AND (? IS NULL OR category_id=?)", (category or None, category or None))
    active_offer_count = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM offers WHERE gone_at IS NULL AND system_status IN ('opportunity', 'candidate', 'needs_review') AND (? IS NULL OR category_id=?)", (category or None, category or None))
    review_offer_count = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM alert_events a JOIN offers o ON o.id=a.offer_id WHERE (? IS NULL OR o.category_id=?)", (category or None, category or None))
    alert_count = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM details_queue q JOIN offers o ON o.id=q.offer_id WHERE q.status IN ('pending', 'failed') AND (? IS NULL OR o.category_id=?)", (category or None, category or None))
    detail_queue_count = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(DISTINCT m.comparable_key) AS total FROM market_price_references m JOIN comparable_groups g ON g.comparable_key=m.comparable_key WHERE (? IS NULL OR g.category_id=?)", (category or None, category or None))
    market_group_count = cursor.fetchone()["total"]
    
    conn.close()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "alerts": alerts,
            "scans": scans,
            "categories": categories,
            "selected_category": category,
            "active_offer_count": active_offer_count,
            "review_offer_count": review_offer_count,
            "alert_count": alert_count,
            "detail_queue_count": detail_queue_count,
            "market_group_count": market_group_count,
            "active_page": "dashboard",
            "page_title": "Przegląd",
            "page_subtitle": "Rynek ofert OLX · Polska / lokalnie",
        }
    )


@app.get("/offers")
def list_offers(
    request: Request,
    q: str = Query(default="", max_length=120),
    category: str = "",
    size: str = "",
    status: str = "",
    availability: str = "current",
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=200),
    sort_by: str = "seen",
    sort_dir: str = "desc",
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, label, olx_size_value, enabled FROM size_profiles WHERE category_id='televisions' ORDER BY sort_order")
    profiles = [dict(row) for row in cursor.fetchall()]
    profile_by_id = {profile["id"]: profile for profile in profiles}
    profile_by_value = {profile["olx_size_value"]: profile for profile in profiles}

    categories = [dict(row) for row in cursor.execute("SELECT id,label FROM categories WHERE enabled=1 ORDER BY label").fetchall()]
    category_ids = {row["id"] for row in categories}
    if category not in category_ids:
        category = ""
    cursor.execute("SELECT DISTINCT system_status FROM offers WHERE system_status IS NOT NULL ORDER BY system_status")
    statuses = [row["system_status"] for row in cursor.fetchall()]

    if size not in profile_by_id and size != "unknown":
        size = ""
    if status not in statuses:
        status = ""
    if availability not in {"current", "unavailable", "all"}:
        availability = "current"
    if per_page not in OFFER_PAGE_SIZES:
        per_page = 100
    if sort_by not in OFFER_SORT_COLUMNS:
        sort_by = "seen"
    if sort_dir not in {"asc", "desc"}:
        sort_dir = "desc"

    base_conditions = []
    if category:
        base_conditions.append("o.category_id = ?")
    if availability == "current":
        base_conditions.append("o.gone_at IS NULL")
    elif availability == "unavailable":
        base_conditions.append("o.gone_at IS NOT NULL")

    category_rows_query = "SELECT o.olx_size_bucket, COUNT(*) AS total FROM offers o"
    if base_conditions:
        category_rows_query += " WHERE " + " AND ".join(base_conditions)
    category_rows_query += " GROUP BY o.olx_size_bucket"
    cursor.execute(category_rows_query, [category] if category else [])
    category_counts = {row["olx_size_bucket"] or "": row["total"] for row in cursor.fetchall()}

    conditions = list(base_conditions)
    params = [category] if category else []
    if size == "unknown":
        conditions.append("(o.olx_size_bucket IS NULL OR TRIM(o.olx_size_bucket) = '')")
    elif size:
        conditions.append("o.olx_size_bucket = ?")
        params.append(profile_by_id[size]["olx_size_value"])
    if status:
        conditions.append("o.system_status = ?")
        params.append(status)
    if q.strip():
        search = f"%{q.strip()}%"
        conditions.append("""(
            o.title LIKE ? COLLATE NOCASE OR o.brand LIKE ? COLLATE NOCASE OR
            o.model LIKE ? COLLATE NOCASE OR o.city LIKE ? COLLATE NOCASE OR
            o.raw_location LIKE ? COLLATE NOCASE
        )""")
        params.extend([search] * 5)

    where_sql = " WHERE " + " AND ".join(conditions) if conditions else ""
    cursor.execute(f"SELECT COUNT(*) AS total FROM offers o{where_sql}", params)
    total = cursor.fetchone()["total"]
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page
    sort_expression = OFFER_SORT_COLUMNS[sort_by]
    sort_order = "ASC" if sort_dir == "asc" else "DESC"

    cursor.execute(
        f"""
        SELECT o.id, o.url, o.title, o.price_pln, o.city, o.district, o.raw_location,
               o.olx_size_bucket, o.detected_size_inches, o.brand, o.model,
               o.technology, o.resolution, o.system_status, o.gone_at, o.last_seen_at,
               o.category_id, o.attributes_json,
               s.score, s.estimated_profit_pln, s.comparison_confidence,
               (SELECT COALESCE(os.main_photo_url, os.listing_thumbnail_url)
                FROM offer_snapshots os
                WHERE os.offer_id = o.id AND COALESCE(os.main_photo_url, os.listing_thumbnail_url) IS NOT NULL
                ORDER BY os.scraped_at DESC, os.id DESC LIMIT 1) AS photo_url
        FROM offers o
        LEFT JOIN offer_scores s ON s.id = (
            SELECT MAX(s2.id) FROM offer_scores s2 WHERE s2.offer_id = o.id
        )
        {where_sql}
        ORDER BY ({sort_expression}) IS NULL ASC, {sort_expression} {sort_order}, o.id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, per_page, offset],
    )
    offers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    status_labels = {value: OFFER_STATUS_LABELS.get(value, value.replace("_", " ").capitalize()) for value in statuses}
    for offer in offers:
        offer["attributes"] = json.loads(offer.get("attributes_json") or "{}")
        profile = profile_by_value.get(offer["olx_size_bucket"])
        bucket_label = profile["label"] if profile else (offer["olx_size_bucket"] or "Nieznany rozmiar")
        if offer["detected_size_inches"]:
            bucket_label += f" · {offer['detected_size_inches']} cali"
        offer["size_label"] = bucket_label if offer["category_id"] == "televisions" else "—"
        offer["status_label"] = "Niedostępna" if offer["gone_at"] else status_labels.get(
            offer["system_status"], offer["system_status"]
        )
        offer["status_class"] = (
            "status-gone" if offer["gone_at"] else
            f"status-{offer['system_status']}" if offer["system_status"] in OFFER_STATUS_LABELS else
            "status-default"
        )
        offer["location_label"] = " · ".join(filter(None, [offer["city"], offer["district"]])) or offer["raw_location"] or "—"
        offer["details_label"] = " · ".join(filter(None, [offer["brand"], offer["model"]])) or "Brak wykrytego modelu"
        if offer["category_id"] == "televisions" and offer["attributes"].get("sale_format") == "bundle_multiple":
            offer["details_label"] += " · zestaw"
        elif offer["category_id"] == "televisions" and offer["attributes"].get("sale_format") == "single_with_accessories":
            offer["details_label"] += " · z dodatkami"
        if offer["category_id"] == "laptops":
            offer["technology_label"] = " · ".join(filter(None, [offer["attributes"].get("cpu"), offer["attributes"].get("gpu")])) or "—"
            offer["details_label"] += (f" · {offer['attributes'].get('ram_gb')} GB RAM" if offer["attributes"].get("ram_gb") else "")
        else:
            offer["technology_label"] = " · ".join(filter(None, [offer["technology"], offer["resolution"]])) or "—"

    query_state = {
        "q": q,
        "category": category,
        "size": size,
        "status": status,
        "availability": availability,
        "per_page": per_page,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
    }
    category_filters = []
    all_categories_count = sum(category_counts.values())
    category_values = [
        ("", "Wszystkie", all_categories_count),
        *[
            (profile["id"], profile["label"], category_counts.get(profile["olx_size_value"], 0))
            for profile in profiles
        ],
        ("unknown", "Nieznany rozmiar", category_counts.get("", 0)),
    ]
    for value, label, count in category_values:
        category_filters.append({
            "value": value,
            "label": label,
            "count": count,
            "active": size == value,
            "url": "/offers?" + urlencode({**query_state, "size": value, "page": 1}),
        })
    previous_url = "/offers?" + urlencode({**query_state, "page": page - 1}) if page > 1 else None
    next_url = "/offers?" + urlencode({**query_state, "page": page + 1}) if page < total_pages else None
    sort_links = {}
    for field in OFFER_SORT_COLUMNS:
        direction = ("asc" if sort_dir == "desc" else "desc") if sort_by == field else "desc"
        sort_links[field] = {
            "url": "/offers?" + urlencode({**query_state, "sort_by": field, "sort_dir": direction, "page": 1}),
            "indicator": ("↑" if sort_dir == "asc" else "↓") if sort_by == field else "↕",
            "aria_sort": "ascending" if sort_by == field and sort_dir == "asc" else "descending" if sort_by == field else "none",
        }
    profile_options = [
        {
            **profile,
            "count": category_counts.get(profile["olx_size_value"], 0),
            "display_label": profile["label"] + (" (wyłączony)" if not profile["enabled"] else ""),
        }
        for profile in profiles
    ]

    return templates.TemplateResponse(
        request=request,
        name="offers.html",
        context={
            "request": request,
            "offers": offers,
            "profiles": profile_options,
            "category_filters": category_filters,
            "statuses": statuses,
            "status_labels": status_labels,
            "category_counts": category_counts,
            "unknown_count": category_counts.get("", 0),
            "q": q,
            "categories": categories,
            "selected_category": category,
            "selected_size": size,
            "selected_status": status,
            "availability": availability,
            "total": total,
            "first_row": offset + 1 if total else 0,
            "last_row": min(offset + per_page, total),
            "page": page,
            "total_pages": total_pages,
            "page_size": per_page,
            "page_sizes": OFFER_PAGE_SIZES,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
            "sort_links": sort_links,
            "previous_url": previous_url,
            "next_url": next_url,
            "active_page": "offers",
            "page_title": "Oferty",
            "page_subtitle": "Ogólnopolska baza ofert · filtruj, porównuj i sortuj",
        },
    )

@app.post("/action/scan")
def run_scan(mode: str = Form(...), profile_id: str = Form(default="")):
    if mode not in ["national", "lodz_alerts"]:
        return RedirectResponse(url="/?error=invalid_mode", status_code=303)
    profile_arg = f" --profile {profile_id}" if re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", profile_id or "") else ""
    run_cli_command(f"scan --mode {mode}{profile_arg}")
    return RedirectResponse(url="/", status_code=303)

@app.post("/action/recalc")
def run_recalc():
    run_cli_command("recalc-market")
    return RedirectResponse(url="/", status_code=303)

@app.post("/action/export")
def run_export(category_id: str = Form(default="")):
    category_arg = f" --category {category_id}" if re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", category_id or "") else ""
    run_cli_command(f"export excel{category_arg}")
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
    categories = service.get_categories()
    search_profiles = service.get_search_profiles()
    
    return templates.TemplateResponse(
        request=request,
        name="settings.html", 
        context={
            "request": request,
            "global_filters": global_filters,
            "scheduler": scheduler,
            "scoring": scoring,
            "categories": categories,
            "search_profiles": search_profiles,
            "active_page": "settings",
            "page_title": "Ustawienia",
            "page_subtitle": "Filtry · profile · scoring · harmonogram",
        }
    )

@app.post("/settings/save")
def save_settings(
    price_min: int = Form(300), price_max: int = Form(700),
    seller_type: str = Form("private"), condition: str = Form("used"),
    national_hours: int = Form(12), lodz_hours: int = Form(2), export_hours: int = Form(2),
    min_discount: float = Form(15.0), min_profit: int = Form(100), min_count: int = Form(3),
    min_score: float = Form(30.0), min_confidence: float = Form(0.7), estimated_costs: int = Form(50),
    suppress_hours: int = Form(24), show_lodz_candidates_min_score: float = Form(0.0)
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
        "estimated_costs": estimated_costs, "suppress_hours": suppress_hours,
        "show_lodz_candidates_min_score": show_lodz_candidates_min_score
    })
    return RedirectResponse(url="/settings", status_code=303)

@app.post("/settings/profile/toggle")
def toggle_profile(profile_id: str = Form(...), enabled: int = Form(...)):
    conn = get_connection()
    conn.execute("UPDATE search_profiles SET enabled = ?, updated_at = datetime('now') WHERE id = ?", (enabled, profile_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/settings", status_code=303)

@app.post("/settings/category/save")
def save_category(
    category_id: str = Form(...), label: str = Form(...), path: str = Form(...),
    allowed_filter_params_json: str = Form("[]"), filter_schema_json: str = Form("[]"),
    attribute_schema_json: str = Form("[]"), scoring_settings_json: str = Form("{}")
):
    if (not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", category_id or "") or not label.strip() or len(label.strip()) > 80
            or not re.fullmatch(r"/(?:[a-z0-9-]+/)+", path or "") or ".." in path):
        return RedirectResponse(url="/settings?error=invalid_category", status_code=303)
    try:
        filter_params = json.loads(allowed_filter_params_json or "[]")
        filter_schema = json.loads(filter_schema_json or "[]")
        attribute_schema = json.loads(attribute_schema_json or "[]")
        scoring_settings = json.loads(scoring_settings_json or "{}")
        if not isinstance(filter_params, list) or any(
            not isinstance(key, str) or not re.fullmatch(r"search\[filter_[a-zA-Z0-9_:-]+\](?:\[\d+\])?", key)
            for key in filter_params
        ):
            raise ValueError("Invalid filter map")
        if not isinstance(filter_schema, list) or any(
            not isinstance(field, dict)
            or field.get("key") not in filter_params
            or not isinstance(field.get("label"), str) or not field.get("label", "").strip() or len(field.get("label", "")) > 100
            or field.get("type", "text") not in {"text", "number", "select"}
            or (field.get("type") == "select" and (not isinstance(field.get("options"), list)
                or any(not isinstance(option, str) for option in field["options"])))
            for field in filter_schema
        ):
            raise ValueError("Invalid filter schema")
        if not isinstance(attribute_schema, list) or any(
            not isinstance(field, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", field)
            for field in attribute_schema
        ):
            raise ValueError("Invalid attribute schema")
        scoring_keys = {"min_discount", "min_profit", "min_count", "min_score", "min_confidence",
                        "estimated_costs", "suppress_hours", "show_lodz_candidates_min_score"}
        if not isinstance(scoring_settings, dict) or not set(scoring_settings).issubset(scoring_keys):
            raise ValueError("Invalid category scoring settings")
        if any(not isinstance(value, (int, float)) for value in scoring_settings.values()):
            raise ValueError("Scoring settings must be numeric")
        SettingsService().save_category(category_id, label.strip(), path, filter_params,
                                        filter_schema, attribute_schema, scoring_settings)
    except (ValueError, json.JSONDecodeError):
        return RedirectResponse(url="/settings?error=invalid_category", status_code=303)
    return RedirectResponse(url="/settings", status_code=303)

@app.post("/settings/profile/save")
def save_search_profile(
    category_id: str = Form(...), profile_id: str = Form(...), label: str = Form(...),
    price_min: int = Form(0), price_max: int = Form(0), query: str = Form(""),
    max_pages: int = Form(5), interval_hours: int = Form(0), mode: str = Form("national"),
    location: str = Form("lodz"), radius_km: int = Form(50), olx_filters_json: str = Form("{}")
):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", profile_id or "") or len(label.strip()) > 100:
        return RedirectResponse(url="/settings?error=invalid_profile", status_code=303)
    try:
        olx_filters = json.loads(olx_filters_json or "{}")
        if not isinstance(olx_filters, dict) or any(
            not isinstance(key, str) or not re.fullmatch(r"search\[filter_[a-zA-Z0-9_:-]+\](?:\[\d+\])?", key)
            for key in olx_filters
        ):
            raise ValueError("Invalid OLX filters")
        if mode not in {"national", "lodz_alerts"}:
            raise ValueError("Invalid search mode")
        if price_min < 0 or price_max < 0 or (price_min and price_max and price_min > price_max):
            raise ValueError("Invalid price range")
        filters = {
            "mode": mode,
            "location": location.strip()[:80] or "lodz",
            "radius_km": max(1, min(int(radius_km), 500)),
            "price_min": price_min or None,
            "price_max": price_max or None,
            "query": query.strip()[:120] or None,
            "olx_filters": olx_filters,
        }
        SettingsService().save_search_profile(profile_id, category_id, label.strip(), filters, max_pages,
                                              interval_hours=interval_hours)
    except (ValueError, json.JSONDecodeError):
        return RedirectResponse(url="/settings?error=invalid_profile", status_code=303)
    return RedirectResponse(url="/settings", status_code=303)

@app.get("/rules")
def get_rules(request: Request):
    import json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM description_rules ORDER BY id DESC")
    rules = [dict(r) for r in cursor.fetchall()]
    conn.close()
    category_labels = {"red_flag": "Czerwona flaga", "warning": "Ostrzeżenie", "positive": "Pozytywna", "info": "Informacja", "exclude": "Wykluczająca"}
    action_labels = {"flag": "Oznacz", "reject": "Odrzuć", "boost": "Podbij ocenę", "info": "Informacja"}
    field_labels = {"title": "Tytuł", "description": "Opis", "parameters": "Parametry", "combined_text": "Tytuł i opis"}
    for rule in rules:
        rule["category_label"] = category_labels.get(rule["category"], rule["category"].replace("_", " ").capitalize())
        rule["action_label"] = action_labels.get(rule["action"], rule["action"].replace("_", " ").capitalize())
        fields = [part.strip() for part in str(rule["applies_to"]).replace(";", ",").split(",") if part.strip()]
        rule["applies_to_label"] = " · ".join(field_labels.get(field, field.capitalize()) for field in fields)
        try:
            patterns = json.loads(rule["patterns_json"] or "[]")
            rule["patterns_label"] = " · ".join(str(pattern) for pattern in patterns)
        except (TypeError, json.JSONDecodeError):
            rule["patterns_label"] = str(rule["patterns_json"] or "—")
    return templates.TemplateResponse(
        request=request,
        name="rules.html",
        context={
            "request": request,
            "rules": rules,
            "active_page": "rules",
            "page_title": "Reguły opisowe",
            "page_subtitle": "Frazy i warunki używane przy ocenie ogłoszeń",
        },
    )

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
