# Release Hardening Checklist (MVP)

Do upewnienia się, że aplikacja zadziała czysto w nowym środowisku, przeprowadź (i odznacz) poniższe kroki w środowisku developerskim przed wrzutką na serwer.

## Smoke Testy Środowiskowe

- [x] **Testy jednostkowe:** Wykonaj `pytest`. Wynik powinien wskazywać na 100% pozytywnych asercji.
- [x] **Czysta migracja:** Skasuj manualnie plik bazy danych (`data/offers.sqlite`). Uruchom `python -m scraper_ofert_tv migrate`. Migracja musi przebiec do końca i wygenerować plik sqlite o nienaruszonej strukturze i relacjach (bez błędów Integrity/Foreign).
- [x] **Skan główny (national):** Na pustej (świeżo zbudowanej) bazie uruchom `python -m scraper_ofert_tv scan --mode national`. Skan powinien zebrać listę wyników i zapisać je z poprawnym stanem.
- [x] **Detale (Queue Worker):** Uruchom `python -m scraper_ofert_tv process-details`. Baza powinna zapisać logi i stworzyć snaphshoty detali dla pierwszych X ogłoszeń. Test `test_detail_worker_schema_match` symuluje ten proces rygorystycznie.
- [x] **Przeliczanie bazy (recalc-market):** Uruchom `python -m scraper_ofert_tv recalc-market`. Przelicza logikę median, wstawia relacyjne rekordy do analizy cen i opcjonalnie triggeruje status `active`/`opportunity`/`rejected`.
- [x] **Test regul (test-rules):** Zweryfikuj silnik na sucho komendą CLI `python -m scraper_ofert_tv test-rules --text "zbita matryca"` - musi odrzucić usterkę z seedów regul.
- [x] **Skan łódzki (lodz_alerts):** Uruchom `python -m scraper_ofert_tv scan --mode lodz_alerts`. Z założenia wyszukuje szybszych alertów opartych na nowym stanie bazy referencyjnej.
- [x] **Eksport (excel):** Ostatecznym testem bazy jest `python -m scraper_ofert_tv export excel`. Upewnij się, że w folderze `output/` powstał poprawny i sformatowany plik XLSX.
- [x] **Kopia Zapasowa (backup):** Sprawdź poprawność komendy `python -m scraper_ofert_tv backup-db`. Powinna utworzyć nowy plik zapasowy w podfolderze `data/backups/`.
- [x] **Scheduler Start:** Zamknij wszystkie inne demony, sprawdź flagę pomocy `python -m scraper_ofert_tv scheduler --help` i uruchom go w celach testu.

Ukończenie niniejszych poleceń świadczy o w pełni gotowym procesie MVP Scrapera do instalacji.
