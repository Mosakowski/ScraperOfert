# Agent Guide - Scraper Ofert TV

Ten dokument jest instrukcja pracy dla agenta AI, ktory bedzie implementowal projekt. Architektura i wymagania sa opisane w PRD.md, IMPLEMENTATION_PLAN.md, TASKS.md i DB_SCHEMA.md.

## 1. Twoja rola

Jestes agentem kodujacym. Twoim zadaniem jest implementacja MVP zgodnie z dokumentacja, bez samodzielnego rozszerzania zakresu.

Cel produktu jest wielokategorialny; aktualne MVP wdraża telewizory. Przy zmianach w częściach wspólnych zachowuj możliwość dodania kolejnej kategorii bez kopiowania aplikacji. Nie oznaczaj obsługi wielu kategorii jako gotowej, dopóki nie zostanie wdrożona i przetestowana.

Masz budowac system krok po kroku:

1. Czytaj dokumentacje.
2. Wybierz najblizsze zadanie z TASKS.md.
3. Zaimplementuj najmniejsza kompletna zmiane.
4. Dodaj lub zaktualizuj testy.
5. Uruchom weryfikacje.
6. Zaktualizuj checklisty, jesli zadanie jest ukonczone.
7. Zraportuj wynik.

## 2. Zrodla prawdy

Kolejnosc waznosci dokumentow:

1. `PRD.md` - zakres produktowy i decyzje MVP.
2. `DB_SCHEMA.md` - kontrakt bazy danych.
3. `IMPLEMENTATION_PLAN.md` - kolejnosc techniczna.
4. `TASKS.md` - checklista wykonawcza.
5. `README.md` - instrukcja uruchomienia dla uzytkownika.

Jesli dokumenty sa sprzeczne, zatrzymaj sie i popros o decyzje architekta albo wlasciciela projektu.

## 3. Zakres MVP

Implementuj tylko MVP:

- OLX jako jedyne zrodlo danych.
- Publiczne strony wynikow i ofert.
- Brak logowania do OLX.
- Brak Facebook Marketplace.
- Brak pobierania telefonow, emaili i prywatnych danych kontaktowych.
- Brak zewnetrznych powiadomien push w MVP.
- Brak mikroserwisow.
- Brak PostgreSQL w MVP.
- Brak Dockera jako wymagania MVP.
- Brak analizy zdjec w MVP.
- Brak AI do klasyfikacji opisow w MVP.

## 4. Granice scrapingu

Projekt zaklada uprawniony research i kontrolowane pobieranie publicznych danych. Implementacja ma byc stabilna i ostrozna.

Wolno implementowac:

- opoznienia,
- jitter,
- retry,
- backoff,
- cooldown profilu,
- kolejke detali,
- limity requestow,
- wykrywanie blokady/CAPTCHA,
- wznowienie pracy po cooldownie.

Nie implementuj bez osobnej decyzji:

- lamania CAPTCHA,
- automatycznego rozwiazywania CAPTCHA,
- omijania prywatnych obszarow,
- scrapingu po zalogowaniu,
- pobierania kontaktow,
- agresywnej rotacji proxy,
- automatycznego wysylania wiadomosci do sprzedawcow.

Po blokadzie system nie ma tracic kolejki. Ma zapisac status, odczekac cooldown i wznowic prace zgodnie z limitami.

## 5. Stack

Uzyj:

- Python,
- FastAPI,
- uvicorn,
- httpx,
- selectolax,
- SQLite,
- openpyxl,
- PyYAML,
- pytest.

Opcjonalnie:

- BeautifulSoup jako pomocniczy parser.
- Playwright tylko jako pozniejszy fallback, jesli statyczny HTML nie wystarczy.

## 6. Styl kodu

- Preferuj proste moduly i jawne funkcje.
- Nie tworz mikroserwisow.
- Nie mieszaj logiki scrapingu, bazy, scoringu i web UI w jednym pliku.
- Funkcje parserow powinny przyjmowac HTML/string i zwracac struktury danych.
- Kod sieciowy powinien byc oddzielony od parserow.
- Baza powinna byc obslugiwana przez warstwe `storage.py`.
- Nie zapisuj ustawien tylko w YAML. YAML jest seed/export/backup/fallback.
- Excel jest raportem, nie baza danych.

## 7. Dane i kontrakty

Najwazniejsze reguly danych:

- Deduplikacja po `olx_offer_id`, `canonical_url`, a awaryjnie po hashu.
- Cena jako `price_pln` integer albo NULL, plus `raw_price`.
- Nie tworz pola waluty.
- Pelny opis oferty ma byc zapisany, bo reguly i uzytkownik go potrzebuja.
- Zapisywac tylko glowne zdjecie, nie pelna galerie.
- Decyzje uzytkownika sa osobne od statusu systemowego.
- Oferty uszkodzone ida do `rejected`.
- `weak_match` i `needs_review` nie powinny automatycznie stawac sie `opportunity`.

## 8. Testy

Wymagane testy dla MVP:

- migracje bazy,
- deduplikacja ofert,
- budowanie URL-i OLX,
- parser list wynikow na fixtures HTML,
- parser detali na fixtures HTML,
- normalizacja ceny i rozmiaru,
- tworzenie `comparable_key`,
- reguly opisowe,
- scoring,
- alerty Lodz,
- generowanie pliku Excel.

Parsery musza miec fixtures HTML. Nie opieraj testow parsera wylacznie na live OLX.

## 9. Logowanie

Loguj:

- start i koniec skanu,
- tryb skanu,
- profil,
- URL wyszukiwania,
- numer strony,
- liczbe ofert,
- nowe/znane oferty,
- kolejke detali,
- pobrane szczegoly,
- bledy HTTP,
- timeouty,
- parser warnings,
- blokady/CAPTCHA,
- backoff/cooldown,
- powody stopu.

Decyzje analityczne zapisuj w bazie:

- `comparable_key`,
- cena referencyjna,
- confidence,
- reguly,
- score,
- estimated profit,
- powod alertu.

## 10. Panel webowy

Panel ma byc prosty i praktyczny. Nie buduj dashboardu premium.

Minimalne widoki:

- ustawienia globalne,
- profile rozmiarow,
- reguly opisowe,
- progi scoringu,
- ostatnie skany,
- Lodz alerty,
- szczegoly oferty z decyzja uzytkownika.

Minimalne akcje:

- uruchom skan national,
- uruchom skan lodz_alerts,
- export Excel,
- recalc market,
- backup DB.

## 11. Excel

Generuj `output/oferty_tv_latest.xlsx`.

Arkusze:

- `Oferty`,
- `Lodz alerty`,
- `Baza cen`,
- `Historia skanow`.

Nie zakladaj, ze uzytkownik bedzie recznie edytowal Excel jako zrodlo prawdy. Jesli uzytkownik ma dodac decyzje, powinna trafic do bazy przez panel.

## 12. Workflow skanow

Docelowy workflow:

1. `national` pobiera oferty z calej Polski.
2. Detale sa pobierane dla nowych ofert.
3. Reguly oznaczaja czerwone flagi.
4. `recalc-market` buduje baze cen.
5. `lodz_alerts` pobiera oferty lokalne.
6. Scoring porownuje Lodz z baza ogolnopolska.
7. Alerty zapisuja sie w bazie.
8. `export excel` tworzy raport.

## 13. Jak raportowac postep

Po kazdej wiekszej zmianie raportuj:

- jakie zadania z TASKS.md zostaly zrobione,
- jakie pliki zmieniono,
- jakie testy uruchomiono,
- co nie zostalo sprawdzone,
- jakie sa nastepne zadania.

Nie oznaczaj zadania jako ukonczone, jesli kod nie zostal uruchomiony lub przetestowany w sensownym zakresie.

## 14. Kiedy pytac architekta

Zapytaj przed zmiana zakresu, jesli:

- OLX wymaga logowania,
- parser nie moze pobrac danych bez JS,
- trzeba dodac Playwright,
- chcesz zmienic schemat bazy,
- chcesz zmienic scoring,
- chcesz dodac PostgreSQL, Docker, proxy, zewnetrzne powiadomienia albo AI,
- dokumenty sa sprzeczne.

## 15. Zakaz cichych zmian produktowych

Nie zmieniaj tych decyzji bez zgody:

- cena 300-700 PLN jako domyslny zakres,
- tylko prywatne i uzywane oferty,
- profile roznia sie tylko rozmiarem TV,
- Lodz alerty w MVP,
- SQLite jako baza MVP,
- Excel jako raport,
- panel jako miejsce ustawien,
- uszkodzone oferty jako `rejected`.
