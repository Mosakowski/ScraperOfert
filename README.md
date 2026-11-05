# Scraper Ofert TV

Zaawansowany scraper ofert telewizorow oparty na lokalnej architekturze zintegrowanej z baza SQLite. Pozwala na automatyczne wyszukiwanie ofert na terenie calego kraju, grupowanie ich pod katem modeli (tworzac swoista gielde cenowa) oraz wypatrywanie lokalnych, łódzkich okazji zakupowych dla zysku (flipowanie).

Docelowym produktem jest uniwersalny system dla różnych kategorii ofert. Obecna wersja obsługuje telewizory z OLX jako pierwszą kategorię. Plan rozszerzenia jest w [PRD.md](PRD.md) i [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md); wybór innych kategorii nie jest jeszcze zaimplementowany.

## Instalacja lokalna
1. Pobierz repozytorium.
2. Zbuduj i zainstaluj srodowisko w trybie deweloperskim (lub standardowym):
   ```bash
   pip install -e .
   ```
   (Zależności to m.in. `fastapi`, `uvicorn`, `selectolax`, `httpx`, `openpyxl`, `schedule`, `jinja2`).

3. Zbuduj czystą bazę danych i dodaj seedy konfiguracyjne:
   ```bash
   python -m scraper_ofert_tv migrate
   # Jeśli 'python' nie jest w PATH na systemie Windows, użyj:
   # py -m scraper_ofert_tv migrate
   ```

## Przeplyw pracy (Workflow)
Sugerowany i w pełni działający na czystej bazie danych workflow (od bazy, az po raport Excela):
1. **national**: `python -m scraper_ofert_tv scan --mode national` (pobiera linki ogolnopolskie).
2. **process-details**: `python -m scraper_ofert_tv process-details` (techniczna komenda, ktora 'konsumuje' oferty z kolejki, sciaga z nich detale jak konkretny model czy uszkodzenia).
3. **recalc-market**: `python -m scraper_ofert_tv recalc-market` (najwazniejszy element: agreguje pobrane oferty i wystawia mediany na dany klucz porownawczy; pod spodem uruchamia rowniez logiczny *scoring* oraz *alerty Lodz*).
4. **lodz_alerts**: `python -m scraper_ofert_tv scan --mode lodz_alerts` (pobiera baze lokalna Lodzi, by nastepnie 'process-details' i 'recalc-market' wylapaly ja jako szybki alert).
5. **export excel**: `python -m scraper_ofert_tv export excel` (generuje estetyczny plik w folderze `output/`).

## Komendy CLI
Aplikacja udostępnia interfejs pod komendą `python -m scraper_ofert_tv <komenda>` (na systemie Windows można również użyć `py -m scraper_ofert_tv <komenda>` jeśli domyślny Python nie jest w zmiennych środowiskowych):

- `migrate` - buduje schemat bazy w `data/offers.sqlite`
- `scan --mode [national|lodz_alerts]` - listuje wyniki i sciaga kafelki do bazy
- `process-details --limit 50` - wyciaga detale oczekujacych ofert. Uzywana jako techniczny worker kolejkowy (odseparowuje liste linkow od blokujacego rate-limit pobierania strony przedmiotu).
- `recalc-market` - przelicza grupowanie cen i aktywuje modul oceny.
- `export excel` - buduje fizycznego excela.
- `web --host 127.0.0.1 --port 8000` - włącza panel WWW
- `scheduler` - odpala prosty system zaplanowanych zadan.
- `backup-db` - tworzy kopie zapasowa SQLite (folder `data/backups/`).

## Uruchomienie na VPS (Local / MVP VPS)
Kompletna instrukcja: [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md). Potrzebne są Python i `venv`, Git, dostęp HTTPS do publicznych stron OLX, trwały dysk na SQLite i raporty oraz dwa stale uruchomione procesy: `web` i `scheduler`. Przy backendzie Playwright trzeba osobno zainstalować Chromium i jego biblioteki systemowe. Panel nie ma własnego logowania, więc przed dostępem z internetu należy ograniczyć dostęp przez reverse proxy, VPN albo tunel.

Oba procesy muszą mieć ten sam katalog roboczy: aplikacja używa względnych ścieżek `data/offers.sqlite`, `output/` i `debug/`. Scheduler odczytuje interwały przy starcie i nie uruchamia pierwszego cyklu od razu; po zmianie interwałów wymaga restartu. Backup oraz próba odtworzenia bazy są osobnymi zadaniami operatora.

## Co oznaczają zadania detali

Skan list wyników zapisuje podstawowe dane oferty i dodaje zadanie do tabeli `details_queue`. Worker `process-details` otwiera stronę konkretnego ogłoszenia, pobiera opis i parametry, normalizuje model, stosuje reguły i zapisuje wynik. Zadania `pending` czekają na pobranie, `processing` są w trakcie, `done` zostały obsłużone, a `failed` wyczerpały próby. Samo znalezienie oferty na liście nie oznacza jeszcze, że można ją rzetelnie wycenić. Komenda `python -m scraper_ofert_tv process-details --limit 50` przetwarza maksymalnie 50 oczekujących wpisów; cykle schedulera pobierają odpowiednio do 100 i 50 zadań. Opcja `--mode lodz_alerts` daje pierwszeństwo ofertom łódzkim, ale nie ogranicza kolejki wyłącznie do nich. Przy dużym napływie ofert kolejka może rosnąć.

## Kopia zapasowa SQLite
Zawsze nalezy wykonywac kopię przed poważnymi zmianami. Baza `data/offers.sqlite` jest źródłem prawdy, a Excel jest raportem. Obecna komenda `backup-db` kopiuje plik SQLite bez użycia API backupu SQLite; na serwerze wykonuj ją przy zatrzymanych procesach zapisujących bazę i sprawdź odtworzenie kopii. Harmonogram backupu nie jest uruchamiany automatycznie przez aplikację.

## Definicja MVP
MVP to Minimal Viable Product - scraper obsluguje wstepne testy wyceny, nie zaciaga danych wrazliwych, jest rate-limitowany by nie spamowac OLX-a, a reguly mozna testowac za pomoca modulu CLI badz wpisow JSON/bazy SQLite. Panel webowy wyswietla surowe agregaty dzialan.
