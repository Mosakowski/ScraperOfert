# Plan uniwersalizacji scrapera ofert OLX

**Status:** bazowa uniwersalizacja wdrożona w kodzie; wymagane pozostaje sprawdzenie działania na kopii bazy i ograniczony przebieg OLX
**Data analizy:** 2026-11-06  
**Zakres planu:** wiele kategorii w serwisie OLX.pl; TV jest pierwszą kategorią, laptopy są pierwszym przykładem kolejnej kategorii.

## 1. Wizja

Użytkownik ma móc w panelu wybrać kategorię OLX, ustawić kryteria wyszukiwania, zapisać profil monitorowania i uruchomić go ręcznie albo cyklicznie. Przykładowo można mieć osobne profile dla telewizorów i laptopów, z różnymi lokalizacjami, limitami, filtrami i harmonogramami. Wyniki trafiają do jednej aplikacji i jednej bazy, ale porównują się tylko z ofertami z tej samej kategorii i odpowiednią grupą produktów.

Cel nie oznacza, że od pierwszego dnia aplikacja zna semantykę każdej kategorii OLX. Powinna zapewnić wspólny przepływ danych i konfigurację kategorii, a analizę właściwą dla produktu prowadzić przez zestaw parametrów, reguł oraz kryteriów porównania. Nową kategorię da się wtedy dodać jako konfigurację i, gdy wymaga nietypowej logiki, mały moduł domenowy zamiast kopii aplikacji.

## 2. Wnioski z analizy obecnego systemu

### Już wspólne i do ponownego użycia

- `listing_scraper.py` pobiera strony wyników niezależnie od produktu.
- `listing_parser.py` wyciąga podstawowe pola wspólne: tytuł, cenę, URL, lokalizację i miniaturę.
- `detail_scraper.py` pobiera stronę ogłoszenia, a `detail_parser.py` zbiera tytuł, cenę, opis i parametry jako pary klucz-wartość. To jest dobra baza pod różne typy produktów.
- `details_queue.py` i `detail_worker.py` obsługują wspólną kolejkę pobierania detali.
- Historia cen, deduplikacja, snapshoty, reguły tekstowe, harmonogram, limity pobierania i panel są w dużej mierze wspólną mechaniką.

### Elementy, które dziś zakładają kategorię TV

- `olx_urls.py` ma na stałe ścieżkę `/elektronika/tv/telewizory/` i filtr rozmiaru TV.
- `size_profiles` i `search_profile_runs.size_profile_id` reprezentują profile rozmiarów, a nie uniwersalne profile wyszukiwania.
- `offers` oraz `comparable_groups` mają pola i klucze takie jak przekątna, technologia i rozdzielczość. Oferta nie ma osobnego `category_id`.
- `normalization.py` ma słownik marek elektroniki oraz logikę modelu TV, cali, OLED/LED i rozdzielczości. `model_specs.py` również zakłada producenta i model telewizora.
- `comparison.py`, `market.py` i `scoring.py` korzystają z tych pól przy tworzeniu podobnych grup i ocenie ceny.
- Reguły, ustawienia scoringu i progi nie mają pełnego zakresu kategorii/profilu.
- `web.py` i szablony pokazują ustawienia rozmiarów TV, a nie katalog kategorii i profili.
- `export_excel.py` używa stałej nazwy `oferty_tv_latest.xlsx` i układu zakładającego TV oraz alerty łódzkie.
- Scheduler ma osobne, zakodowane workflow `national` i `lodz_alerts`, zamiast wykonywać aktywne profile monitorowania.

Wniosek: nie trzeba pisać ponownie scrapera, kolejki ani całego panelu. Trzeba dodać kategorię jako jawny wymiar danych i odseparować parametry TV od wspólnego przepływu. Największy zakres pracy jest w bazie i migracji, normalizacji/porównywaniu, ustawieniach panelu, eksporcie i schedulerze.

## 3. Jak traktować strukturę OLX

Publiczne strony OLX pokazują hierarchię kategorii i stron podkategorii. Przykładowa ścieżka laptopów to `Elektronika > Komputery > Laptopy`; strona telewizorów ma odrębną ścieżkę. Kategorie powinny być wybierane z katalogu obsługiwanych kategorii OLX, a profil powinien zapamiętywać konkretną kategorię/podkategorię i parametry URL.

Nie zakładaj jednego wspólnego zestawu filtrów dla wszystkich kategorii. Cena, lokalizacja, stan, typ sprzedawcy i sortowanie mogą być filtrami wspólnymi, o ile konkretna strona OLX je obsługuje. Filtry takie jak przekątna TV, procesor laptopa lub RAM są kategoriowe. Dla każdej obsługiwanej kategorii należy zachować mapowanie filtra na parametr URL OLX i przetestować wygenerowany adres.

Nie planować integracji Partner API jako źródła cudzych ofert. Oficjalne FAQ OLX mówi, że API służy do zarządzania ogłoszeniami autoryzowanego konta i nie pozwala czytać ogłoszeń innych użytkowników: [OLX Developer Portal FAQ](https://developer.olx.pl/articles/faq). Źródłem MVP pozostają publiczne strony ofert i kategorii. Jeśli OLX zaoferuje oficjalny produkt do odczytu publicznych ofert, można ocenić go osobno.

Kategoria OLX i rozpoznany typ produktu to dwie różne rzeczy. Kategoria określa źródłowy dział serwisu i zestaw dostępnych filtrów. Rozpoznanie typu produktu może być dokładniejsze, np. podkategoria „Laptopy” zawiera też baterie, części i akcesoria. Dla wiarygodnych porównań profil powinien umożliwiać zawężenie kategorii, a reguły lub klasyfikacja powinny odróżniać cały laptop od części do laptopa.

Serwis może zmieniać ścieżki, filtry i HTML. Katalog i mapowanie filtrów trzeba weryfikować na publicznych stronach OLX, a błędy i CAPTCHA mają wstrzymywać przebieg zgodnie z obecnym konserwatywnym podejściem. Nie obchodzić blokad i nie używać rotacji proxy.

## 4. Docelowy model pojęciowy

### Kategoria (`category`)

Konfiguracja produktu OLX, np. `telewizory` albo `laptopy`:

- stabilny wewnętrzny `id`, nazwa i status (`enabled`, `disabled`),
- ścieżka OLX i opcjonalny identyfikator/slug kategorii,
- obsługiwane filtry wspólne oraz mapowanie filtrów na nazwy parametrów URL,
- opis pól/atrybutów i ich typów, które warto wydobywać z parametrów, tytułu i opisu,
- strategia normalizacji, porównywania i reguł,
- ustawienia scoringu/alertów w zakresie, w którym różnią się od wspólnych domyślnych.

Pierwsze kategorie mogą być dostarczane jako sprawdzone definicje w kodzie lub plikach YAML. Panel wybiera pozycję z tego katalogu. „Uniwersalny” nie powinien oznaczać dowolnego URL-u wpisywanego przez użytkownika bez walidacji. Później można dodać odświeżanie katalogu, jeśli da się to zrobić w stabilny i dozwolony sposób.

### Profil monitorowania (`search_profile`)

Zastępuje założenie, że jedynym profilem jest rozmiar TV. Profil łączy:

- kategorię/podkategorię,
- nazwę profilu i jego włączenie,
- tryb i lokalizację (Polska albo lokalizacja z promieniem),
- wspólne filtry: zakres ceny, stan, sprzedawca, słowa kluczowe, sortowanie,
- filtry właściwe kategorii,
- limit stron/requestów i częstotliwość uruchamiania,
- kolejność/priorytet oraz ustawienia alertów.

Przykłady: „TV 40–49 cali, Polska”, „TV 40–49 cali, Łódź 50 km”, „Laptopy, Polska, do 1500 zł” i „Laptopy biznesowe, Łódź, 8–16 GB RAM”. Użytkownik może uruchomić jeden profil albo wszystkie aktywne profile.

### Oferta i parametry

Oferta zachowuje wspólne, znormalizowane pola: źródło, URL, identyfikator źródłowy, tytuł, cena i waluta, stan, typ sprzedawcy, lokalizacja, opis, znaczniki czasu oraz status. Dane surowe i parametry z OLX pozostają zachowane.

Parametry kategorii powinny być przechowywane jako elastyczne atrybuty z typem i źródłem rozpoznania, np. `screen_size_inches=55`, `ram_gb=16`, `gpu_model=RTX 4060`. Nie dodawać nowej kolumny do tabeli `offers` dla każdego parametru nowej kategorii. Istniejące pola TV można utrzymać dla zgodności raportów w okresie migracji, ale logika wspólna nie może wymagać ich dla każdej oferty.

### Grupa porównawcza i wycena

`comparable_key` zawsze jest ograniczony kategorią. Wspólna logika tworzy rynek referencyjny z ofert podobnych, ale to definicja kategorii mówi, które cechy decydują o podobieństwie.

- TV: producent/model, rozmiar, technologia, rozdzielczość i stan.
- Laptopy: producent/model lub seria, CPU, GPU (szczególnie dla laptopów gamingowych), RAM, rodzaj/pojemność dysku, ekran i stan.

Nie wszystkie atrybuty muszą być znane. System może tworzyć poziomy dopasowania i confidence jak obecny kod. Słabe dopasowanie kieruje ofertę do sprawdzenia zamiast mieszać ją z medianą dokładnych modeli. Uszkodzone sztuki, części, usługi i akcesoria muszą być oddzielone od pełnych, sprawnych produktów.

## 5. Docelowy przepływ

1. Użytkownik wybiera kategorię i zapisuje jeden lub więcej profili monitorowania.
2. Walidator sprawdza kategorię, dozwolone filtry, wartości i limit przebiegu.
3. Adapter OLX buduje publiczny URL kategorii i query string dla profilu.
4. Wspólny scraper pobiera listing, wspólny parser zbiera pola bazowe, a parser źródła zachowuje surowe parametry.
5. Deduplikacja uwzględnia źródło i ID/URL, a oferta oraz snapshot są przypisane do kategorii i profilu.
6. Wspólna kolejka pobiera szczegóły z limitami i retry. Blokada OLX przerywa pracę, nie kasując zadań.
7. Normalizator kategorii wylicza atrybuty produktu, reguły i diagnostykę źródła danych.
8. Comparator kategorii tworzy klucze dopasowania; agregator liczy referencje tylko wewnątrz kategorii i porównywalnego stanu.
9. Wspólny scoring łączy rabat, zysk, confidence i reguły z progami profilu/kategorii.
10. Wspólny scheduler uruchamia aktywne profile bez nakładania dwóch zapisujących przebiegów na tę samą bazę.
11. Panel filtruje oferty, przebiegi, alerty i ustawienia po kategorii. Eksport zapisuje kategorię/atrybuty i może filtrować lub podzielić arkusze.

## 6. Docelowy podział kodu

Nie jest wymagany nowy framework ani mikroserwisy. Zachowujemy obecny stos i porządkujemy odpowiedzialności:

- **`olx` adapter**: budowanie URL, wspólne pobieranie i paginacja, identyfikacja statusów odpowiedzi, mapowanie filtrów.
- **Definicje kategorii**: katalog obsługiwanych kategorii i schematy filtrów/atrybutów.
- **Wspólne modele i pipeline**: profile, oferta, snapshot, kolejka, historia cen, scoring bazowy, logi.
- **Strategie domenowe**: ekstrakcja/normalizacja parametrów, klucz podobieństwa, reguły kategorii.
- **Panel/eksport**: wybór kategorii i profilu oraz czytelne pokazywanie atrybutów dynamicznych.

Praktyczny wariant początkowy: zwykłe klasy/funkcje strategii z rejestrem `category_id -> definition`, bez skomplikowanego systemu pluginów. Parametry dobrze obsługiwane w polach OLX mapować konfiguracyjnie; nietypowe wnioskowanie z opisu może mieć mały normalizator kategorii.

## 7. Baza danych i migracja

Przygotować migrację SQLite, która zachowuje historię i istniejące ID ofert. Wymagane zmiany:

1. Tabela kategorii oraz seedy `telewizory`; przyszły seed `laptopy` dopiero po sprawdzeniu URL-i i filtrów.
2. Uogólnienie `size_profiles` do `search_profiles`, z `category_id`, JSON konfiguracji filtrów/trybu i harmonogramem. Alternatywnie zachować nazwę tabeli przez jedną migrację pomostową, ale API repozytorium ma już mówić o profilu wyszukiwania.
3. Dodać `category_id` do `offers`, `search_profile_runs`, `offer_snapshots`, `comparable_groups`, `market_price_references`/ich kluczy, reguł i ustawień zależnych od kategorii.
4. Zapewnić unikalność ID źródła jako `(source, source_offer_id)` lub równoważną. Dwa marketplace'y nie mogą przypadkiem scalić ID.
5. Dodać elastyczne atrybuty kategorii (np. `offer_attributes` albo kontrolowane `attributes_json`) z informacją: wartość surowa, typowana wartość, źródło i pewność.
6. Przypisać istniejące oferty, przebiegi i profile do `telewizory`; ustawić TV na ich obecne wartości, bez zmiany wyniku obecnych porównań.
7. Oddzielić `rule_category` (np. red flag/positive) od `product_category_id`, by nie pomylić istniejącego pola `category` w `description_rules`.
8. Dodać indeksy po kategorii, statusie, dacie i kluczach porównawczych. Ograniczenia FK i backup zachować.

Nie zmieniać produkcyjnej bazy przy pierwszym prototypie. Najpierw test migracji na kopii i fixture'ach; backup SQLite ma być wykonany przed wdrożeniem migracji.

## 8. Etapy realizacji

### Stan wdrożenia (2026-11-06)

- **Wdrożone:** katalog kategorii `televisions` i `laptops`, profile wyszukiwania, migracja SQLite zachowująca dotychczasowe profile TV, budowanie URL-i po ścieżce kategorii, walidacja dozwolonych filtrów, atrybuty JSON, normalizacja i klucze porównawcze TV/laptopów/pozostałych kategorii, reguły laptopów, filtr kategorii w panelu ofert, ręczne uruchamianie profilu, profilowy interwał scheduler i ogólny eksport `oferty_olx_latest.xlsx`.
- **Częściowe:** kategorie są konfigurowalne z panelu, ale dla kategorii spoza TV/laptopów używana jest normalizacja ogólna; pola kategorii i ich filtry wpisuje się jako JSON, nie są dynamicznie odkrywane z OLX. Scoring i alerty w większości współdzielą dotychczasowe ustawienia.
- **Do operacyjnego potwierdzenia:** migracja na kopii prawdziwej bazy, poprawność URL-i kategorii/filtrów w bieżącym OLX, parser laptopowych detali i jakość porównań na ograniczonej próbce. Nie uruchamiano przebiegu live w ramach wdrożenia kodu.

Etapy poniżej opisują cel i kryteria produktu. Punkty już wdrożone nie zwalniają z weryfikacji operacyjnej przed aktualizacją produkcyjnej bazy.

### Etap 0 — kontrakt kategorii

- Uzgodnić strukturę kategorii/profilu i wspólne pola oferty.
- Wybrać laptopy jako kategorię testową nr 2; sprawdzić stronę kategorii, paginację, dostępne parametry URL i detale ofert na OLX.
- Zdefiniować kryteria porównania TV oraz laptopów i rozróżniania produktu od części/akcesoriów.

**Gotowe, gdy:** model i przykładowa konfiguracja TV/laptop opisują różnice kategorii bez duplikowania wspólnego pipeline'u.

### Etap 1 — konfiguracja katalogu OLX

- Zastąpić stałą `CATEGORY_PATH` adapterem przyjmującym definicję kategorii.
- Przenieść mapowanie filtrów do schematu: `key`, etykieta, typ, wspólny/kategoriowy, nazwa parametru OLX, dozwolone wartości.
- Walidować URL-y dla wszystkich obsługiwanych profili; dodać fallback paginacji, gdy URL OLX nie daje stabilnego linku „Dalej”.
- Zachować bezpieczne limity i wykrywanie duplikatów stron.

**Gotowe, gdy:** jeden adapter tworzy poprawny URL dla profilu TV i laptopa, bez rozgałęzień ścieżki kategorii w skanerze.

### Etap 2 — migracja modelu danych

- Dodać tabele/rejestr kategorii i profili wyszukiwania.
- Dodać `category_id` do danych, wyników przebiegów, ustawień i grup porównawczych.
- Migrować rekordy TV bez utraty danych; zapewnić możliwość powrotu z backupu.
- Wprowadzić typowane atrybuty produktu w elastycznym formacie.

**Gotowe, gdy:** migracje od zera i ze starej bazy przechodzą, a raport TV po migracji ma te same oferty i klucze.

### Etap 3 — normalizatory i porównywanie kategorii

- Oddzielić wspólną normalizację (cena, lokalizacja, stan, tekst, seller type) od kategorii.
- Przenieść aktualną normalizację TV do strategii TV bez zmiany jej wyników.
- Dodać strategię laptopową: marka/model/seria, CPU, GPU, RAM, magazyn, rozmiar ekranu, stan, części/usługi.
- Generować hierarchiczne klucze dopasowania i confidence kategorii.
- Zakresować reguły, specs cache i scoring po kategorii.

**Gotowe, gdy:** oferty TV i laptopów nie trafiają do tych samych grup, a niepełne atrybuty są jawnie oznaczane.

### Etap 4 — panel i scheduler

- Dodać widok katalogu kategorii oraz tworzenie/edycję/włączanie profili.
- Formularz profilu pokazuje tylko filtry obsługiwane przez wybraną kategorię i lokalizację.
- Dashboard i lista ofert dostają filtr kategorii; etykiety oraz formularze nie zakładają przekątnej.
- Uogólnić harmonogram: uruchamia aktywne profile według interwału/priorytetu, z blokadą współbieżnych przebiegów.
- Pokazywać liczbę kolejki i ostatni błąd per profil/kategoria.

**Gotowe, gdy:** można w panelu włączyć profil TV i laptopa, uruchomić je oddzielnie, a log pokazuje kategorię i profil przebiegu.

### Etap 5 — eksport i alerty

- Zmienić stałą nazwę/arkusze eksportu na raport ogólny, z kolumnami wspólnymi i atrybutami właściwymi kategorii.
- Umożliwić eksport wszystkich kategorii albo jednej wybranej kategorii.
- Zakresować alerty, ustawienia progu i suppress window do profilu/kategorii.
- Domyślne koszty/score ustawiać per kategoria, z możliwością zmiany na profilu.

**Gotowe, gdy:** raport może zawierać TV i laptopy, nie porównuje ich między sobą i pokazuje potrzebne dla kategorii parametry.

### Etap 6 — wdrożenie kategorii laptopów

- Dodać zweryfikowaną definicję ścieżki i filtrów laptopów w OLX.
- Ustawić zakres ceny niezależny od TV; nie współdzielić wartości filtra ceny z profilu TV.
- Testować fixtures list i detali laptopów oraz typowe false positives (części, baterie, usługi, zestawy).
- Wykonać mały ręczny przebieg testowy, zapisać metryki pobrań i błędów, porównać wyniki z ręczną oceną.

**Gotowe, gdy:** użytkownik wybiera kategorię laptopów w UI, tworzy profil, zapisuje oferty i detale, buduje osobne ceny rynkowe, zmienia ustawienia i eksportuje wyniki.

### Etap 7 — stabilizacja i kolejne kategorie

- Monitorować zmianę HTML, liczbę pustych parse'ów, 403/CAPTCHA, backlog kolejki i błędy normalizacji per kategoria.
- Dodawać następne kategorie na bazie tego samego checklistu kontraktu, fixture'ów i testu URL.
- Ustawić jasny komunikat dla kategorii/filtrów nieobsługiwanych.

## 9. Testy i kryteria produktu

- Testy adaptera URL dla category path, wspólnych filtrów, filtrów kategorii, lokalizacji i paginacji.
- Fixtures OLX dla list i szczegółów przynajmniej TV i laptopa.
- Migracja starej bazy TV do nowego schematu; istniejące oferty i decyzje użytkownika zachowane.
- Izolacja deduplikacji i porównań między kategoriami oraz źródłami.
- Testy typowania atrybutów, brakujących danych, dopasowania i confidence.
- Reguły kategorii nie wpływają na inne kategorie, o ile nie są oznaczone jako wspólne.
- UI pozwala wybrać kategorię i profil; profile wyłączone nie uruchamiają pobierania.
- Scheduler uruchamia właściwy profil, respektuje limity, zapisuje status i nie uruchamia dwóch konfliktowych workerów.
- Eksport zawiera nazwę kategorii, atrybuty i link; rekordy różnych kategorii nie są porównywane razem.
- Ręczny ograniczony test publicznej strony OLX jest smoke testem operacyjnym, nie zastępuje fixture tests; po blokadzie system się zatrzymuje.

## 10. Ryzyka i decyzje projektowe

| Ryzyko | Sposób ograniczenia |
|---|---|
| Parametry URL/ścieżki różnią się w każdej podkategorii | jawne mapowanie i test URL na fixture/próbce dla każdej obsługiwanej kategorii |
| Zmienia się HTML lub OLX blokuje IP serwera | monitoring błędów parsera/statusów, konserwatywne limity, zatrzymanie przy CAPTCHA/403 |
| Szeroka kategoria zawiera części i akcesoria | obsługa podkategorii, fraz wykluczających i niepewności klasyfikacji |
| Model produktu ma inne cechy w każdej branży | elastyczne atrybuty i małe strategie domenowe, nie kolumny w tabeli dla każdego parametru |
| Dane różnych produktów zanieczyszczą medianę | `category_id` w kluczu/grupie cenowej i wymuszona izolacja zapytań |
| Migracja uszkodzi historię TV | backup, migracja na kopii, zachowanie ID i test zgodności liczebności/kluczy |
| Różne częstotliwości wyczerpią limity/rosnącą kolejkę | limity per profil, priorytety, metryki backlogu i możliwość pauzy profilu |

## 11. Poza pierwszą wersją uniwersalną

- Inne marketplace'y niż OLX.
- Partner API do odczytu cudzych ogłoszeń — oficjalne FAQ OLX wskazuje, że ten przypadek nie jest obsługiwany.
- Obchodzenie CAPTCHA, logowanie scraperem, rotowanie proxy lub ukrywanie automatyzacji.
- Automatyczna klasyfikacja dowolnego produktu bez jawnych kategorii i weryfikacji.
- Osobna baza danych lub mikroserwis dla każdej kategorii.

## 12. Materiały OLX

- [Laptopy OLX — publiczna podkategoria i przykładowe listingi](https://www.olx.pl/elektronika/komputery/laptopy/)
- [Laptopy OLX — widok wyników zapytania](https://www.olx.pl/elektronika/komputery/q-laptopy/)
- [OLX Developer Portal FAQ — ograniczenia Partner API](https://developer.olx.pl/articles/faq)

Struktura publicznych stron i filtry są zmienne; sprawdź je ponownie przed implementacją kategorii laptopów.
