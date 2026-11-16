# Checklista wydania MVP na VPS

Stan na 2026-11-16. Odhaczaj po wykonaniu na wersji przeznaczonej do wdrożenia, a nie na podstawie wcześniejszych prób lokalnych.

## Przed wdrożeniem

- [x] Testy `python -m pytest -q` przechodzą lokalnie (52 testy, 2026-11-16); przed wdrożeniem uruchom je ponownie na docelowym commicie.
- [ ] Commit i push obejmują kod, testy i dokumentację potrzebne do instalacji; pliki diagnostyczne, bazy i raporty nie trafiają do Git.
- [x] Migracje przechodzą na pustej bazie testowej i lokalnej bazie projektu (schemat v4); przed wdrożeniem sprawdź kopię bazy serwerowej.
- [ ] Panel jest dostępny tylko przez chroniony kanał z HTTPS; port aplikacji nie jest publiczny.
- [ ] Skonfigurowano dwie usługi: `web` i `scheduler`, z tym samym `WorkingDirectory` i automatycznym restartem.
- [ ] Wybrany backend pobierania działa na VPS; przy Playwright zainstalowano Chromium i biblioteki systemowe.
- [ ] Skonfigurowano backup SQLite i wykonano próbę odtworzenia.

## Próba na docelowym VPS

- [ ] Skan `national` zapisuje oferty bez blokady lub poprawnie raportuje jej przyczynę.
- [ ] `process-details` przetwarza zadania z kolejki i zapisuje opisy oraz parametry.
- [ ] `recalc-market` tworzy dane porównawcze i wyceny.
- [ ] Skan `lodz_alerts` i detale lokalnych ofert działają.
- [ ] Eksport tworzy ogólny `output/oferty_olx_latest.xlsx` i raport wybranej kategorii.
- [ ] Statusy przebiegów, liczba oczekujących zadań i logi usług są sprawdzone po pełnym cyklu.
- [ ] Po restarcie VPS usługi wstają i używają tej samej bazy.

Instrukcja uruchomienia: [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md).
