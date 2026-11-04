# Checklista wydania MVP na VPS

Stan na 2026-11-04. Odhaczaj po wykonaniu na wersji przeznaczonej do wdrożenia, a nie na podstawie wcześniejszych prób lokalnych.

## Przed wdrożeniem

- [ ] Testy `python -m pytest -q` przechodzą na commicie przeznaczonym do wdrożenia.
- [ ] Commit i push obejmują kod, testy i dokumentację potrzebne do instalacji; pliki diagnostyczne, bazy i raporty nie trafiają do Git.
- [ ] Migracja działa na pustej bazie i na kopii istniejącej bazy.
- [ ] Panel jest dostępny tylko przez chroniony kanał z HTTPS; port aplikacji nie jest publiczny.
- [ ] Skonfigurowano dwie usługi: `web` i `scheduler`, z tym samym `WorkingDirectory` i automatycznym restartem.
- [ ] Wybrany backend pobierania działa na VPS; przy Playwright zainstalowano Chromium i biblioteki systemowe.
- [ ] Skonfigurowano backup SQLite i wykonano próbę odtworzenia.

## Próba na docelowym VPS

- [ ] Skan `national` zapisuje oferty bez blokady lub poprawnie raportuje jej przyczynę.
- [ ] `process-details` przetwarza zadania z kolejki i zapisuje opisy oraz parametry.
- [ ] `recalc-market` tworzy dane porównawcze i wyceny.
- [ ] Skan `lodz_alerts` i detale lokalnych ofert działają.
- [ ] Eksport tworzy `output/oferty_tv_latest.xlsx`.
- [ ] Statusy przebiegów, liczba oczekujących zadań i logi usług są sprawdzone po pełnym cyklu.
- [ ] Po restarcie VPS usługi wstają i używają tej samej bazy.

Instrukcja uruchomienia: [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md).
