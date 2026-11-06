import time
import schedule
import logging
from scraper_ofert_tv.scanner import Scanner
from scraper_ofert_tv.detail_worker import DetailWorker
from scraper_ofert_tv.storage import get_connection
from scraper_ofert_tv.market import recalculate_market
from scraper_ofert_tv.scoring import score_offers
from scraper_ofert_tv.alerts import process_alerts
from scraper_ofert_tv.export_excel import export_to_excel
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_workflow_national():
    logger.info("Rozpoczynanie cyklu 'national'")
    try:
        # Skan list
        scanner = Scanner()
        scanner.run_scan(mode='national')
        
        # Pobranie szczegolow dla znalezionych w kolejce
        worker = DetailWorker()
        worker.work(limit=100) # Pobierz np. 100 max detali w cyklu
        
        # Przeliczanie bazy i scoring
        conn = get_connection()
        recalculate_market(conn)
        score_offers(conn)
        conn.close()
        logger.info("Zakonczono cykl 'national'")
    except Exception as e:
        logger.error(f"Blad w cyklu national: {e}")

def run_workflow_lodz():
    logger.info("Rozpoczynanie cyklu 'lodz_alerts'")
    try:
        scanner = Scanner()
        scanner.run_scan(mode='lodz_alerts')
        
        worker = DetailWorker()
        worker.work(limit=50)
        
        conn = get_connection()
        # Tylko oceniamy nowosci lodzkie i sprawdzamy alerty, bez przeliczania median
        score_offers(conn)
        process_alerts(conn)
        conn.close()
        logger.info("Zakonczono cykl 'lodz_alerts'")
    except Exception as e:
        logger.error(f"Blad w cyklu lodz: {e}")

def run_export():
    logger.info("Rozpoczynanie automatycznego eksportu Excel")
    try:
        conn = get_connection()
        output_dir = Path("output")
        export_to_excel(conn, output_dir)
        conn.close()
        logger.info("Zakonczono automatyczny eksport Excel")
    except Exception as e:
        logger.error(f"Blad w cyklu export: {e}")

def run_workflow_profile(profile_id: str):
    logger.info("Uruchamiam profil monitorowania: %s", profile_id)
    try:
        Scanner().run_scan(mode="national", specific_profile=profile_id)
        DetailWorker().work(limit=100)
        conn = get_connection()
        recalculate_market(conn)
        score_offers(conn)
        process_alerts(conn)
        export_to_excel(conn, Path("output"))
        conn.close()
    except Exception:
        logger.exception("Błąd profilu monitorowania %s", profile_id)

def start_scheduler():
    from scraper_ofert_tv.settings_service import SettingsService
    service = SettingsService()
    sched_settings = service.get_setting("scheduler", {"national_hours": 12, "lodz_hours": 2, "export_hours": 2})
    active_profiles = service.get_search_profiles(enabled_only=True)
    
    n_hours = sched_settings.get("national_hours", 12)
    l_hours = sched_settings.get("lodz_hours", 2)
    e_hours = sched_settings.get("export_hours", 2)
    
    logger.info(f"Uruchamianie schedulera. Czasy: national={n_hours}h, lodz={l_hours}h, export={e_hours}h.")
    
    if active_profiles:
        scheduled = 0
        for profile in active_profiles:
            profile_mode = (profile.get("filters") or {}).get("mode", "national")
            inherited_interval = l_hours if profile_mode == "lodz_alerts" else n_hours
            interval = int(profile.get("interval_hours") or inherited_interval)
            if interval > 0:
                schedule.every(interval).hours.do(run_workflow_profile, profile["id"])
                scheduled += 1
        if e_hours > 0 and not scheduled:
            schedule.every(e_hours).hours.do(run_export)
        logger.info("Włączono harmonogram dla %s z %s aktywnych profili.", scheduled, len(active_profiles))
    else:
        if n_hours > 0:
            schedule.every(n_hours).hours.do(run_workflow_national)
        if l_hours > 0:
            schedule.every(l_hours).hours.do(run_workflow_lodz)
        if e_hours > 0:
            schedule.every(e_hours).hours.do(run_export)

    logger.info("Scheduler aktywny, nacisnij Ctrl+C aby przerwac.")
    while True:
        schedule.run_pending()
        time.sleep(1)
