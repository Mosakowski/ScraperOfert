# Implementation Plan - Scraper Ofert TV

Ten dokument opisuje techniczny plan wykonania MVP. PRD.md pozostaje zrodlem prawdy produktowej, a ten plik przeklada wymagania na kolejnosc prac, moduly i kryteria ukonczenia.

Docelowo aplikacja ma obsługiwać wiele kategorii. Etapy poniżej wdrażają pierwszą z nich, telewizory, i nie oznaczają, że model produktu jest ograniczony do TV.

## Ścieżka rozszerzenia po MVP

1. Dodać identyfikator kategorii do oferty, profilu wyszukiwania i grupy porównawczej oraz migrować istniejące rekordy jako `telewizory`.
2. Wydzielić konfigurację adresów, filtrów i profili wyszukiwania dla kategorii; obecny filtr przekątnej pozostaje konfiguracją TV.
3. Wydzielić normalizację parametrów, budowanie klucza porównania i reguły zależne od kategorii. Kolejka, zapis historii, harmonogram i pobieranie stron mogą pozostać wspólne.
4. W panelu i eksporcie dodać wybór kategorii oraz odrębne ustawienia progów. Porównania cen i alerty muszą działać w obrębie jednej kategorii.
5. Potwierdzić podział testami na drugiej kategorii, zanim system zostanie określony jako wielokategorialny.

To rozszerzenie istniejącego przepływu, bez potrzeby przepisywania całego scrapera. Szczegóły parametrów drugiej kategorii zostaną ustalone przy jej wyborze.

## 1. Zasady implementacji

- Budujemy MVP, nie pelny system produkcyjny.
- Stack startowy: Python, FastAPI, httpx, selectolax, SQLite, openpyxl.
- Jedna aplikacja i jedno repozytorium, bez mikroserwisow.
- SQLite jest zrodlem prawdy. Excel jest raportem generowanym z bazy.
- Panel webowy jest glownym miejscem edycji ustawien, regul i progow.
- CLI sluzy do uruchomien technicznych, migracji, eksportow i pracy na serwerze.
- Scraper pobiera publiczne strony OLX, bez logowania i bez danych kontaktowych.
- System ma retry, backoff, cooldown i kolejke, ale nie implementuje lamania CAPTCHA ani obchodzenia prywatnych obszarow.
- Najpierw stabilnosc danych i parserow, potem automatyzacja i ladny panel.

## 2. Docelowe moduly

Kod aplikacji powinien byc podzielony na moduly:

- `cli.py` - komendy terminalowe.
- `web.py` - FastAPI, panel webowy i akcje administracyjne.
- `config.py` - ustawienia startowe, import/export ustawien.
- `settings_service.py` - odczyt i zapis ustawien z bazy.
- `storage.py` - dostep do SQLite.
- `migrations.py` - migracje bazy danych.
- `olx_urls.py` - budowanie URL-i wyszukiwania OLX.
- `listing_scraper.py` - pobieranie stron wynikow.
- `listing_parser.py` - parser list wynikow.
- `detail_scraper.py` - pobieranie stron ofert.
- `detail_parser.py` - parser szczegolow ofert.
- `details_queue.py` - kolejka pobierania szczegolow.
- `normalization.py` - normalizacja ceny, marki, modelu, rozmiaru, lokalizacji.
- `comparison.py` - tworzenie `comparable_key` i pewnosc dopasowania.
- `market.py` - baza cen ogolnopolskich.
- `rules.py` - reguly opisowe.
- `scoring.py` - scoring, statusy i profit.
- `alerts.py` - logika alertow Lodz.
- `export_excel.py` - raport Excel.
- `scheduler.py` - cykliczne uruchomienia.
- `rate_limiter.py` - opoznienia, jitter, backoff, cooldown.

## 3. Etap 0 - Przygotowanie projektu

Cel: utworzyc minimalny szkielet aplikacji.

Zakres:

- Utworzyc strukture katalogow `src/scraper_ofert_tv/`, `tests/`, `data/`, `output/`, `logs/`, `config/`.
- Dodac pliki konfiguracyjne projektu Python.
- Dodac zaleznosci: FastAPI, uvicorn, httpx, selectolax, openpyxl, PyYAML, pytest.
- Dodac entrypoint CLI: `python -m scraper_ofert_tv`.
- Dodac README z podstawowymi komendami.

Kryteria ukonczenia:

- Projekt instaluje sie lokalnie.
- Dziala komenda `python -m scraper_ofert_tv --help`.
- Testy uruchamiaja sie komenda `pytest`.

## 4. Etap 1 - Baza danych i migracje

Cel: stworzyc stabilny fundament danych.

Zakres:

- Zaimplementowac SQLite pod sciezka `data/offers.sqlite`.
- Dodac proste migracje wersjonowane.
- Utworzyc tabele opisane w DB_SCHEMA.md.
- Dodac warstwe `storage.py` z funkcjami CRUD potrzebnymi w MVP.
- Dodac backup bazy do `data/backups/`.

Kryteria ukonczenia:

- `python -m scraper_ofert_tv migrate` tworzy baze od zera.
- Ponowne uruchomienie migracji jest bezpieczne.
- `python -m scraper_ofert_tv backup-db` tworzy kopie bazy.
- Testy sprawdzaja deduplikacje po OLX ID i canonical URL.

## 5. Etap 2 - Ustawienia i profile

Cel: ustawienia maja byc dostepne z bazy i przygotowane pod panel.

Zakres:

- Dodac domyslne ustawienia globalne: cena 300-700 PLN, prywatne, uzywane.
- Dodac profile rozmiarow OLX.
- Dodac ustawienia trybow `national` i `lodz_alerts`.
- Dodac ustawienia rate limit, scoringu i alertow.
- Dodac seed danych startowych.
- Dodac import/export YAML jako funkcje techniczne.

Kryteria ukonczenia:

- Po migracji baza zawiera domyslne ustawienia.
- `show-config` pokazuje ustawienia z bazy.
- Zmiana ustawien nie wymaga edycji Excela.

## 6. Etap 3 - Budowanie URL-i OLX

Cel: generowac poprawne URL-e wyszukiwania dla kazdego profilu.

Zakres:

- Zaimplementowac `olx_urls.py`.
- Obslugiwac tryb `national`.
- Obslugiwac tryb `lodz_alerts` z lokalizacja Lodz i promieniem.
- Dodac parametry: cena, prywatne, uzywane, rozmiar TV, strona wynikow.
- Zapewnic zachowanie filtrow przy paginacji.

Kryteria ukonczenia:

- Testy potwierdzaja URL-e dla wszystkich profili rozmiarow.
- URL zawiera stale filtry 300-700, private, used.
- URL dla kolejnej strony zachowuje wszystkie filtry.

## 7. Etap 4 - Scraper i parser list wynikow

Cel: pobierac strony wynikow, wyciagac linki i podstawowe dane.

Zakres:

- `listing_scraper.py` pobiera HTML przez httpx.
- `listing_parser.py` wyciaga z listy: URL, OLX ID, tytul, cene, lokalizacje, date, thumbnail, pozycje.
- Obslugiwac paginacje przez link `Dalej`, z fallbackiem na `page=N`.
- Wykrywac powtorzone strony, brak wynikow, brak nastepnej strony i limity.
- Zapisywac `search_runs` i `search_profile_runs`.
- Dodac fixtures HTML do testow parsera.

Kryteria ukonczenia:

- Tryb `national` pobiera minimum jeden profil i zapisuje oferty z listy.
- Deduplikacja blokuje duplikaty tej samej oferty.
- Parser ma testy na zapisanych przykladach HTML.
- Bledy parsera sa zapisywane jako parser warnings.

## 8. Etap 5 - Kolejka szczegolow i parser oferty

Cel: pobierac dane szczegolowe co najmniej raz dla ofert uzywanych do bazy cen/scoringu.

Zakres:

- `details_queue.py` zapisuje oferty czekajace na detale.
- `detail_scraper.py` pobiera strony ofert z rate limitingiem.
- `detail_parser.py` wyciaga: tytul, cena, opis, parametry, lokalizacja, sprzedawca publiczny, liczba zdjec, glowne zdjecie, data.
- Nie pobierac telefonow, emaili ani prywatnych danych kontaktowych.
- Wykrywac oferty znikniete lub niedostepne.
- Zapisywac snapshoty i historie cen.

Kryteria ukonczenia:

- Nowe oferty trafiaja do kolejki detali.
- Limit detali na przebieg nie powoduje utraty ofert.
- Oferta po pobraniu detali ma snapshot w bazie.
- Parser detali ma testy na zapisanych przykladach HTML.

## 9. Etap 6 - Normalizacja, porownywanie i baza cen

Cel: zamienic surowe dane w dane porownywalne.

Zakres:

- Normalizacja ceny, rozmiaru, marki, modelu, technologii, rozdzielczosci i lokalizacji.
- Tworzenie `comparable_key`.
- Wyliczanie `comparison_confidence`.
- Budowanie tabel `comparable_groups` i `market_price_references`.
- Liczenie count, min, median, avg, p25, p75.
- Wykluczanie ofert `rejected` z normalnej bazy referencyjnej.
- Dodac komende `recalc-market`.

Kryteria ukonczenia:

- Oferta z wystarczajacymi danymi dostaje `comparable_key`.
- Baza cen powstaje dla grup z minimalna liczba ofert.
- Rzadkie/slabe dopasowania dostaja niska pewnosc zamiast falszywej okazji.

## 10. Etap 7 - Reguly opisowe

Cel: wykrywac czerwone flagi i sygnaly pozytywne.

Zakres:

- Tabela `description_rules`.
- Silnik regul dzialajacy na tytule, opisie, parametrach i combined text.
- Kategorie: red_flag, warning, positive, exclude, info.
- Akcje: flag, reject, boost, info.
- Minimalne reguly: uszkodzona matryca, brak obrazu, nie wlacza sie, brak pilota, brak podstawy, OLED, 4K, serwis.
- Testowanie regul przez CLI.

Kryteria ukonczenia:

- Reguly moga odrzucac oferty jako `rejected`.
- Wyniki regul sa zapisywane w `rule_matches`.
- `test-rules` pokazuje dopasowane reguly dla tekstu.

## 11. Etap 8 - Scoring i alerty Lodz

Cel: wykrywac lokalne okazje na podstawie bazy ogolnopolskiej.

Zakres:

- Tryb `lodz_alerts`.
- Porownanie ceny lokalnej z cena referencyjna.
- Wyliczanie `market_discount_percent`, `expected_resale_price`, `estimated_profit`, `score`.
- Statusy: opportunity, candidate, needs_review, weak_match, rejected, alerted.
- Progi alertow: score, rabat, profit, confidence, liczba ofert porownawczych.
- Zapis `alert_events`.
- Tlumienie powtorzonych alertow.

Kryteria ukonczenia:

- Oferta z Lodzi moze trafic do `Lodz alerty`.
- Alert nie powstaje bez wystarczajacej bazy porownawczej.
- Slabe dopasowanie nie dostaje automatycznie statusu `opportunity`.

## 12. Etap 9 - Eksport Excel

Cel: wygenerowac raport uzywalny do codziennej pracy.

Zakres:

- `output/oferty_tv_latest.xlsx` generowany z bazy.
- Arkusze: `Oferty`, `Lodz alerty`, `Baza cen`, `Historia skanow`.
- Klikalne linki do OLX.
- Filtry, sortowanie i podstawowe formatowanie.
- Opcjonalne kopie archiwalne z timestampem.

Kryteria ukonczenia:

- Eksport dziala komenda `export excel`.
- Excel zawiera wszystkie cztery arkusze.
- Arkusz `Lodz alerty` pokazuje tylko lokalne okazje/kandydatow do weryfikacji.
- Reczne decyzje uzytkownika pochodza z bazy, nie z edycji Excela.

## 13. Etap 10 - Panel webowy

Cel: dac proste UI do ustawien i kontroli pracy.

Zakres:

- FastAPI + proste szablony HTML.
- Widok ustawien globalnych.
- Widok profili rozmiarow.
- Widok regul opisowych.
- Widok progow scoringu.
- Akcje: uruchom national, uruchom lodz_alerts, export Excel, recalc-market.
- Widok ostatnich alertow Lodz.
- Edycja decyzji uzytkownika: watch, contacted, purchased, ignored, bad_match, not_profitable.

Kryteria ukonczenia:

- Panel uruchamia sie komenda `web`.
- Ustawienia zapisane w panelu sa uzywane przez CLI i scraper.
- Agent/uzytkownik nie musi edytowac YAML do codziennej pracy.

## 14. Etap 11 - Scheduler i serwer

Cel: przygotowac system do dzialania na VPS.

Zakres:

- Scheduler dla `national`, `lodz_alerts`, exportu i `recalc-market`.
- Ustawienia interwalow w panelu.
- Instrukcja uruchomienia na serwerze.
- Backup SQLite.
- Rotacja logow lub ograniczenie rozmiaru logow.

Kryteria ukonczenia:

- Harmonogram moze uruchamiac skany bez recznego CLI.
- System zapisuje logi i statusy przebiegow.
- Projekt ma instrukcje przeniesienia na VPS.

## 15. Kolejnosc minimalna dla pierwszego dzialajacego MVP

Najkrotsza sciezka do uzywalnego MVP:

1. Etap 0 - szkielet.
2. Etap 1 - baza.
3. Etap 2 - ustawienia.
4. Etap 3 - URL-e.
5. Etap 4 - listy wynikow.
6. Etap 5 - szczegoly.
7. Etap 6 - baza cen.
8. Etap 7 - reguly.
9. Etap 8 - Lodz scoring.
10. Etap 9 - Excel.

Panel moze powstawac rownolegle, ale nie powinien blokowac pierwszego dzialajacego scrapera i eksportu.
