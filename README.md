# Scraper Ofert TV

Zaawansowany scraper ofert telewizorow oparty na lokalnej architekturze zintegrowanej z baza SQLite. Pozwala na automatyczne wyszukiwanie ofert na terenie calego kraju, grupowanie ich pod katem modeli (tworzac swoista gielde cenowa) oraz wypatrywanie lokalnych, łódzkich okazji zakupowych dla zysku (flipowanie).

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
Z racji wbudowanego `scheduler` (uruchamianego z terminala za pomoca menedzera zadan, np. PM2, Supervisor lub nohup), wystarczy zaledwie kilka kroków. Należy jednak pamiętać, że aplikacja jest na etapie MVP, co oznacza, że taki serwer VPS służy do izolacji działania z dala od domowego komputera, ale z założenia nie dysponuje pełnym monitoringiem w środowisku czysto "produkcyjnym".

1. Sklonowac srodowisko na linuxowego serwera (np. Ubuntu).
2. Wywolac `python -m scraper_ofert_tv migrate`.
3. Odpal deamon w tle z uzyciem komendy `python -m scraper_ofert_tv scheduler` (np. przez Supervisor). Osobno mozna wystawic sam interfejs panelu poleceniem `python -m scraper_ofert_tv web` (i wpuscic za rewers proxy, np. Nginx), aby miec staly dostep do podgladu i ustawien. **Uwaga:** W przypadku zmiany interwałów czasowych dla pętli w panelu webowym, aby ustawienia zaczęły działać należy manualnie zrestartować proces `scheduler`!
4. Backup bazy wykonuje sie zlecajac w crontabie: `0 3 * * * python -m scraper_ofert_tv backup-db`.

## Kopia zapasowa SQLite
Zawsze nalezy wykonywac `python -m scraper_ofert_tv backup-db` przed probami powaznych ingerencji lub updatow. Baza znajduje sie w `data/offers.sqlite` - nie jest ona formatem tymczasowym. Stanowi zrodlo prawdy calego systemu. Wygenerowany Excel z alertami wyciaga dane wprost z relacyjnych zlaczen, a nie logiki pamieciowej.

## Definicja MVP
MVP to Minimal Viable Product - scraper obsluguje wstepne testy wyceny, nie zaciaga danych wrazliwych, jest rate-limitowany by nie spamowac OLX-a, a reguly mozna testowac za pomoca modulu CLI badz wpisow JSON/bazy SQLite. Panel webowy wyswietla surowe agregaty dzialan.
