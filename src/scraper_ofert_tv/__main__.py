import sys
import argparse
import json
from pathlib import Path

from scraper_ofert_tv.migrations import apply_migrations
from scraper_ofert_tv.storage import backup_database
from scraper_ofert_tv.settings_service import SettingsService

def run_migrate(args):
    print("Rozpoczynanie migracji...")
    apply_migrations()
    print("Migracje zakonczone pomyslnie.")

def run_backup_db(args):
    print("Rozpoczynanie backupu bazy...")
    backup_path = backup_database()
    if backup_path:
        print(f"Kopia zapasowa utworzona: {backup_path}")
    else:
        print("Nie mozna utworzyc backupu. Plik bazy nie istnieje.")

def run_show_config(args):
    service = SettingsService()
    config = {
        "global_filters": service.get_global_filters(),
        "national_scan": service.get_national_scan_settings(),
        "lodz_alerts": service.get_lodz_alerts_settings(),
        "rate_limit": service.get_rate_limit_settings(),
        "size_profiles": service.get_size_profiles()
    }
    print(json.dumps(config, indent=2, ensure_ascii=False))

from scraper_ofert_tv.scanner import Scanner
from scraper_ofert_tv.detail_worker import DetailWorker
from scraper_ofert_tv.market import recalculate_market
from scraper_ofert_tv.storage import get_connection

def run_scan(args):
    print(f"Uruchamianie skanu, tryb: {args.mode}")
    if args.profile:
        print(f"Wybrany profil: {args.profile}")
    
    scanner = Scanner()
    scanner.run_scan(mode=args.mode, specific_profile=args.profile)
    print("Skan zakonczony.")

from scraper_ofert_tv.export_excel import export_to_excel
from pathlib import Path

def run_export_excel(args):
    print("Rozpoczynanie eksportu do Excela...")
    conn = get_connection()
    output_dir = Path("output")
    export_to_excel(conn, output_dir)
    conn.close()
    print("Pomyślnie wyeksportowano do Excela w folderze output/")

def run_process_details(args):
    print(f"Przetwarzanie detali (limit: {args.limit})...")
    worker = DetailWorker()
    worker.work(limit=args.limit)
    print("Zakonczono przetwarzanie detali.")

from scraper_ofert_tv.scoring import score_offers
from scraper_ofert_tv.alerts import process_alerts

def run_recalc_market(args):
    print("Rozpoczynanie przeliczania bazy referencyjnej cen (recalc-market)...")
    conn = get_connection()
    recalculate_market(conn)
    print("Przeliczanie bazy zakonczone pomyslnie. Rozpoczynanie scoringu...")
    score_offers(conn)
    print("Scoring zakonczony. Generowanie alertow Lodz...")
    process_alerts(conn)
    conn.close()
    print("Generowanie alertow zakonczone.")

def run_test_rules(args):
    print(f"Testowanie regul dla tekstu: '{args.text}'")
    from scraper_ofert_tv.rules import evaluate_rules
    conn = get_connection()
    detail = {"description": args.text, "full_title": args.text}
    matched, actions = evaluate_rules(conn, {}, detail)
    conn.close()
    import json
    print("Dopasowane reguly:", json.dumps(matched, indent=2))
    print("Zastosowane akcje:", actions)

def run_web(args):
    import uvicorn
    print(f"Uruchamianie panelu webowego na {args.host}:{args.port}...")
    uvicorn.run("scraper_ofert_tv.web:app", host=args.host, port=args.port, reload=False)

def main():
    parser = argparse.ArgumentParser(description="Scraper Ofert TV CLI")
    subparsers = parser.add_subparsers(dest="command", help="Dostepne komendy")

    # T201 migrate
    parser_migrate = subparsers.add_parser("migrate", help="Uruchamia migracje bazy danych")
    
    # T202 backup-db
    parser_backup = subparsers.add_parser("backup-db", help="Tworzy kopie zapasowa bazy danych")

    # T203 show-config
    parser_show_config = subparsers.add_parser("show-config", help="Pokazuje aktualna konfiguracje")

    # T204, T205, T206 scan
    parser_scan = subparsers.add_parser("scan", help="Uruchamia proces skanowania")
    parser_scan.add_argument("--mode", required=True, choices=["national", "lodz_alerts"], help="Tryb skanowania")
    parser_scan.add_argument("--profile", help="Opcjonalny ID profilu rozmiaru")

    # T207 export excel
    parser_export = subparsers.add_parser("export", help="Eksportuje raporty")
    parser_export.add_argument("format", choices=["excel"], help="Format eksportu (tylko excel)")

    # process-details
    parser_details = subparsers.add_parser("process-details", help="Pobiera z kolejki detali i przetwarza je")
    parser_details.add_argument("--limit", type=int, default=10, help="Limit cct detal do pobrania (default 10)")

    # T208 recalc-market
    parser_recalc = subparsers.add_parser("recalc-market", help="Przelicza grupowanie i mediany referencyjne")

    # T209 test-rules
    parser_test_rules = subparsers.add_parser("test-rules", help="Testuje dzialanie regul na tekscie")
    parser_test_rules.add_argument("--text", required=True, help="Tekst (tytul i opis) do przetestowania")

    # T210 web
    parser_web = subparsers.add_parser("web", help="Uruchamia panel webowy")
    parser_web.add_argument("--host", default="127.0.0.1", help="Host nasluchiwania")
    parser_web.add_argument("--port", type=int, default=8000, help="Port nasluchiwania")

    # scheduler
    parser_scheduler = subparsers.add_parser("scheduler", help="Uruchamia proces w tle dla zadan cyklicznych")

    args = parser.parse_args()

    if args.command == "migrate":
        run_migrate(args)
    elif args.command == "backup-db":
        run_backup_db(args)
    elif args.command == "show-config":
        run_show_config(args)
    elif args.command == "scan":
        run_scan(args)
    elif args.command == "export":
        run_export_excel(args)
    elif args.command == "process-details":
        run_process_details(args)
    elif args.command == "recalc-market":
        run_recalc_market(args)
    elif args.command == "test-rules":
        run_test_rules(args)
    elif args.command == "web":
        run_web(args)
    elif args.command == "scheduler":
        from scraper_ofert_tv.scheduler import start_scheduler
        start_scheduler()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
