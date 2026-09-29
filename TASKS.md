# Tasks - Scraper Ofert TV

Ten plik jest checklista wykonawcza dla agenta kodujacego. Zadania powinny byc wykonywane zgodnie z PRD.md, IMPLEMENTATION_PLAN.md, DB_SCHEMA.md i AGENT_GUIDE.md.

## 0. Przygotowanie

- [x] T001 Przeczytaj `PRD.md`, `IMPLEMENTATION_PLAN.md`, `DB_SCHEMA.md` i `AGENT_GUIDE.md`.
- [x] T002 Utworz strukture katalogow projektu.
- [x] T003 Skonfiguruj projekt Python i zaleznosci.
- [x] T004 Dodaj pakiet `scraper_ofert_tv` w `src/`.
- [x] T005 Dodaj entrypoint `python -m scraper_ofert_tv`.
- [x] T006 Dodaj podstawowe testy uruchomieniowe.
- [x] T007 Dodaj README z komendami startowymi.

## 1. Baza danych

- [x] T101 Dodaj `migrations.py`.
- [x] T102 Dodaj tabele z `DB_SCHEMA.md`.
- [x] T103 Dodaj migracje inicjalna.
- [x] T104 Dodaj tabele `schema_migrations`.
- [x] T105 Dodaj seed ustawien domyslnych.
- [x] T106 Dodaj seed profili rozmiarow OLX.
- [x] T107 Dodaj seed podstawowych regul opisowych.
- [x] T108 Dodaj `storage.py` z polaczeniem SQLite.
- [x] T109 Dodaj funkcje tworzenia `search_run`.
- [x] T110 Dodaj funkcje tworzenia `search_profile_run`.
- [x] T111 Dodaj funkcje upsert oferty.
- [x] T112 Dodaj funkcje zapisu snapshotu.
- [x] T113 Dodaj funkcje zapisu historii ceny.
- [x] T114 Dodaj funkcje backupu bazy.
- [x] T115 Dodaj testy migracji i deduplikacji.

## 2. CLI

- [x] T201 Dodaj komenda `migrate`.
- [x] T202 Dodaj komenda `backup-db`.
- [x] T203 Dodaj komenda `show-config`.
- [x] T204 Dodaj komenda `scan --mode national`.
- [x] T205 Dodaj komenda `scan --mode lodz_alerts`.
- [x] T206 Dodaj komenda `scan --mode national --profile 40_49`.
- [x] T207 Dodaj komenda `export excel`.
- [x] T208 Dodaj komenda `recalc-market`.
- [x] T209 Dodaj komenda `test-rules --text`.
- [x] T210 Dodaj komenda `web --host --port`.

## 3. Ustawienia i konfiguracja

- [x] T301 Dodaj `settings_service.py`.
- [x] T302 Odczytuj ustawienia globalne z bazy.
- [x] T303 Odczytuj profile rozmiarow z bazy.
- [x] T304 Odczytuj ustawienia `national`.
- [x] T305 Odczytuj ustawienia `lodz_alerts`.
- [x] T306 Odczytuj ustawienia rate limit.
- [x] T307 Odczytuj ustawienia scoringu.
- [x] T308 Dodaj import ustawien z YAML.
- [x] T309 Dodaj export ustawien do YAML.
- [x] T310 Dodaj walidacje ustawien.

## 4. Budowanie URL-i OLX

- [x] T401 Dodaj `olx_urls.py`.
- [x] T402 Zbuduj URL kategorii Telewizory dla trybu `national`.
- [x] T403 Dodaj parametry ceny 300-700.
- [x] T404 Dodaj parametr ofert prywatnych.
- [x] T405 Dodaj parametr stanu uzywane.
- [x] T406 Dodaj parametry natywnych rozmiarow TV OLX.
- [x] T407 Dodaj paginacje `page=N`.
- [x] T408 Dodaj budowanie URL dla `lodz_alerts`.
- [x] T409 Dodaj testy URL-i dla kazdego profilu rozmiaru.

## 5. Rate limiter

- [x] T501 Dodaj `rate_limiter.py`.
- [x] T502 Dodaj opoznienia dla list wynikow.
- [x] T503 Dodaj opoznienia dla stron szczegolow.
- [x] T504 Dodaj losowy jitter.
- [x] T505 Dodaj limit requestow na minute.
- [x] T506 Dodaj limit requestow na przebieg.
- [x] T507 Dodaj limit detali na przebieg.
- [x] T508 Dodaj backoff po bledach.
- [x] T509 Dodaj cooldown profilu po blokadzie.
- [x] T510 Dodaj status `temporarily_blocked` w przebiegach profili.

## 6. Scraper list wynikow

- [x] T601 Dodaj `listing_scraper.py`.
- [x] T602 Pobieraj HTML przez httpx.
- [x] T603 Ustaw timeouty i naglowki requestow.
- [x] T604 Obsluguj HTTP 200, 404, 429, 5xx.
- [x] T605 Wykrywaj sygnaly CAPTCHA/blokady.
- [x] T606 Zapisuj bledy do logow i `search_profile_runs`.
- [x] T607 Przestrzegaj rate limitera.

## 7. Parser list wynikow

- [x] T701 Dodaj `listing_parser.py`.
- [x] T702 Wyciagaj URL oferty.
- [x] T703 Wyciagaj canonical URL albo dane do jego pozniejszego ustalenia.
- [x] T704 Wyciagaj OLX ID, jesli jest dostepny.
- [x] T705 Wyciagaj tytul.
- [x] T706 Wyciagaj cene i raw price.
- [x] T707 Wyciagaj lokalizacje z listy.
- [x] T708 Wyciagaj date z listy.
- [x] T709 Wyciagaj thumbnail.
- [x] T710 Wyciagaj numer strony i pozycje.
- [x] T711 Wykrywaj link `Dalej`.
- [x] T712 Dodaj testy parsera na fixtures HTML.

## 8. Paginacja i deduplikacja

- [x] T801 Implementuj przechodzenie po stronach do `max_pages`.
- [x] T802 Preferuj link `Dalej`.
- [x] T803 Dodaj fallback `page=N`.
- [x] T804 Wykrywaj powtorzona strone wynikow.
- [x] T805 Wykrywaj brak ofert.
- [x] T806 Wykrywaj brak nowych ofert jako warunek stopu, jesli wlaczony.
- [x] T807 Deduplikuj po OLX ID.
- [x] T808 Deduplikuj po canonical URL.
- [x] T809 Deduplikuj awaryjnie po hashu URL/tytul/cena/lokalizacja.

## 9. Kolejka detali

- [x] T901 Dodaj `details_queue.py`.
- [x] T902 Dodawaj nowe oferty do kolejki detali.
- [x] T903 Dodawaj oferty bez `comparable_key` do kolejki.
- [x] T904 Dodawaj oferty po zmianie ceny do kolejki.
- [x] T905 Pobieraj oferty z kolejki wedlug priorytetu.
- [x] T906 Respektuj limit `max_detail_fetches_per_run`.
- [x] T907 Oznaczaj zadania jako pending, processing, done, failed, skipped.
- [x] T908 Ponawiaj zadania po bledach zgodnie z limitem.

## 10. Scraper i parser szczegolow

- [x] T1001 Dodaj `detail_scraper.py`.
- [x] T1002 Dodaj `detail_parser.py`.
- [x] T1003 Wyciagaj pelny tytul.
- [x] T1004 Wyciagaj cene i raw price.
- [x] T1005 Wyciagaj opis.
- [x] T1006 Wyciagaj parametry.
- [x] T1007 Wyciagaj lokalizacje.
- [x] T1008 Wyciagaj publiczna nazwe sprzedawcy i publiczny URL profilu, jesli dostepne.
- [x] T1009 Wyciagaj liczbe zdjec.
- [x] T1010 Wyciagaj tylko URL glownego zdjecia.
- [x] T1011 Wykrywaj stan oferty: aktywna, usunieta, niedostepna.
- [x] T1012 Nie pobieraj telefonow, emaili ani prywatnych danych kontaktowych.
- [x] T1013 Dodaj testy parsera szczegolow na fixtures HTML.

## 11. Normalizacja

- [x] T1101 Dodaj `normalization.py`.
- [x] T1102 Normalizuj cene do `price_pln`.
- [x] T1103 Normalizuj informacje o negocjacji ceny.
- [x] T1104 Normalizuj rozmiar TV w calach.
- [x] T1105 Zapisuj natywny bucket OLX.
- [x] T1106 Normalizuj marke.
- [x] T1107 Normalizuj model.
- [x] T1108 Normalizuj technologie: LED, OLED, QLED itd.
- [x] T1109 Normalizuj rozdzielczosc.
- [x] T1110 Normalizuj lokalizacje: miasto, dzielnica, region.
- [x] T1111 Wykrywaj pilot, podstawke, pudelko, odbior/dostawe.

## 12. Porownywanie i baza cen

- [x] T1201 Dodaj `comparison.py`.
- [x] T1202 Tworz `comparable_key`.
- [x] T1203 Wyliczaj `comparison_confidence`.
- [x] T1204 Dodaj `market.py`.
- [x] T1205 Grupuj oferty po `comparable_key`.
- [x] T1206 Wykluczaj `rejected` z normalnych cen referencyjnych.
- [x] T1207 Wyliczaj count, min, median, avg, p25, p75.
- [x] T1208 Zapisuj `market_price_references`.
- [x] T1209 Dodaj testy dla mediany i confidence.

## 13. Reguly opisowe

- [x] T1301 Dodaj `rules.py`.
- [x] T1302 Wczytuj aktywne reguly z bazy.
- [x] T1303 Obsluguj pola: title, description, params, combined_text.
- [x] T1304 Obsluguj match_mode: contains, regex.
- [x] T1305 Obsluguj akcje: flag, reject, boost, info.
- [x] T1306 Zapisuj `rule_matches`.
- [x] T1307 Dodaj reguly na uszkodzona matryce.
- [x] T1308 Dodaj reguly na brak obrazu.
- [x] T1309 Dodaj reguly na brak wlaczania.
- [x] T1310 Dodaj reguly na brak pilota.
- [x] T1311 Dodaj reguly na brak podstawy.
- [x] T1312 Dodaj reguly pozytywne OLED/4K.
- [x] T1313 Dodaj testy regul.

## 14. Scoring

- [x] T1401 Dodaj `scoring.py`.
- [x] T1402 Wyliczaj `market_discount_percent`.
- [x] T1403 Wyliczaj `expected_resale_price`.
- [x] T1404 Wyliczaj `estimated_profit`.
- [x] T1405 Wyliczaj score 0-100.
- [x] T1406 Uwzgledniaj confidence.
- [x] T1407 Uwzgledniaj liczbe ofert porownawczych.
- [x] T1408 Uwzgledniaj reguly opisowe.
- [x] T1409 Nadawaj statusy systemowe.
- [x] T1410 Nie oznaczaj `weak_match` jako `opportunity`.
- [x] T1411 Odrzucaj uszkodzone oferty jako `rejected`.
- [x] T1412 Dodaj testy scoringu.

## 15. Lodz alerty

- [x] T1501 Dodaj `alerts.py`.
- [x] T1502 Implementuj tryb `lodz_alerts`.
- [x] T1503 Uzywaj lokalizacji Lodz i promienia z ustawien.
- [x] T1504 Porownuj lokalne oferty z baza ogolnopolska.
- [x] T1505 Stosuj progi score, rabatu, profitu i confidence.
- [x] T1506 Wymagaj minimalnej liczby ofert porownawczych.
- [x] T1507 Zapisuj `alert_events`.
- [x] T1508 Tlum powtorzone alerty przez skonfigurowany czas.
- [x] T1509 Dodaj testy alertow.

## 16. Excel

- [x] T1601 Dodaj `export_excel.py`.
- [x] T1602 Generuj `output/oferty_tv_latest.xlsx`.
- [x] T1603 Dodaj arkusz `Oferty`.
- [x] T1604 Dodaj arkusz `Lodz alerty`.
- [x] T1605 Dodaj arkusz `Baza cen`.
- [x] T1606 Dodaj arkusz `Historia skanow`.
- [x] T1607 Dodaj filtry i zamrozenie naglowkow.
- [x] T1608 Dodaj klikalne linki do OLX.
- [x] T1609 Dodaj podstawowe formatowanie statusow i score.
- [x] T1610 Dodaj opcjonalne kopie archiwalne.
- [x] T1611 Dodaj test sprawdzajacy utworzenie pliku xlsx.

## 17. Panel webowy

- [x] T1701 Dodaj `web.py` z FastAPI.
- [x] T1702 Dodaj szablony HTML.
- [x] T1703 Dodaj statyczny CSS.
- [x] T1704 Widok ustawien globalnych.
- [x] T1705 Widok profili rozmiarow.
- [x] T1706 Widok regul opisowych.
- [x] T1707 Widok progow scoringu.
- [x] T1708 Widok ostatnich skanow.
- [x] T1709 Widok `Lodz alerty`.
- [x] T1710 Akcja uruchomienia `national`.
- [x] T1711 Akcja uruchomienia `lodz_alerts`.
- [x] T1712 Akcja export Excel.
- [x] T1713 Akcja recalc-market.
- [x] T1714 Edycja decyzji uzytkownika dla oferty.

## 18. Scheduler

- [x] T1801 Dodaj `scheduler.py`.
- [x] T1802 Dodaj harmonogram `national`.
- [x] T1803 Dodaj harmonogram `lodz_alerts`.
- [x] T1804 Dodaj harmonogram exportu Excel.
- [x] T1805 Dodaj harmonogram `recalc-market`.
- [x] T1806 Umozliwiaj edycje interwalow w panelu.
- [x] T1807 Loguj uruchomienia scheduler.

## 19. Dokumentacja i uruchomienie

- [x] T1901 Uzupelnij README o instalacje lokalna.
- [x] T1902 Uzupelnij README o komendy CLI.
- [x] T1903 Uzupelnij README o panel webowy.
- [x] T1904 Dodaj instrukcje przeniesienia na VPS.
- [x] T1905 Dodaj opis backupu SQLite.
- [x] T1906 Dodaj opis workflow: national -> recalc-market -> lodz_alerts -> export.

## 20. Definicja ukonczenia MVP

- [x] T2001 Wszystkie kryteria z rozdzialu 26 PRD sa spelnione.
- [x] T2002 Testy parserow przechodza na fixtures HTML.
- [x] T2003 Testy scoringu i alertow przechodza.
- [x] T2004 Da sie uruchomic skan `national`.
- [x] T2005 Da sie uruchomic skan `lodz_alerts`.
- [x] T2006 Da sie wygenerowac Excel.
- [x] T2007 Panel pozwala edytowac ustawienia i reguly.
- [x] T2008 Dane uzytkownika sa zapisane w bazie, nie tylko w Excelu.
