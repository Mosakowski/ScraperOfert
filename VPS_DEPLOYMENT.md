# MVP na VPS

## Co musi zapewnić serwer

- Linux z Pythonem, `venv` i Git; użytkownik systemowy z prawem zapisu do katalogów `data/`, `output/` i `debug/`.
- Trwały dysk na `data/offers.sqlite` oraz raporty. Nie uruchamiaj aplikacji z katalogu tymczasowego.
- Wyjście HTTPS do publicznych stron OLX. Wynik pobierania z IP VPS trzeba potwierdzić próbą; lokalny sukces nie dowodzi, że serwer nie dostanie 403, CAPTCHA lub timeoutu.
- Dwa stale uruchomione procesy: panel `web` i `scheduler` (np. dwie jednostki systemd). Baza jest wspólna dla obu.
- Jeśli ustawienie `scraper_settings.fetch_backend` ma wartość `playwright`: Chromium i jego zależności systemowe. Dla domyślnego `httpx` przeglądarka nie jest potrzebna.
- Dostęp do panelu tylko przez VPN/tunel albo reverse proxy z HTTPS i uwierzytelnianiem. Wbudowany panel nie ma logowania. Nie wystawiaj portu 8000 publicznie.
- Backup bazy i okresowy test odtworzenia, logi usług oraz miejsce na pliki diagnostyczne.

Docker, PostgreSQL, domena i zewnętrzne powiadomienia nie są wymagane do tego MVP. Rozmiar VPS dobierz po pomiarze zużycia podczas pełnego przebiegu, szczególnie jeśli używasz Chromium.

## Instalacja przykładowa na Ubuntu

W poniższym przykładzie kod jest w `/opt/scraper-ofert-tv`, a usługi działają jako użytkownik `scrapertv`. Utwórz tego użytkownika i katalog z odpowiednimi prawami. Następnie, jako ten użytkownik:

```bash
cd /opt/scraper-ofert-tv
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m scraper_ofert_tv migrate
```

Jeśli w bazie wybierzesz backend `playwright`, zainstaluj też przeglądarkę i biblioteki systemowe zgodnie z [instrukcją Playwright](https://playwright.dev/python/docs/browsers):

```bash
.venv/bin/python -m playwright install --with-deps chromium
```

Instalacja zależności systemowych może wymagać uprawnień administratora. Przeglądarkę zainstaluj dla tego samego użytkownika, który uruchamia scraper.

## Procesy i pierwszy przebieg

Skonfiguruj dwie jednostki systemd z `WorkingDirectory=/opt/scraper-ofert-tv`, `User=scrapertv` i `Restart=on-failure`. Ich polecenia `ExecStart`:

```text
/opt/scraper-ofert-tv/.venv/bin/python -m scraper_ofert_tv web --host 127.0.0.1 --port 8000
/opt/scraper-ofert-tv/.venv/bin/python -m scraper_ofert_tv scheduler
```

Jednostki uruchom i włącz do startu systemu. Obserwuj ich logi w `journalctl`. Scheduler czeka na pierwszy interwał, dlatego pierwszy pełny przebieg uruchom ręcznie w katalogu projektu:

```bash
.venv/bin/python -m scraper_ofert_tv scan --mode national
.venv/bin/python -m scraper_ofert_tv process-details --limit 100
.venv/bin/python -m scraper_ofert_tv recalc-market
.venv/bin/python -m scraper_ofert_tv scan --mode lodz_alerts
.venv/bin/python -m scraper_ofert_tv process-details --limit 50 --mode lodz_alerts
.venv/bin/python -m scraper_ofert_tv recalc-market
.venv/bin/python -m scraper_ofert_tv export excel
```

Nie uruchamiaj tego przebiegu równocześnie z zaplanowanym skanem. Sprawdź statusy przebiegów i liczbę ofert, zadania `pending`/`failed` w `details_queue`, dane porównawcze oraz plik `output/oferty_olx_latest.xlsx` (alias zgodności TV: `oferty_tv_latest.xlsx`). Brak alertów może wynikać z progów i danych; sam w sobie nie dowodzi awarii. Blokadę OLX lub CAPTCHA traktuj jako warunek zatrzymania i diagnostyki, bez obchodzenia zabezpieczeń.

Panel uruchamia skan list w osobnym procesie; pobranie detali i wycena następują w cyklu schedulera albo po ręcznym uruchomieniu powyższych komend. Zmiana interwałów w panelu wymaga restartu schedulera.

## Dane i backup

`data/offers.sqlite` jest źródłem prawdy. Wszystkie polecenia i usługi muszą używać tego samego katalogu roboczego, ponieważ ścieżki bazy, raportów i diagnostyki są względne. Nie przenoś tylko pliku XLSX jako kopii danych.

Obecna komenda `backup-db` używa zwykłego kopiowania pliku. Zaplanuj ją poza pracą procesów zapisujących bazę albo zatrzymaj te procesy na czas kopii; po backupie sprawdź odtworzenie w odosobnionym katalogu. Do kopii bez przestoju potrzebna jest zmiana implementacji na API backupu SQLite. Przechowuj kopie poza VPS, jeśli dane mają przetrwać awarię dysku lub serwera.
