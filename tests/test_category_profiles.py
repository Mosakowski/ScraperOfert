import json
import sqlite3
import urllib.parse

import openpyxl

from scraper_ofert_tv.comparison import generate_comparable_keys
from scraper_ofert_tv.export_excel import export_to_excel
from scraper_ofert_tv.alerts import process_alerts
from scraper_ofert_tv.backfill import run_backfill
from scraper_ofert_tv.migrations import apply_migrations
from scraper_ofert_tv.normalization import normalize_offer_data
from scraper_ofert_tv.olx_urls import build_olx_search_url
from scraper_ofert_tv.rules import evaluate_rules
from scraper_ofert_tv.settings_service import SettingsService
from scraper_ofert_tv.storage import now_iso


def _connection(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def test_category_profiles_and_filter_schema_round_trip(tmp_path):
    db_path = tmp_path / "categories.sqlite"
    apply_migrations(db_path)
    service = SettingsService(db_path)
    service.save_category(
        "printers", "Drukarki", "/elektronika/drukarki/",
        ["search[filter_enum_brand][0]"],
        [{"key": "search[filter_enum_brand][0]", "label": "Marka", "type": "select", "options": ["HP", "Canon"]}],
        ["brand", "print_technology"], {"min_count": 4, "estimated_costs": 70},
    )
    service.save_search_profile(
        "printers_hp", "printers", "Drukarki HP",
        {"mode": "national", "olx_filters": {"search[filter_enum_brand][0]": "HP"}},
        max_pages=8,
    )

    categories = {row["id"]: row for row in service.get_categories()}
    assert categories["printers"]["filter_schema"][0]["options"] == ["HP", "Canon"]
    assert categories["printers"]["attribute_schema"] == ["brand", "print_technology"]
    assert service.get_scoring_settings("printers")["estimated_costs"] == 70
    profile = next(row for row in service.get_search_profiles() if row["id"] == "printers_hp")
    assert profile["category_path"] == "/elektronika/drukarki/"
    assert profile["filters"]["olx_filters"]["search[filter_enum_brand][0]"] == "HP"
    assert service.get_size_profiles() and len(service.get_size_profiles()) == 7


def test_category_profile_rejects_undeclared_olx_filters(tmp_path):
    db_path = tmp_path / "invalid-filter.sqlite"
    apply_migrations(db_path)
    service = SettingsService(db_path)
    try:
        service.save_search_profile(
            "bad", "laptops", "Bad", {"olx_filters": {"search[filter_enum_brand][0]": "HP"}}
        )
    except ValueError as exc:
        assert "filtra" in str(exc).lower()
    else:
        raise AssertionError("An undeclared category filter must be rejected")


def test_category_profile_rejects_filter_values_outside_schema(tmp_path):
    db_path = tmp_path / "invalid-option.sqlite"
    apply_migrations(db_path)
    service = SettingsService(db_path)
    try:
        service.save_search_profile(
            "bad_value", "laptops", "Bad option",
            {"olx_filters": {"search[filter_enum_ramsize_laptops][0]": "999gb"}},
        )
    except ValueError as exc:
        assert "wartość" in str(exc).lower()
    else:
        raise AssertionError("A select value outside the category schema must be rejected")


def test_category_url_builds_path_filters_location_and_pagination():
    url = build_olx_search_url(
        mode="lodz_alerts", location="lodz", radius_km=25, price_min=500, price_max=2000,
        category_path="/elektronika/komputery/laptopy/", query="ThinkPad T14",
        olx_filters={"search[filter_enum_brand][0]": "Lenovo"}, page=3,
    )
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    assert parsed.path == "/elektronika/komputery/laptopy/lodz/"
    assert params["search[filter_float_price:from]"] == ["500"]
    assert params["search[filter_float_price:to]"] == ["2000"]
    assert params["search[dist]"] == ["25"]
    assert params["search[filter_enum_brand][0]"] == ["Lenovo"]
    assert params["q"] == ["ThinkPad T14"]
    assert params["page"] == ["3"]


def test_laptop_normalization_creates_typed_attributes_and_category_keys():
    offer = {"title": "Lenovo ThinkPad T14 i7 16GB RAM 512GB SSD 14,0 cala", "raw_price": "2 500 zł",
             "raw_location": "Łódź"}
    detail = {"full_title": offer["title"], "description": "Laptop sprawny", "raw_price": "2 500 zł",
              "params": {"Marka": "Lenovo", "Model": "ThinkPad T14", "Procesor": "Intel Core i7-1165G7",
                         "Pamięć RAM": "16 GB", "Dysk": "512 GB SSD", "Przekątna ekranu": "14,0 cala",
                         "Stan": "Używane"}}
    normalized = normalize_offer_data(offer, detail, category_id="laptops")
    assert normalized["price_pln"] == 2500
    assert normalized["brand"] == "lenovo"
    assert normalized["attributes"]["ram_gb"] == 16
    assert normalized["attributes"]["storage_gb"] == 512
    assert normalized["attributes"]["screen_inches_tenths"] == 140
    assert normalized["attributes"]["condition"] == "used"
    assert normalized["diagnostics"]["ram_source"] == "params"
    keys = generate_comparable_keys({
        "brand": normalized["brand"], "model_name": normalized["model_name"],
        "attributes": normalized["attributes"],
    }, category_id="laptops")
    assert keys["A"].startswith("laptops|model|")
    changed = {"brand": normalized["brand"], "model_name": normalized["model_name"],
               "attributes": {**normalized["attributes"], "condition": "new"}}
    assert generate_comparable_keys(changed, category_id="laptops")["A"] != keys["A"]


def test_product_rules_do_not_cross_categories(tmp_path):
    db_path = tmp_path / "rules.sqlite"
    apply_migrations(db_path)
    conn = _connection(db_path)
    detail = {"full_title": "Bateria do laptop na części", "description": "Bateria do laptopa na części"}
    _, laptop_actions = evaluate_rules(conn, {}, detail, category_id="laptops")
    _, tv_actions = evaluate_rules(conn, {}, detail, category_id="televisions")
    assert "reject" in laptop_actions
    assert "reject" not in tv_actions
    conn.close()


def test_alert_thresholds_are_scoped_to_product_category(tmp_path):
    db_path = tmp_path / "category-alerts.sqlite"
    apply_migrations(db_path)
    conn = _connection(db_path)
    now = now_iso()
    conn.execute("UPDATE categories SET scoring_settings_json=? WHERE id='televisions'", (json.dumps({"min_score": 90}),))
    conn.execute("UPDATE categories SET scoring_settings_json=? WHERE id='laptops'", (json.dumps({"min_score": 10}),))
    for offer_id, category_id in ((11, "televisions"), (12, "laptops")):
        conn.execute("""
            INSERT INTO offers (id, source, url, url_hash, title, category_id, system_status, city,
                                first_seen_at, last_seen_at, created_at, updated_at)
            VALUES (?, 'olx', ?, ?, ?, ?, 'opportunity', 'Łódź', ?, ?, ?, ?)
        """, (offer_id, f"https://olx.pl/{offer_id}", f"h{offer_id}", f"Oferta {offer_id}",
              category_id, now, now, now, now))
        conn.execute("""
            INSERT INTO offer_scores (offer_id, score, system_status, reference_price_pln,
                estimated_profit_pln, market_discount_percent, comparable_offers_count,
                comparison_confidence, scoring_reasons_json, calculated_at)
            VALUES (?, 50, 'opportunity', 1000, 300, 30, 5, '0.9', '[]', ?)
        """, (offer_id, now))
    conn.commit()

    process_alerts(conn)
    alert_ids = [row[0] for row in conn.execute("SELECT offer_id FROM alert_events")]
    assert alert_ids == [12]
    conn.close()


def test_category_export_contains_only_selected_category(tmp_path):
    db_path = tmp_path / "export.sqlite"
    apply_migrations(db_path)
    conn = _connection(db_path)
    now = now_iso()
    for offer_id, category_id, title in ((1, "televisions", "TV sample"), (2, "laptops", "Laptop sample")):
        conn.execute("""
            INSERT INTO offers (id, source, url, url_hash, title, category_id, first_seen_at,
                                last_seen_at, created_at, updated_at)
            VALUES (?, 'olx', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (offer_id, f"https://olx.pl/{offer_id}", f"hash{offer_id}", title,
              category_id, now, now, now, now))
    conn.commit()
    output = tmp_path / "output"
    export_to_excel(conn, output, category_id="laptops")
    path = output / "oferty_olx_laptops_latest.xlsx"
    assert path.exists()
    sheet = openpyxl.load_workbook(path)["Oferty"]
    titles = [sheet.cell(row, 4).value for row in range(2, sheet.max_row + 1)]
    assert titles == ["Laptop sample"]
    assert not (output / "oferty_tv_latest.xlsx").exists()
    conn.close()


def test_v3_database_upgrade_adds_category_schemas(tmp_path):
    db_path = tmp_path / "upgrade.sqlite"
    apply_migrations(db_path)
    conn = _connection(db_path)
    conn.execute("DELETE FROM schema_migrations WHERE version=4")
    for column in ("filter_schema_json", "attribute_schema_json", "scoring_settings_json"):
        conn.execute(f"ALTER TABLE categories DROP COLUMN {column}")
    conn.commit()
    conn.close()

    apply_migrations(db_path)
    conn = _connection(db_path)
    versions = [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
    assert versions == [1, 2, 3, 4]
    category = conn.execute("SELECT filter_schema_json FROM categories WHERE id='televisions'").fetchone()
    assert json.loads(category[0])[0]["key"] == "search[filter_enum_size][0]"
    conn.close()


def test_backfill_uses_category_normalization_and_attributes_json(tmp_path):
    db_path = tmp_path / "backfill.sqlite"
    apply_migrations(db_path)
    conn = _connection(db_path)
    now = now_iso()
    conn.execute("""
        INSERT INTO offers (id, source, url, url_hash, title, category_id, raw_price, first_seen_at,
                            last_seen_at, created_at, updated_at)
        VALUES (1, 'olx', 'https://olx.pl/d/oferta/1', 'hash1', 'HP ZBook 14 G6 16GB',
                'laptops', '1099 zł', ?, ?, ?, ?)
    """, (now, now, now, now))
    conn.execute("""
        INSERT INTO offer_snapshots (offer_id, category_id, scan_mode, title, description, params_json, scraped_at)
        VALUES (1, 'laptops', 'detail_fetch', 'HP ZBook 14 G6 16GB', 'Sprawny', ?, ?)
    """, (json.dumps({"Marka": "HP", "Seria procesora": "Intel Core i5", "Wielkość pamięci RAM": "16GB"}), now))
    conn.commit()
    conn.close()

    run_backfill(db_path)
    conn = _connection(db_path)
    row = conn.execute("SELECT category_id, attributes_json, comparable_key, condition_value FROM offers WHERE id=1").fetchone()
    attrs = json.loads(row["attributes_json"])
    assert row["category_id"] == "laptops"
    assert attrs["ram_gb"] == 16
    assert row["comparable_key"].startswith("laptops|model|")
    conn.close()
