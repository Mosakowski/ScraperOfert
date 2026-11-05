# PRD: Uniwersalny scraper ofert - MVP dla telewizorow z OLX

## 1. Cel produktu

Celem produktu jest uniwersalny system wyszukiwania i oceny ofert z różnych kategorii. Telewizory na OLX są pierwszą wdrażaną kategorią i zakresem tego MVP. System będzie cyklicznie wyszukiwał publiczne oferty TV, pobierał dane z list wyników oraz stron poszczególnych ofert, oceniał atrakcyjność według edytowalnych reguł i eksportował wynik do pliku Excel.

Kolejne kategorie powinny korzystać ze wspólnego przepływu: pobrania listy i detali, kolejki, historii ceny, reguł, porównania ofert, scoringu, harmonogramu i panelu. Właściwe dla kategorii są: adresy i filtry wyszukiwania, rozpoznawane parametry, klucz porównania, reguły oraz progi oceny. Oferty i ich grupy porównawcze muszą mieć identyfikator kategorii, aby ceny różnych typów produktów nie były mieszane. Dodanie kategorii nie powinno wymagać kopiowania całej aplikacji ani osobnej bazy.

Narzedzie nie ma automatycznie kupowac ofert ani kontaktowac sie ze sprzedawcami. Jego rola jest szybkie wskazywanie ofert z potencjalnym zyskiem, ofert ryzykownych oraz ofert wymagajacych recznej weryfikacji.

MVP moze byc uruchamiane lokalnie na komputerze uzytkownika, ale docelowa architektura powinna zakladac uruchomienie na serwerze, VPS albo innym stale dzialajacym srodowisku. Dzieki temu system bedzie mogl wykonywac skany cyklicznie bez koniecznosci odpalania go recznie na prywatnym komputerze.

Projekt ma dwa glowne tryby:

1. Tryb ogolnopolski: szerokie wyszukiwanie ofert TV z calej Polski, sluzace do budowania bazy cen rynkowych podobnych modeli.
2. Tryb Lodz: osobne, czestsze wyszukiwanie ofert z Lodzi i okolic, porownujace lokalne oferty z baza ogolnopolska i wskazujace okazje do flipu.

## 2. Problem

Reczne przegladanie ofert TV na OLX jest czasochlonne, szczegolnie gdy trzeba sprawdzac wiele rozmiarow, przedzialow cenowych i kolejnych stron wynikow. Dobre okazje moga znikac szybko, dlatego reczne sprawdzanie raz na jakis czas nie daje wystarczajacej przewagi przy flipowaniu telewizorow dla zysku.

Atrakcyjnosc oferty zalezy nie tylko od ceny, ale tez od rozmiaru, marki, modelu, stanu, lokalizacji, opisu, kompletnosci zestawu i czerwonych flag typu "uszkodzona matryca". Jedno szerokie wyszukiwanie miesza oferty potencjalnie dochodowe z ofertami uszkodzonymi, drogimi, niepelno opisanymi albo zbyt oddalonymi.

Problemem jest tez powtarzalnosc analizy. Te same kryteria trzeba stosowac do wielu segmentow rynku: innych dla 32 cali, innych dla 55 cali, innych dla 65 cali, OLED/QLED itd. Bez automatyzacji trudno regularnie porownywac oferty i nie przegapiac tych, ktore maja potencjal na profit.

Narzedzie ma zautomatyzowac zbieranie, porzadkowanie i wstepna ocene ofert, zostawiajac uzytkownikowi finalna decyzje biznesowa: czy dana oferta nadaje sie do zakupu i pozniejszej odsprzedazy z zyskiem.

## 3. Zakres MVP

Poniższy zakres dotyczy pierwszej kategorii: telewizorów. Obsługa kolejnych kategorii jest celem produktu po MVP; obecny kod nie udostępnia jeszcze wyboru kategorii.

MVP obejmuje:

- OLX jako jedyne zrodlo ofert.
- Wyszukiwania publicznych ofert bez logowania.
- Wyszukiwania ofert z calej Polski.
- Profile wyszukiwania roznicowane jedynie rozmiarem TV.
- Globalny, wspolny dla wszystkich profili zakres ceny.
- Globalne filtrowanie pod oferty prywatne.
- Globalne filtrowanie pod oferty uzywane.
- Pobieranie stron wynikow wyszukiwania.
- Zbieranie linkow do ofert z kazdej strony wynikow.
- Otwieranie stron szczegolow ofert.
- Pobieranie danych ze stron ofert, w tym pelnego opisu.
- Przechodzenie po kolejnych stronach wynikow.
- Dedupikacje ofert.
- Zapis danych i historii ofert w bazie.
- Budowanie ogolnopolskiej bazy cen podobnych modeli TV.
- Tworzenie klucza porownania ofert, np. marka, model, rozmiar, technologia i rozdzielczosc.
- Reguly i ustawienia edytowalne w prostym panelu webowym.
- Prosty panel administracyjny do konfiguracji filtrow, profili rozmiarow, scoringu i regul opisowych.
- Wykrywanie czerwonych flag i pozytywnych cech z tytulu oraz opisu.
- Scoring porownawczy oparty o roznice ceny wzgledem podobnych ofert z calej Polski.
- Eksport do pliku Excel.
- Excel zawierajacy pelny opis, link, cene, lokalizacje, status, score i dopasowane reguly.
- Arkusz `Lodz alerty` jako czesc MVP.
- Profile wyszukiwania dla Lodzi i okolic, oparte na tych samych rozmiarach i globalnych filtrach.
- Wstepna logika alertow Lodz w Excelu, bez zewnetrznych powiadomien push.
- Przygotowanie architektury tak, aby system mogl dzialac lokalnie albo na serwerze.
- Podstawowa obsluga limitow i stabilnosci scrapera: opoznienia, jitter, retry, backoff, limity requestow oraz zatrzymanie skanu po wykryciu CAPTCHA lub blokady.

## 4. Poza zakresem MVP

MVP nie obejmuje:

- Scrapingu Facebook Marketplace.
- Logowania do OLX.
- Pobierania danych kontaktowych sprzedawcy.
- Obchodzenia CAPTCHA, aktywnych blokad lub zabezpieczen OLX.
- Rotacji proxy lub udawania wielu uzytkownikow.
- Automatycznego wysylania wiadomosci do sprzedawcow.
- Zewnetrznych powiadomien push, np. Telegram, Discord, email, SMS.
- Pelnej wyceny AI na podstawie zdjec.
- Analizy zdjec ofert.
- Pelnej predykcji ceny odsprzedazy na podstawie historii transakcji.
- Integracji z platnymi API.
- Rozbudowanego dashboardu analitycznego albo publicznego panelu wielouzytkownikowego.
- Zaawansowanego systemu rol i uprawnien uzytkownikow.
- Produkcyjnego wdrozenia harmonogramu na serwerze z monitoringiem.

## 5. Zalozenia operacyjne

- MVP moze dzialac lokalnie na komputerze uzytkownika.
- Docelowo system powinien dzialac na serwerze, VPS albo innym stale dzialajacym srodowisku.
- System powinien byc mozliwy do uruchomienia jedna komenda.
- System nie powinien wymagac recznego klikania w przegladarce.
- Dane trwale sa zapisywane w bazie, a Excel jest raportem generowanym z bazy.
- Pliki raportowe moga byc zapisywane lokalnie, na serwerze lub w innym miejscu wybranym w konfiguracji.
- Glownym formatem raportowym jest `.xlsx`.
- Konfiguracja wyszukiwan, scoringu i regul opisowych powinna byc edytowalna w prostym panelu webowym.
- Pliki konfiguracyjne moga istniec jako techniczny seed, eksport, backup albo fallback developerski, ale nie powinny byc glownym sposobem codziennej obslugi systemu.
- System powinien dzialac spokojnie i konserwatywnie, z limitami czestotliwosci pobierania.
- System ma korzystac z publicznie dostepnych stron wynikow i stron ofert.
- Kazda oferta powinna byc zapisana z data pierwszego i ostatniego wykrycia.
- System powinien prowadzic logi przebiegow, bledow i statystyk.
- Scraper powinien byc odporny na czesciowe zmiany HTML OLX.
- System powinien pozwalac uruchomic osobno: skan ogolnopolski, skan Lodzi, eksport Excela i test regul.

## 6. Wazne ograniczenia

OLX API nie jest traktowane jako realne zrodlo danych dla tego projektu, poniewaz oficjalne FAQ OLX wskazuje, ze API nie sluzy do czytania cudzych ogloszen, tylko do pracy na ogloszeniach wlasnego konta.

System ma pobierac publicznie dostepne strony wynikow i publiczne strony ofert. Nie zakladamy logowania ani dostepu do danych prywatnych.

Dozwolona jest podstawowa obsluga stabilnosci scrapera:

- opoznienia pomiedzy requestami,
- losowy jitter,
- retry po tymczasowych bledach,
- backoff po serii bledow,
- limity requestow,
- wykrycie CAPTCHA lub blokady i zatrzymanie skanu.

Scraper nie powinien:

- wchodzic w obszary wymagajace konta,
- pobierac endpointow kontaktowych,
- pobierac numerow telefonow lub prywatnych danych sprzedawcy,
- obchodzic CAPTCHA,
- ignorowac blokad serwisu,
- wykonywac agresywnych zapytan,
- rotowac proxy,
- udawac wielu uzytkownikow,
- korzystac z niepublicznych endpointow, jesli nie sa potrzebne do publicznych wynikow.

## 7. Glowny przeplyw danych

1. System wczytuje konfiguracje globalna, profile rozmiarow, reguly opisowe i scoring.
2. Uzytkownik wybiera tryb uruchomienia: `national`, `lodz_alerts`, konkretny profil, eksport albo test regul.
3. System wybiera aktywne profile rozmiarow dla danego trybu.
4. Dla kazdego profilu buduje URL OLX z globalnymi filtrami: cena, oferta prywatna, stan uzywane.
5. Pobiera pierwsza strone wynikow.
6. Parsuje oferty z listy wynikow.
7. Zapisuje podstawowe dane ofert i informacje o profilu, ktory je znalazl.
8. Dla kazdej oferty sprawdza dedupikacje po OLX ID lub URL.
9. Dla nowych, zmienionych lub potencjalnie ciekawych ofert pobiera strone szczegolow.
10. Parsuje dane szczegolowe z oferty.
11. Normalizuje cene, lokalizacje, rozmiar, marke, model, technologie i stan.
12. Tworzy `comparable_key`, czyli klucz porownania podobnych ofert.
13. Uruchamia reguly opisowe na tytule, opisie i parametrach.
14. Zapisuje dopasowane reguly.
15. Dla trybu `national` aktualizuje baze cen rynkowych podobnych ofert.
16. Dla trybu `lodz_alerts` porownuje oferte z baza ogolnopolska.
17. Wylicza scoring, szacowany profit, pewnosc porownania i status oferty.
18. Dla trybu `lodz_alerts` sprawdza, czy oferta kwalifikuje sie do arkusza `Lodz alerty`.
19. Przechodzi do kolejnej strony wynikow.
20. Konczy profil po spelnieniu warunkow stopu.
21. Po zakonczeniu wszystkich profili zapisuje podsumowanie przebiegu.
22. Eksportuje aktualny widok do Excela.

Excel jest eksportowany po zakonczeniu skanu, a nie po kazdej stronie wynikow. Dzieki temu raport pokazuje spojny stan po calym przebiegu.

## 8. Strategia wyszukiwan ogolnopolskich

Nie nalezy opierac calego systemu tylko na jednym szerokim wyszukiwaniu "telewizory, cala Polska", poniewaz OLX moze ograniczac liczbe widocznych wynikow i stron. Zamiast tego system powinien wykonywac wiele mniejszych wyszukiwan opartych o natywny filtr rozmiaru TV dostepny na OLX.

Tryb ogolnopolski ma dwa zadania:

- zebrac aktualne oferty z rynku w zadanym zakresie ceny,
- zbudowac baze porownawcza cen podobnych modeli TV, ktora pozniej sluzy do scoringu ofert z Lodzi.

W MVP profile wyszukiwania roznia sie jedynie rozmiarem TV. Pozostale filtry sa globalne i wspolne dla wszystkich profili:

- lokalizacja: cala Polska,
- zakres ceny: 300-700 PLN,
- typ sprzedawcy: prywatne,
- stan: uzywane,
- sortowanie: najnowsze,
- kategoria: elektronika / TV / telewizory,
- kazdy profil ma wlasny limit stron.

Na aktualnej stronie OLX filtr `Rozmiar` dla kategorii Telewizory udostepnia nastepujace wartosci:

- `Mniejszy niz 30 cali`,
- `30-39`,
- `40-49`,
- `50-59`,
- `60-69`,
- `70-79`,
- `Wiekszy niz 80 cali`.

Adapter OLX powinien korzystac z natywnego parametru filtra rozmiaru, a nie tylko z wyszukiwania tekstowego. Przykladowo zakres `40-49` jest reprezentowany w URL jako:

```text
search[filter_enum_size][0]=40-49
```

### 8.1. Profile rozmiarow MVP

Proponowane profile rozmiarow MVP odpowiadaja wartosciom filtra OLX:

- `lt_30` - mniejszy niz 30 cali,
- `30_39` - 30-39 cali,
- `40_49` - 40-49 cali,
- `50_59` - 50-59 cali,
- `60_69` - 60-69 cali,
- `70_79` - 70-79 cali,
- `gt_80` - wiekszy niz 80 cali.

Kazdy profil rozmiaru moze dodatkowo miec pomocnicze frazy tekstowe, ale nie powinny one byc glownym mechanizmem filtrowania. Glownym mechanizmem filtrowania jest natywny filtr OLX `Rozmiar`.

### 8.2. Globalny zakres ceny

W MVP zakres ceny jest globalny i wspolny dla wszystkich profili rozmiarow.

Zakres startowy:

- `price_min`: 300 PLN,
- `price_max`: 700 PLN.

Zakres ceny powinien byc edytowalny w panelu ustawien. Jesli pozniej okaze sie, ze wspolny zakres ceny jest zbyt szeroki lub zbyt waski dla konkretnych rozmiarow, mozna dodac osobne zakresy per profil w kolejnej wersji.

Na OLX cena moze byc reprezentowana w URL jako:

```text
search[filter_float_price:from]=300
search[filter_float_price:to]=700
```

### 8.3. Globalny typ sprzedawcy i stan

W MVP wszystkie profile korzystaja z tych samych filtrow:

- typ sprzedawcy: prywatne,
- stan: uzywane.

Na OLX stan `Uzywane` moze byc reprezentowany w URL jako:

```text
search[filter_enum_state][0]=used
```

Typ sprzedawcy `Prywatne` moze byc reprezentowany w URL jako:

```text
search[private_business]=private
```

### 8.4. Dlaczego wiele wyszukiwan

Wiele mniejszych wyszukiwan daje:

- wieksza szanse zobaczenia ofert, ktore zniknelyby za limitem wynikow,
- lepsza kontrole nad liczba stron,
- latwiejsze porownywanie ofert w konkretnych segmentach rozmiarowych,
- prostsze reguly scoringu per zakres rozmiaru,
- mniejsze ryzyko pobierania zbyt wielu nieistotnych ofert.

## 9. Panel ustawien i konfiguracja wyszukiwania

Konfiguracja wyszukiwania powinna byc zarzadzana z prostego panelu webowego. Panel powinien zapisywac ustawienia w bazie danych albo w plikach konfiguracyjnych generowanych przez aplikacje. Uzytkownik nie powinien musiec edytowac plikow recznie na serwerze.

Panel ustawien MVP powinien obslugiwac:

- globalny zakres ceny,
- globalny typ sprzedawcy,
- globalny stan oferty,
- wlaczanie i wylaczanie profili rozmiarow,
- tryb `national`,
- tryb `lodz_alerts`,
- promien i lokalizacje dla Lodzi,
- limity stron na profil,
- progi alertow,
- progi scoringu,
- reguly opisowe,
- eksport i import ustawien technicznych.

Konfiguracja powinna byc logicznie rozdzielona na ustawienia globalne oraz profile rozmiarow.

Profile rozmiarow nie zawieraja ceny, stanu ani typu sprzedawcy. Te wartosci sa trzymane globalnie, aby zmiana zakresu ceny albo typu ofert nie wymagala edycji kazdego profilu osobno.

Pliki typu YAML moga istniec jako format techniczny:

- seed poczatkowych ustawien,
- backup,
- eksport/import konfiguracji,
- fallback developerski.

Nie sa glownym miejscem codziennej edycji ustawien przez uzytkownika.

Przykladowy techniczny eksport konfiguracji globalnej:

```yaml
source: olx
category: telewizory

global_filters:
  price_min: 300
  price_max: 700
  seller_type: private
  condition: used
  sort: newest
  fetch_details: true

modes:
  national:
    enabled: true
    location: all_poland
    max_pages_per_profile: 25

  lodz_alerts:
    enabled: true
    location: lodz
    radius_km: 50
    max_pages_per_profile: 5
    alert_min_score: 75
    alert_min_estimated_profit: 150
```

Przykladowy techniczny eksport profili rozmiarow:

```yaml
size_profiles:
  - id: lt_30
    enabled: true
    label: "Mniejszy niz 30 cali"
    olx_size_filter: "lt-30"

  - id: 30_39
    enabled: true
    label: "30-39 cali"
    olx_size_filter: "30-39"

  - id: 40_49
    enabled: true
    label: "40-49 cali"
    olx_size_filter: "40-49"

  - id: 50_59
    enabled: true
    label: "50-59 cali"
    olx_size_filter: "50-59"

  - id: 60_69
    enabled: true
    label: "60-69 cali"
    olx_size_filter: "60-69"

  - id: 70_79
    enabled: true
    label: "70-79 cali"
    olx_size_filter: "70-79"

  - id: gt_80
    enabled: true
    label: "Wiekszy niz 80 cali"
    olx_size_filter: "gt-80"
```

Uwaga: dokladne parametry URL OLX powinny byc zaimplementowane w warstwie adaptera OLX, a nie wpisywane recznie w kazdym profilu. Wartosci `40-49`, `50-59`, `60-69` i `70-79` zostaly potwierdzone na stronie OLX jako wartosci filtra rozmiaru. Techniczne wartosci dla skrajnych zakresow `Mniejszy niz 30 cali` i `Wiekszy niz 80 cali` nalezy potwierdzic przy implementacji, poniewaz moga roznic sie od etykiet widocznych w interfejsie.

## 10. Paginacja

System ma obslugiwac kolejne strony wynikow wyszukiwania dla kazdego profilu rozmiaru i trybu pracy.

Preferowany sposob:

1. Pobierz aktualna strone wynikow.
2. Sparsuj oferty oraz element paginacji.
3. Sprobuj znalezc link `Dalej` w HTML.
4. Jesli link istnieje, uzyj go jako adresu nastepnej strony, poniewaz zawiera aktualne filtry OLX.
5. Jesli link nie istnieje, zakoncz dany profil.
6. Jesli kolejna strona zawiera te same oferty co poprzednia, zakoncz dany profil jako ochrone przed petla.

Fallback:

- Buduj adres kolejnej strony przez parametr `page`, np. `?page=2`, `?page=3`.
- Fallback musi zachowac wszystkie aktualne parametry filtrow: rozmiar, cena, stan, typ sprzedawcy, lokalizacja i sortowanie.

System nie powinien isc po stronach bez limitu.

Domyslne limity:

- `national`: maksymalnie 25 stron na profil rozmiaru,
- `lodz_alerts`: maksymalnie 5 stron na profil rozmiaru.

### 10.1. Warunki stopu paginacji

Profil wyszukiwania konczy prace, gdy wystapi jeden z warunkow:

- brak ofert na stronie,
- brak linku do kolejnej strony,
- osiagnieto `max_pages`,
- strona zwraca blad HTTP,
- wykryto blokade lub CAPTCHA,
- nastepna strona ma taki sam zestaw URL-i ofert jak poprzednia,
- kilka kolejnych stron zawiera wylacznie znane oferty,
- liczba kolejnych znanych ofert przekroczy prog, np. 80% strony,
- parser nie potrafi znalezc zadnej oferty mimo widocznej strony wynikow,
- oferty na stronie sa starsze niz skonfigurowany horyzont czasowy.

## 11. Dane pobierane z listy wynikow

Ze strony wynikow nalezy pobierac:

- URL oferty,
- URL kanoniczny, jesli mozliwy do ustalenia,
- ID oferty, jesli mozliwe do wyciagniecia z URL lub HTML,
- tytul,
- cena jako liczba,
- surowy tekst ceny,
- czy cena jest do negocjacji, jesli widoczne,
- miasto,
- dzielnica, jesli widoczna,
- region, jesli widoczny,
- surowy tekst lokalizacji,
- data widoczna na liscie,
- miniatura,
- informacja o stanie, jesli widoczna,
- informacja o promowaniu, jesli widoczna,
- informacja o profilu firmowym, jesli widoczna mimo filtra prywatnego,
- tryb skanu: `national` albo `lodz_alerts`,
- ID profilu rozmiaru,
- URL strony wynikow,
- numer strony wynikow,
- pozycja oferty na stronie,
- czas pobrania,
- ostrzezenia parsera.

Dane z listy wynikow sa szybkim filtrem. Moga sluzyc do deduplikacji, wstepnego odrzucenia i decyzji, czy pobierac szczegoly. Nie sa wystarczajace do finalnego scoringu, poniewaz pelny opis, parametry i czesc czerwonych flag znajduja sie dopiero na stronie oferty.

## 12. Dane pobierane ze strony oferty

Ze strony szczegolow oferty nalezy pobierac:

- URL kanoniczny,
- ID oferty,
- tytul,
- surowy tytul,
- cena jako liczba,
- surowy tekst ceny,
- czy cena jest do negocjacji, jesli widoczne,
- lokalizacja,
- miasto,
- dzielnica, jesli widoczna,
- region, jesli widoczny,
- data dodania lub odswiezenia,
- pelny opis,
- surowy opis,
- parametry oferty,
- surowe parametry oferty,
- stan,
- typ sprzedawcy, jesli widoczny,
- nazwa sprzedawcy, jesli publicznie widoczna,
- URL profilu sprzedawcy, jesli publicznie widoczny,
- liczba zdjec,
- URL glownego zdjecia,
- wykryta marka,
- wykryty model,
- wykryty rozmiar,
- wykryta technologia ekranu,
- wykryta rozdzielczosc,
- informacja czy jest pilot, jesli wynika z tekstu,
- informacja czy jest podstawka/nogi, jesli wynika z tekstu,
- informacja czy jest pudelko, jesli wynika z tekstu,
- informacja o odbiorze osobistym lub dostawie, jesli wynika z tekstu,
- czy oferta jest niedostepna/usunieta,
- ostrzezenia parsera.

Nie pobieramy:

- numeru telefonu,
- adresu e-mail,
- prywatnych danych kontaktowych,
- danych wymagajacych logowania,
- endpointow kontaktowych.

## 13. Normalizacja danych

System powinien normalizowac:

- cene do liczby,
- surowy tekst ceny,
- informacje czy cena jest do negocjacji,
- rozmiar w calach,
- zakres rozmiaru OLX,
- miasto,
- dzielnice,
- wojewodztwo,
- lokalizacje pod potrzeby trybu `lodz_alerts`,
- marke,
- model,
- technologie ekranu,
- rozdzielczosc,
- stan,
- typ sprzedawcy,
- date widoczna na OLX,
- date pierwszego wykrycia,
- date ostatniego wykrycia,
- date pobrania listy wynikow,
- date pobrania szczegolow,
- informacje o pilocie,
- informacje o podstawce/nogach,
- informacje o pudelku,
- informacje o odbiorze osobistym lub dostawie,
- klucz porownania ofert `comparable_key`,
- pewnosc dopasowania modelu `comparison_confidence`,
- dopasowane reguly opisowe,
- status oferty.

### 13.1. Rozmiar TV

System przechowuje dwa rodzaje informacji o rozmiarze:

- `olx_size_bucket` - zakres rozmiaru wynikajacy z profilu wyszukiwania OLX, np. `40-49`,
- `detected_size_inches` - konkretny rozmiar wykryty z tytulu, opisu lub parametrow oferty, np. `43`.

`olx_size_bucket` sluzy do organizacji skanow, a `detected_size_inches` sluzy do scoringu, tworzenia grup porownawczych i oceny oplacalnosci.

Rozmiar moze byc wykrywany z:

- tytulu,
- opisu,
- parametrow OLX,
- zakresu rozmiaru profilu wyszukiwania.

Przykladowe wzorce:

- `55 cali`,
- `55"`,
- `55 cal`,
- `55cali`,
- `55 inch`,
- `UE55`,
- `OLED55`,
- `55PUS`.

Jesli wykryto kilka rozmiarow, system powinien zapisac:

- `detected_size_inches`,
- `size_confidence`,
- `size_detection_source`.

### 13.2. Cena

Cena powinna byc zapisana jako liczba w PLN. System powinien rozpoznawac:

- `450 zl`,
- `1 200 zl`,
- `555,50 zl`,
- `Za darmo`,
- `do negocjacji`.

Oferty `Za darmo` powinny byc zapisane jako `price = 0`, ale oznaczone flaga `is_free = true`. W MVP globalny filtr ceny `300-700` powinien zwykle odsiac takie oferty, ale parser powinien umiec je obsluzyc na wypadek zmian filtrow lub niespojnosci wynikow OLX.

## 14. Reguly opisowe

Reguly opisowe maja byc edytowalne w prostym panelu webowym, bez zmiany kodu i bez recznego logowania sie na serwer. Panel powinien pozwalac dodawac, edytowac, wlaczac, wylaczac i testowac reguly.

Techniczny plik `config/description_rules.yml` moze istniec jako seed, eksport, backup albo fallback developerski, ale nie jest glownym miejscem codziennej edycji regul przez uzytkownika.

Panel regul MVP powinien pozwalac ustawic:

- `id`,
- `enabled`,
- `category`,
- `severity`,
- `label`,
- `applies_to`,
- `match_mode`,
- `patterns`,
- `score_delta`,
- `action`.

Panel powinien miec tez funkcje testu reguly na przykladowym tekscie oferty, aby przed zapisem zobaczyc, czy frazy dopasowuja sie zgodnie z oczekiwaniem.

Reguly powinny dzialac na:

- tytule,
- opisie,
- parametrach,
- polaczonym tekscie oferty.

System powinien zapisywac nie tylko fakt dopasowania reguly, ale tez miejsce dopasowania:

- `title`,
- `description`,
- `parameters`,
- `combined_text`.

### 14.1. Kategorie regul

Proponowane kategorie:

- `red_flag`: powazne ryzyko lub wada,
- `warning`: wymaga sprawdzenia,
- `positive`: cecha pozytywna,
- `exclude`: powod automatycznego odrzucenia,
- `info`: neutralna informacja do pokazania w Excelu.

### 14.2. Przykladowy format regul

```yaml
rules:
  - id: damaged_matrix
    enabled: true
    category: red_flag
    severity: high
    label: "Mozliwie uszkodzona matryca"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "uszkodzona matryca"
      - "zbita matryca"
      - "peknieta matryca"
      - "pasy na ekranie"
      - "linie na ekranie"
    score_delta: -80
    action: flag

  - id: screen_lines
    enabled: true
    category: red_flag
    severity: high
    label: "Pasy lub linie na ekranie"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "pasy na ekranie"
      - "linie na ekranie"
      - "pionowe pasy"
      - "poziome pasy"
    score_delta: -80
    action: flag

  - id: no_image
    enabled: true
    category: exclude
    severity: critical
    label: "Brak obrazu"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "brak obrazu"
      - "nie ma obrazu"
      - "czarny ekran"
    score_delta: -100
    action: reject

  - id: no_remote
    enabled: true
    category: warning
    severity: low
    label: "Brak pilota"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "brak pilota"
      - "bez pilota"
    score_delta: -10
    action: flag

  - id: no_stand
    enabled: true
    category: warning
    severity: low
    label: "Brak podstawy"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "bez podstawy"
      - "brak podstawki"
      - "bez nogi"
      - "bez nozek"
    score_delta: -10
    action: flag

  - id: has_remote
    enabled: true
    category: positive
    severity: low
    label: "Pilot w zestawie"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "z pilotem"
      - "pilot w zestawie"
      - "oryginalny pilot"
    score_delta: 8
    action: flag

  - id: not_turning_on
    enabled: true
    category: exclude
    severity: critical
    label: "Telewizor sie nie wlacza"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "nie wlacza sie"
      - "nie odpala"
      - "martwy"
      - "brak zasilania"
    score_delta: -100
    action: reject

  - id: oled
    enabled: true
    category: positive
    severity: medium
    label: "OLED"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "oled"
    score_delta: 20
    action: flag

  - id: four_k
    enabled: true
    category: positive
    severity: low
    label: "4K"
    applies_to:
      - title
      - description
      - parameters
    match_mode: phrase
    patterns:
      - "4k"
      - "ultra hd"
      - "uhd"
    score_delta: 10
    action: flag

  - id: service_offer
    enabled: true
    category: exclude
    severity: critical
    label: "To moze byc usluga serwisowa, nie telewizor"
    applies_to:
      - title
      - description
    match_mode: phrase
    patterns:
      - "wymiana matryc"
      - "wymiana matrycy"
      - "naprawa telewizorow"
      - "serwis telewizorow"
      - "naprawiam telewizory"
    score_delta: -100
    action: reject
```

### 14.3. Zasady dzialania regul

- Reguly sa niewrazliwe na wielkosc liter.
- Domyslny tryb dopasowania to zwykla fraza.
- Reguly powinny opcjonalnie wspierac regex przez `match_mode: regex`.
- Kazde dopasowanie zapisuje sie w bazie.
- Kazde dopasowanie zapisuje zrodlo dopasowania, np. tytul, opis albo parametry.
- W Excelu widac liste dopasowanych regul.
- Regula moze obnizac albo podwyzszac score.
- Regula moze oznaczyc oferte jako odrzucona.
- Regula moze tylko dodac etykiete informacyjna.
- Regula moze zostac wlaczona albo wylaczona bez zmiany kodu.
- Dostepne akcje MVP: `flag`, `reject`, `boost`, `info`.

### 14.4. Reguly zamiast AI w MVP

W MVP AI nie jest wymagane do wykrywania wad z opisu. Wiele przypadkow da sie wykryc prostymi regulami.

AI moze zostac dodane pozniej jako dodatkowa warstwa klasyfikacji dla ofert, ktore:

- maja dobry potencjal cenowy,
- ale opis jest niejednoznaczny,
- albo wymagaja streszczenia i oceny ryzyka.

### 14.5. Minimalny zestaw regul MVP

Minimalny zestaw regul MVP powinien obejmowac:

- matryca i ekran: zbita/uszkodzona matryca, pasy, linie, plamy, martwe piksele, brak podswietlenia,
- zasilanie i uruchamianie: nie wlacza sie, brak zasilania, martwy, restartuje sie,
- obraz i dzwiek: brak obrazu, czarny ekran, brak dzwieku,
- komplet zestawu: brak pilota, brak podstawki/nog, uchwyt zamiast podstawki, brak kabla,
- stan wizualny: rysy, pekniecia, uszkodzona obudowa,
- pozytywne technologie: OLED, QLED, MiniLED, 4K, UHD, Ambilight, 120 Hz,
- odbior i logistyka: odbior osobisty, mozliwy dowoz, wysylka,
- anty-oferty: naprawa, serwis, wymiana matryc, czesci, hurt, wiele sztuk, rezerwacja.

## 15. Scoring ofert

Scoring ofert powinien opierac sie przede wszystkim na porownaniu danej oferty z podobnymi ofertami znalezionymi w skanie ogolnopolskim. Celem nie jest prosta ocena typu "wiekszy telewizor jest lepszy", tylko wykrycie sytuacji, w ktorej konkretny model albo bardzo podobny telewizor jest wystawiony znacznie taniej niz typowa cena rynkowa.

Przyklad:

- system znajduje w Polsce oferty typu `Samsung 40 cali OLED` w okolicach 1000 PLN,
- potem w Lodzi pojawia sie podobna oferta za 500 PLN,
- oferta lodzka dostaje wysoki scoring, poniewaz cena jest znaczaco nizsza od porownywalnych ofert.

Tryb ogolnopolski sluzy glownie do budowania bazy cen i porownan rynkowych. Tryb `lodz_alerts` sluzy do wykrywania okazji na podstawie tej bazy.

Przykladowa skala:

- `90-100`: bardzo mocna okazja,
- `70-89`: potencjalna okazja,
- `50-69`: do recznej weryfikacji,
- `20-49`: slaba oferta,
- `0-19`: odrzucic,
- ponizej `0`: prawdopodobnie problematyczna lub niezgodna z celem.

### 15.1. Skladniki scoringu MVP

MVP scoring powinien uwzgledniac:

- cene oferty,
- typowa cene podobnych ofert z calej Polski,
- procentowa roznice wzgledem ceny referencyjnej,
- szacowany profit,
- pewnosc dopasowania modelu,
- liczbe porownywalnych ofert,
- rozmiar,
- marke,
- model,
- technologie ekranu,
- stan,
- czerwone flagi z opisu,
- pozytywne cechy z opisu,
- lokalizacje,
- swiezosc oferty,
- komplet informacji.

### 15.2. Klucz porownania ofert

System powinien probowac grupowac oferty tak, aby porownywac mozliwie te same modele z tymi samymi modelami.

Najlepszy przypadek:

- ta sama marka,
- ten sam lub bardzo podobny model,
- ten sam rozmiar,
- ta sama technologia ekranu,
- podobny stan.

Fallback, gdy model nie jest jednoznaczny:

- ta sama marka,
- ten sam rozmiar,
- podobna technologia,
- podobna rozdzielczosc,
- podobny zakres wieku/modelu, jesli mozliwy do wykrycia.

System powinien tworzyc pole `comparable_key`, np.:

```text
samsung|ue40xxxx|40|led|full_hd
samsung|unknown|40|oled|unknown
lg|43up78003lb|43|led|4k
```

Jesli nie da sie ustalic modelu, system powinien zapisac nizsza pewnosc porownania i uzyc szerszej grupy porownawczej.

### 15.3. Baza cen rynkowych

Skan ogolnopolski powinien budowac baze cen podobnych ofert. Dla kazdego `comparable_key` system powinien zapisywac:

- liczbe porownywalnych ofert,
- minimalna cene,
- mediane ceny,
- srednia cene,
- percentyl 25,
- percentyl 75,
- date ostatniego odswiezenia,
- liste ofert uzytych do porownania.

Cena referencyjna powinna bazowac przede wszystkim na medianie albo ostroznej medianie po odrzuceniu skrajnych wartosci. Oferty odrzucone regulami `exclude`, oferty uszkodzone i anty-oferty serwisowe nie powinny budowac normalnej ceny rynkowej sprawnego telewizora.

### 15.4. Scoring porownawczy

Scoring powinien premiowac oferty, ktore sa tansze od ceny referencyjnej dla podobnego modelu.

Przykladowe wartosci:

```text
market_discount_percent = (reference_price - offer_price) / reference_price
estimated_profit = expected_resale_price - offer_price - estimated_costs
expected_resale_price = reference_price * resale_safety_factor
```

Przykladowy `resale_safety_factor`:

- 0.85 albo 0.90, aby nie zakladac sprzedazy dokladnie po medianie rynku.

Przykladowe progi:

- rabat 10-19% wzgledem rynku: lekki sygnal,
- rabat 20-34% wzgledem rynku: kandydat,
- rabat 35-49% wzgledem rynku: okazja,
- rabat 50%+ wzgledem rynku: bardzo mocna okazja.

Oferta z regula `exclude` powinna dostac status `rejected` niezaleznie od rabatu.

### 15.5. Pewnosc porownania

Kazda oferta powinna miec `comparison_confidence`, poniewaz nie kazde dopasowanie bedzie tak samo mocne.

Przykladowa skala:

- `high`: wykryto marke, model, rozmiar i podobne parametry,
- `medium`: wykryto marke, rozmiar i technologie, ale model jest niepewny,
- `low`: wykryto tylko czesc parametrow i porownanie jest szerokie,
- `none`: brak sensownej grupy porownawczej.

Oferta moze byc okazja tylko wtedy, gdy:

- ma wystarczajaca pewnosc porownania,
- ma wystarczajaca liczbe porownywalnych ofert,
- nie ma krytycznych czerwonych flag.

Jesli porownanie jest slabe, oferta powinna dostac status `needs_review`, a nie automatycznie `opportunity`.

### 15.6. Statusy scoringu

Proponowane statusy:

- `opportunity`: duzy rabat wzgledem rynku, dobra pewnosc porownania, brak `exclude`,
- `candidate`: umiarkowany rabat albo srednia pewnosc porownania,
- `needs_review`: potencjalnie ciekawa, ale brakuje danych albo opis jest niejednoznaczny,
- `market_reference`: oferta ogolnopolska uzywana glownie do budowania bazy cen,
- `weak`: brak rabatu wzgledem rynku,
- `rejected`: regula `exclude`, powazna wada albo cena nie ma sensu wzgledem ryzyka.

### 15.7. Szacowany profit

Docelowo system powinien wyliczac:

```text
estimated_profit = estimated_resale_price - offer_price - estimated_costs
```

Gdzie `estimated_costs` moze obejmowac:

- paliwo/transport,
- czas,
- ewentualne braki,
- ryzyko naprawy,
- bufor negocjacyjny.

W MVP `estimated_profit` powinien byc liczony wtedy, gdy istnieje wystarczajaca grupa porownawcza. Jesli system nie ma wystarczajacych danych o podobnych ofertach, `estimated_profit` moze byc pusty, a oferta powinna trafic do recznej weryfikacji.

## 16. Excel

Excel jest raportem generowanym z bazy danych. Nie jest miejscem konfiguracji systemu i nie powinien byc glownym miejscem recznej edycji regul, filtrow, progow scoringu ani profili wyszukiwania. Te elementy sa zarzadzane w panelu webowym.

Glowne pliki raportowe:

- `output/oferty_tv_latest.xlsx` - zawsze najnowszy raport, nadpisywany przy eksporcie,
- `output/archive/oferty_tv_YYYY-MM-DD_HH-MM.xlsx` - opcjonalny snapshot historyczny, jesli archiwizacja eksportow jest wlaczona.

Raport powinien byc generowany po kazdym pelnym przebiegu albo na zadanie.

### 16.1. Zasada nadpisywania

Plik `oferty_tv_latest.xlsx` jest budowany od nowa przy kazdym eksporcie na podstawie danych z bazy. Reczne zmiany wykonane bezposrednio w tym pliku nie sa traktowane jako trwale i moga zostac nadpisane przy kolejnym eksporcie.

Reczne decyzje uzytkownika, np. "sprawdzone", "kontaktowalem sie", "kupione", "ignoruj", "notatka", powinny byc zapisywane w panelu webowym i bazie danych. Excel moze pokazywac te decyzje jako kolumny raportowe, ale nie jest ich zrodlem prawdy.

### 16.2. Arkusze

Arkuszy powinno byc malo, zeby raport byl latwy do czytania.

- `Oferty` - wszystkie aktualnie znane oferty z ostatniego eksportu, z kolumna `status` i filtrami.
- `Lodz alerty` - lokalne oferty z Lodzi i okolic, ktore spelniaja warunki alertu.
- `Baza cen` - statystyki grup porownawczych per `comparable_key`.
- `Historia skanow` - daty, profile, liczba ofert, bledy.

Nie tworzymy osobnych arkuszy `Okazje`, `Do sprawdzenia` i `Odrzucone` w MVP. Te widoki powinny wynikac z filtrow w arkuszu `Oferty` oraz z kolumn `status`, `score`, `reject_reasons` i `matched_red_flags`.

Nie tworzymy arkusza `Reguly` jako miejsca konfiguracji. Reguly sa edytowane w panelu webowym. Excel pokazuje jedynie wynik dopasowania regul przy konkretnych ofertach.

### 16.3. Kolumny w arkuszu `Oferty`

Minimalne kolumny:

- `score`,
- `status`,
- `reason`,
- `estimated_profit`,
- `market_discount_percent`,
- `reference_price`,
- `expected_resale_price`,
- `estimated_costs`,
- `comparison_confidence`,
- `comparable_offers_count`,
- `comparable_key`,
- `scan_mode`,
- `source`,
- `offer_id`,
- `size_profile_id`,
- `first_seen_at`,
- `last_seen_at`,
- `scraped_at`,
- `title`,
- `price`,
- `raw_price_text`,
- `price_negotiable`,
- `seller_type`,
- `condition`,
- `city`,
- `district`,
- `region`,
- `distance_from_lodz_km`,
- `detected_size_inches`,
- `olx_size_bucket`,
- `brand`,
- `model`,
- `display_technology`,
- `resolution`,
- `has_remote`,
- `has_stand`,
- `has_box`,
- `pickup_or_delivery_hint`,
- `matched_positive_rules`,
- `matched_warning_rules`,
- `matched_red_flags`,
- `reject_reasons`,
- `user_decision`,
- `user_note`,
- `contacted_at`,
- `purchased_at`,
- `ignored_until`,
- `description`,
- `photos_count`,
- `main_photo_url`,
- `url`.

### 16.4. Kolumny w arkuszu `Baza cen`

Minimalne kolumny:

- `comparable_key`,
- `brand`,
- `model`,
- `detected_size_inches`,
- `display_technology`,
- `resolution`,
- `condition`,
- `offers_count`,
- `min_price`,
- `median_price`,
- `average_price`,
- `p25_price`,
- `p75_price`,
- `last_updated_at`,
- `sample_offer_urls`.

### 16.5. Formatowanie Excela

Excel powinien byc czytelny bez dodatkowej obrobki:

- zamrozenie pierwszego wiersza,
- filtry w naglowkach,
- sortowanie domyslne po `score` malejaco,
- w arkuszu `Lodz alerty` sortowanie po `score`, `estimated_profit` i `market_discount_percent`,
- kolorowanie statusow,
- szerokie kolumny dla tytulu i opisu,
- linki klikalne w kolumnie `url`,
- format cen jako PLN,
- osobne kolory dla red flags.

## 17. Baza danych

Excel jest raportem, ale baza danych jest zrodlem prawdy dla systemu. Baza przechowuje oferty, historie zmian, grupy porownawcze, ceny referencyjne, reguly, ustawienia panelu, decyzje uzytkownika oraz historie eksportow.

Proponowana baza:

- SQLite w MVP,
- plik: `data/offers.sqlite`,
- architektura przygotowana tak, aby w przyszlosci mozna bylo przejsc na PostgreSQL bez przepisywania calej logiki biznesowej.

SQLite jest dobrym wyborem na start, poniewaz upraszcza development, lokalne uruchomienie i pierwsze wdrozenie. PostgreSQL moze byc potrzebny pozniej, jesli system bedzie stale dzialal na serwerze, bedzie mial wiecej danych, kilku uzytkownikow albo bardziej rozbudowany panel.

### 17.1. Tabele

Proponowane tabele:

- `offers` - aktualny stan oferty.
- `offer_snapshots` - historia zmian ceny, opisu, statusu i scoringu.
- `comparable_groups` - grupy podobnych ofert tworzone przez `comparable_key`.
- `market_price_references` - mediany, srednie, percentyle i liczba ofert per grupa.
- `search_runs` - przebiegi wyszukiwan.
- `search_profile_runs` - wynik kazdego profilu.
- `description_rules` - reguly opisowe edytowane w panelu.
- `rule_matches` - dopasowania regul do ofert.
- `settings` - globalne ustawienia systemu i panelu.
- `size_profiles` - profile rozmiarow OLX.
- `scoring_settings` - progi scoringu i alertow.
- `user_offer_notes` - decyzje i notatki uzytkownika per oferta.
- `manual_ignored_offers` - oferty ignorowane recznie.
- `alert_events` - historia kwalifikacji do `Lodz alerty`.
- `export_runs` - historia eksportow do Excela.

### 17.2. Dedupikacja

Oferta powinna byc identyfikowana przez:

- OLX ID, jesli dostepne,
- URL kanoniczny,
- fallback: hash z URL.

Ten sam telewizor znaleziony przez kilka profili nie powinien tworzyc duplikatow w Excelu. Zamiast tego zapisujemy liste profili, w ktorych oferta zostala znaleziona.

### 17.3. Dane uzytkownika

Decyzje i notatki uzytkownika powinny byc zapisywane w bazie, a nie w wygenerowanym Excelu.

Przykladowe pola:

- `user_decision` - np. `sprawdzone`, `kontakt`, `kupione`, `ignoruj`,
- `user_note`,
- `contacted_at`,
- `purchased_at`,
- `ignored_until`,
- `manual_priority`.

Excel moze pokazywac te pola, ale ich edycja powinna odbywac sie w panelu webowym.

### 17.4. Migracje

Baza powinna byc wersjonowana migracjami. Zmiany struktury tabel nie powinny wymagac recznego kasowania bazy. W MVP wystarczy prosty system migracji, ale struktura projektu powinna pozwalac na pozniejsze uzycie Alembic albo podobnego narzedzia.

### 17.5. Backup

System powinien pozwalac wykonac backup bazy przed wiekszymi zmianami, eksportem ustawien albo aktualizacja aplikacji.

Minimalne wymagania:

- komenda lub przycisk w panelu do wykonania backupu,
- backup pliku SQLite do katalogu `data/backups/`,
- nazwa backupu zawierajaca date i godzine,
- mozliwosc wyeksportowania ustawien panelu do pliku technicznego.

## 18. Modul Lodz

Modul Lodz jest czescia MVP, ale dziala jako osobny tryb pracy od skanu ogolnopolskiego.

Tryb `lodz_alerts` nie jest osobnym scraperem. Korzysta z tego samego mechanizmu pobierania, parsowania, normalizacji, regul i scoringu co tryb ogolnopolski, ale uzywa innej lokalizacji, mniejszego limitu stron i ostrzejszych kryteriow alertu.

Cel:

- czesciej sprawdzac oferty z Lodzi i okolic,
- porownywac lokalne oferty z ogolnopolska baza cen podobnych modeli,
- wykrywac oferty z potencjalem na flip szybciej niz reczne przegladanie,
- zapisywac okazje w arkuszu `Lodz alerty`.

### 18.1. Wyszukiwania Lodz

Profile Lodz powinny miec:

- `mode: lodz_alerts`,
- lokalizacje Lodz,
- opcjonalny promien wyszukiwania, jesli OLX pozwala go stabilnie ustawic,
- te same profile rozmiarow co tryb ogolnopolski,
- te same globalne filtry ceny, stanu i typu sprzedawcy,
- mniejszy limit stron na profil,
- ostrzejsze kryteria alertu oparte o rabat wzgledem rynku i szacowany profit.

Przykladowa konfiguracja trybu:

```yaml
lodz_alerts:
  enabled: true
  location: lodz
  radius_km: 50
  max_pages_per_profile: 5
  alert_min_score: 75
  alert_min_market_discount_percent: 0.30
  alert_min_estimated_profit: 150
  min_comparable_offers: 3
  min_comparison_confidence: medium
  alert_only_new_or_changed: true
  suppress_repeated_alert_hours: 48
```

Profile rozmiarow dla Lodzi sa pobierane z `config/search_profiles.yml`, np.:

```yaml
size_profiles:
  - id: 40_49
    enabled: true
    label: "40-49 cali"
    olx_size_filter: "40-49"
```

Adapter OLX laczy konfiguracje trybu `lodz_alerts`, globalne filtry oraz aktywne profile rozmiarow w finalne URL-e wyszukiwania.

### 18.2. Warunki alertu

Alert powinien powstac, gdy:

- oferta jest nowa albo istotnie zmieniona,
- oferta jest z Lodzi lub ustawionych okolic,
- oferta ma porownywalna grupe cenowa z calej Polski,
- rabat wzgledem ceny referencyjnej przekracza prog,
- score przekracza prog,
- nie ma regul `exclude`,
- estimated profit przekracza prog, jesli jest liczony,
- pewnosc porownania jest wystarczajaca,
- oferta nie byla alertowana w ostatnich `suppress_repeated_alert_hours`, chyba ze zmienila sie cena albo status.

### 18.3. Kanaly powiadomien

Po MVP mozliwe kanaly:

- email,
- Telegram,
- Discord webhook,
- lokalne powiadomienie systemowe.

W MVP alerty Lodz powinny byc widoczne w arkuszu `Lodz alerty` oraz w panelu webowym. Zewnetrzne powiadomienia push pozostaja poza MVP.

## 19. Harmonogram pracy scrapera

System powinien miec harmonogram uruchomien, ktory mozna ustawic w panelu webowym. MVP moze pozwalac takze na reczne uruchomienie skanow z panelu albo CLI.

Proponowane interwaly:

- ogolnopolski skan: 1-4 razy dziennie,
- Lodz alerty: co 10-30 minut,
- eksport Excel: po kazdym skanie albo na zadanie,
- pelne odswiezenie szczegolow: rzadziej niz listy wynikow,
- przeliczenie bazy cen: po kazdym skanie ogolnopolskim.

Tryb `lodz_alerts` powinien korzystac z mozliwie swiezej bazy ogolnopolskiej. Jesli baza cen dla danej grupy porownawczej jest starsza niz skonfigurowany prog, np. 24 godziny, oferta z Lodzi moze nadal trafic do alertow, ale powinna miec obnizona pewnosc porownania albo status `needs_review`.

System powinien pozwalac uruchomic z panelu i CLI:

- pojedynczy profil rozmiaru,
- wszystkie profile ogolnopolskie,
- tylko `lodz_alerts`,
- tylko eksport Excela,
- przeliczenie bazy cen,
- test regul opisowych.

W MVP harmonogram moze byc prosty i lokalny, np. proces aplikacji z schedulerem. Produkcyjne wdrozenie z monitoringiem, restartami i alertami infrastrukturalnymi pozostaje poza MVP.

## 20. Polityka pobierania szczegolow ofert

Nie kazda oferta musi byc pobierana ze szczegolami przy kazdym skanie, ale kazda nowa oferta, ktora ma byc uzyta do bazy cen albo scoringu porownawczego, powinna miec pobrane szczegoly co najmniej raz.

Zasady:

- Nowa oferta: pobierz szczegoly.
- Oferta uzywana do bazy cen: musi miec szczegoly i `comparable_key`.
- Oferta z Lodzi kwalifikujaca sie do alertu: pobierz szczegoly zawsze przed oznaczeniem alertu.
- Oferta z wysokim potencjalem z listy: pobierz szczegoly.
- Oferta znana i bez zmiany ceny: nie pobieraj szczegolow ponownie zbyt czesto.
- Oferta, ktora zmienila cene: pobierz szczegoly ponownie.
- Oferta stara/slaba/odrzucona: mozna pominac szczegoly przy kolejnych skanach.

Konfiguracja:

```yaml
details_fetch_policy:
  fetch_new_offers: true
  fetch_if_missing_comparable_key: true
  fetch_if_price_changed: true
  fetch_known_after_hours: 48
  fetch_lodz_candidates_always: true
  skip_rejected_known_offers: true
  max_detail_fetches_per_run: 200
```

System powinien miec limit pobierania szczegolow na jeden przebieg, aby nie robic zbyt agresywnego scrapingu. Jesli limit zostanie osiagniety, pozostale oferty trafiaja do kolejki na nastepny przebieg.

## 21. Rate limiting i stabilnosc

Scraper powinien dzialac ostroznie, z kontrolowanym tempem pobierania stron. PRD zaklada, ze projekt jest prowadzony w ramach uprawnionego researchu i zgodnie z uzyskanymi zgodami oraz zakresem tych zgod. MVP nie opisuje technik lamania zabezpieczen technicznych, omijania CAPTCHA ani obchodzenia niepublicznych blokad dostepu. Pozadane jest natomiast takie zaprojektowanie systemu, aby ograniczac ryzyko blokad przez legalne i technicznie bezpieczne mechanizmy: limity, opoznienia, backoff, kolejke i kontrolowane ponawianie pracy.

Mechanizmy MVP:

- opoznienia pomiedzy requestami,
- losowy jitter,
- osobne limity dla list wynikow i stron szczegolow,
- limit requestow na minute,
- limit requestow na jeden przebieg,
- backoff po bledach HTTP, timeoutach i parser errors,
- pauzowanie profilu po kilku bledach z rzedu,
- kolejka ofert do pobrania w kolejnym przebiegu,
- wykrywanie CAPTCHA/blokady,
- po wykryciu blokady system nie zatrzymuje calej aplikacji i nie traci kolejki; oznacza profil lub przebieg jako `temporarily_blocked`, czeka przez skonfigurowany cooldown i ponawia prace zgodnie z limitami,
- jesli blokada powtarza sie, system pomija dany profil w aktualnym przebiegu i przechodzi do pozostalych prac,
- zapisywanie bledow i powodow zatrzymania do logow oraz `search_runs`.

Przykladowe ustawienia:

```yaml
network:
  listing_min_delay_seconds: 3
  listing_max_delay_seconds: 8
  detail_min_delay_seconds: 5
  detail_max_delay_seconds: 12
  max_requests_per_minute: 10
  max_requests_per_run: 800
  max_detail_requests_per_run: 200
  max_errors_per_profile: 3
  backoff_after_error_seconds: 60
  backoff_after_block_seconds: 3600
  stop_whole_system_on_block: false
  pause_blocked_profile: true
  resume_after_block_backoff: true
  max_block_retries_per_run: 2
```

Jesli limit requestow, limit pobierania szczegolow lub blokada zostanie osiagnieta, system nie powinien tracic ofert. Powinien zapisac je jako oczekujace i kontynuowac w nastepnym przebiegu albo po uplywie cooldownu.

## 22. Statusy ofert

Oferta moze miec status systemowy oraz osobna decyzje uzytkownika.

Status systemowy opisuje wynik automatycznej analizy:

- `new` - nowo znaleziona, jeszcze bez pelnej analizy,
- `queued_details` - oferta czeka na pobranie szczegolow,
- `active` - aktywna oferta po pobraniu danych,
- `market_reference` - oferta uzyta do budowy ogolnopolskiej bazy cen,
- `candidate` - potencjalnie ciekawa oferta,
- `opportunity` - dobra okazja wedlug scoringu,
- `needs_review` - wymaga recznego sprawdzenia,
- `weak_match` - system nie jest pewny dopasowania modelu do bazy cen,
- `stale_reference` - baza porownawcza dla tej oferty jest za stara,
- `rejected` - odrzucona regulami lub scoringiem,
- `gone` - oferta zniknela z wynikow lub strona nie istnieje,
- `alerted` - oferta trafila do alertow Lodz.

Decyzja uzytkownika jest niezalezna od statusu systemowego:

- `none` - brak decyzji,
- `watch` - obserwowac,
- `contacted` - sprzedawca zostal skontaktowany,
- `purchased` - kupione,
- `ignored` - ignorowane,
- `bad_match` - bledne dopasowanie modelu lub danych,
- `not_profitable` - recznie uznane za nieoplacalne.

Dzieki temu system moze nadal aktualizowac status automatyczny, ale nie nadpisuje recznych decyzji uzytkownika.

## 23. Architektura techniczna

Proponowany stack:

- Python,
- FastAPI do prostego panelu webowego, API i akcji administracyjnych,
- `httpx` do pobierania stron,
- `selectolax` jako glowny parser HTML,
- `BeautifulSoup` pomocniczo, jesli konkretne fragmenty HTML beda wygodniejsze do parsowania,
- SQLite do lokalnej bazy MVP,
- `openpyxl` do generowania plikow Excel,
- `APScheduler` albo prosty scheduler aplikacyjny do cyklicznych skanow,
- `PyYAML` opcjonalnie do importu, eksportu i seedowania konfiguracji,
- opcjonalnie `Playwright`, jesli statyczne HTML nie wystarczy.

MVP nie powinno byc mikroserwisem. Panel webowy, scraper, scheduler, baza danych, scoring i eksport Excel moga dzialac w jednym repozytorium i jednej aplikacji, ale logika powinna byc podzielona na wyrazne moduly. Dzieki temu pozniej bedzie mozna latwo przeniesc projekt na VPS, dodac Dockera albo wymienic SQLite na PostgreSQL.

### 23.1. Proponowana struktura katalogow

```text
ScraperOfertTv/
  PRD.md
  README.md
  config/
    search_profiles.yml
    description_rules.yml
    scoring.yml
    app.yml
  data/
    offers.sqlite
  output/
    oferty_tv.xlsx
  logs/
    scraper.log
  src/
    scraper_ofert_tv/
      __init__.py
      cli.py
      config.py
      web.py
      olx_urls.py
      listing_scraper.py
      listing_parser.py
      detail_scraper.py
      detail_parser.py
      normalization.py
      rules.py
      scoring.py
      market.py
      comparison.py
      rate_limiter.py
      details_queue.py
      storage.py
      settings_service.py
      export_excel.py
      alerts.py
      scheduler.py
      migrations.py
      templates/
      static/
```

### 23.2. Moduly

- `config.py`: wczytywanie, walidacja, import i eksport konfiguracji.
- `web.py`: prosty panel ustawien i podstawowe akcje administracyjne.
- `olx_urls.py`: budowanie URL-i OLX z profili.
- `listing_scraper.py`: pobieranie stron wynikow.
- `listing_parser.py`: wyciaganie ofert z listy.
- `detail_scraper.py`: pobieranie stron szczegolow.
- `detail_parser.py`: wyciaganie danych szczegolowych.
- `normalization.py`: rozmiar, marka, cena, lokalizacja.
- `rules.py`: reguly opisowe.
- `scoring.py`: scoring i statusy.
- `market.py`: budowanie bazy cen i statystyk rynkowych.
- `comparison.py`: dopasowanie ofert do porownywalnych modeli.
- `rate_limiter.py`: opoznienia, jitter, backoff i limity.
- `details_queue.py`: kolejka ofert czekajacych na pobranie szczegolow.
- `storage.py`: SQLite.
- `settings_service.py`: odczyt i zapis ustawien z panelu.
- `export_excel.py`: generowanie pliku Excel.
- `alerts.py`: logika alertow Lodz.
- `scheduler.py`: cykliczne uruchamianie.
- `migrations.py`: proste migracje bazy SQLite.
- `cli.py`: komendy terminalowe.

## 24. CLI

CLI jest technicznym interfejsem do uruchamiania scrapera, testowania regul, eksportow i prac administracyjnych. Codzienna obsluga ustawien i alertow powinna odbywac sie przede wszystkim przez panel webowy.

Proponowane komendy:

```bash
python -m scraper_ofert_tv web --host 0.0.0.0 --port 8000
python -m scraper_ofert_tv scan --mode national
python -m scraper_ofert_tv scan --mode lodz_alerts
python -m scraper_ofert_tv scan --mode national --profile 40_49
python -m scraper_ofert_tv export excel
python -m scraper_ofert_tv recalc-market
python -m scraper_ofert_tv test-rules --text "Telewizor 55 cali, uszkodzona matryca"
python -m scraper_ofert_tv show-config
python -m scraper_ofert_tv backup-db
python -m scraper_ofert_tv migrate
```

Komendy powinny korzystac z tych samych ustawien co panel webowy. CLI nie powinno miec osobnej, rozjechanej konfiguracji.

## 25. Logowanie

System powinien logowac zdarzenia techniczne oraz decyzje analityczne. Logi techniczne pomagaja diagnozowac scraper, a dane audytowe w bazie pozwalaja zrozumiec, dlaczego dana oferta zostala oceniona jako okazja, kandydat, odrzucona albo wymagajaca sprawdzenia.

Log techniczny powinien zawierac:

- start i koniec skanu,
- tryb skanu: `national` albo `lodz_alerts`,
- profil wyszukiwania,
- URL wyszukiwania,
- numer strony wynikow,
- liczbe stron pobranych,
- liczbe ofert z listy,
- liczbe nowych ofert,
- liczbe ofert znanych,
- liczbe ofert dodanych do kolejki detali,
- liczbe pobranych szczegolow,
- liczbe pominietych szczegolow,
- liczbe okazji,
- bledy HTTP,
- timeouty,
- bledy parsowania,
- wykrycie blokady/CAPTCHA,
- uruchomienie backoff/cooldown,
- powody zakonczenia profilu lub calego przebiegu,
- czas trwania skanu.

Dane audytowe w bazie powinny zawierac:

- dopasowany `comparable_key`,
- uzyta cene referencyjna,
- liczbe ofert porownawczych,
- poziom pewnosci porownania,
- dopasowane reguly opisowe,
- powody odrzucenia,
- wyliczony score,
- wyliczony potencjalny profit,
- powod trafienia do `Lodz alerty`,
- historie zmian ceny,
- historie statusow.

Logi powinny byc zapisywane do pliku, np. `logs/scraper.log`, a najwazniejsze informacje o przebiegach powinny byc zapisywane rowniez w tabelach `search_runs`, `search_profile_runs`, `rule_matches`, `alert_events` i `export_runs`.

## 26. Kryteria akceptacji MVP

MVP jest gotowe, gdy:

- system ma prosty panel webowy do edycji ustawien, profili rozmiarow, regul opisowych i progow scoringu,
- profile wyszukiwania roznia sie tylko zakresem rozmiaru TV,
- globalne filtry OLX sa stosowane wspolnie dla wszystkich profili: cena 300-700 PLN, oferty prywatne, stan uzywane,
- scraper pobiera oferty OLX dla calej Polski w trybie `national`,
- scraper pobiera oferty OLX dla Lodzi i okolic w trybie `lodz_alerts`,
- scraper przechodzi po kolejnych stronach wynikow do ustawionego limitu albo warunku stopu,
- scraper zbiera linki do ofert i deduplikuje je po OLX ID oraz canonical URL,
- scraper pobiera szczegoly nowych ofert albo dodaje je do kolejki detali, jesli limit przebiegu zostal osiagniety,
- dane sa zapisywane w SQLite jako glownym zrodle prawdy,
- skan ogolnopolski buduje baze cen podobnych ofert,
- system tworzy `comparable_key` dla ofert z wystarczajaca liczba danych,
- tryb `lodz_alerts` porownuje lokalne oferty z baza ogolnopolska,
- scoring porownawczy uwzglednia cene referencyjna, rabat wzgledem rynku, liczbe ofert porownawczych, pewnosc dopasowania i reguly opisowe,
- reguly opisowe wykrywaja podstawowe czerwone flagi, np. uszkodzona matryca, brak obrazu, brak pilota, brak podstawy,
- system rozroznia status systemowy i decyzje uzytkownika,
- eksport Excel zawiera arkusze `Oferty`, `Lodz alerty`, `Baza cen`, `Historia skanow`,
- arkusz `Lodz alerty` pokazuje lokalne okazje nadajace sie do recznej weryfikacji,
- Excel ma czytelne kolumny, filtry i klikalne linki,
- reczne decyzje uzytkownika sa zapisywane w bazie/panelu, a nie tylko w Excelu,
- system nie traci ofert po osiagnieciu limitow, bledach albo czasowej blokadzie profilu,
- bledy, powody stopu, alerty i najwazniejsze decyzje scoringu sa logowane,
- scraper mozna uruchomic z panelu oraz z CLI,
- projekt da sie uruchomic lokalnie i przygotowac do przeniesienia na serwer/VPS.

## 27. Etapy realizacji

### Etap 1: Fundament projektu

- Utworzenie struktury projektu.
- Konfiguracja zaleznosci.
- SQLite i proste migracje.
- Podstawowy model danych: oferty, snapshoty, przebiegi skanow, ustawienia.
- CLI: `web`, `scan`, `export`, `migrate`.
- Minimalny panel webowy z ekranem ustawien globalnych.

### Etap 2: Scraper list wynikow OLX

- Budowanie URL-i OLX.
- Profile rozmiarow TV.
- Globalne filtry: cena 300-700 PLN, prywatne, uzywane.
- Tryb `national`.
- Pobieranie HTML list wynikow.
- Parser list wynikow.
- Paginacja.
- Dedupikacja po OLX ID i canonical URL.
- Logowanie przebiegow.

### Etap 3: Szczegoly ofert i normalizacja

- Kolejka pobierania szczegolow.
- Pobieranie stron ofert.
- Parser szczegolow.
- Normalizacja ceny, lokalizacji, rozmiaru, marki, modelu i technologii.
- Zapis historii cen i snapshotow.
- Oznaczanie ofert zniknietych.
- Rate limiting, backoff i cooldown profili.

### Etap 4: Baza cen ogolnopolskich

- Tworzenie `comparable_key`.
- Grupowanie podobnych modeli TV.
- Liczenie mediany, sredniej, minimum, kwartylow i liczby ofert.
- Wykluczanie ofert uszkodzonych z normalnej bazy referencyjnej.
- Poziom pewnosci porownania.
- Komenda `recalc-market`.

### Etap 5: Reguly opisowe i scoring

- Panel edycji regul opisowych.
- Silnik regul.
- Testowanie regul na przykladowym opisie.
- Panel ustawien progow scoringu.
- Scoring porownawczy.
- Statusy systemowe ofert.
- Osobna decyzja uzytkownika.

### Etap 6: Excel

- Eksport `oferty_tv_latest.xlsx`.
- Arkusze `Oferty`, `Lodz alerty`, `Baza cen`, `Historia skanow`.
- Czytelne kolumny.
- Linki do OLX.
- Sortowanie, filtry i podstawowe formatowanie.
- Opcjonalne archiwalne kopie eksportow.

### Etap 7: Lodz alerty MVP

- Osobny tryb `lodz_alerts`.
- Lokalizacja Lodz i promien.
- Porownanie ofert lokalnych z baza ogolnopolska.
- Progi alertow.
- Zapis `alert_events`.
- Widok alertow w panelu.
- Arkusz `Lodz alerty`.
- Zewnetrzne powiadomienia push pozostaja poza MVP.

### Etap 8: Uruchomienie na serwerze

- Przygotowanie konfiguracji pod VPS.
- Instrukcja uruchomienia.
- Backup SQLite.
- Harmonogram skanow.
- Podstawowa kontrola logow.

### Etap 9: Ulepszenia po MVP

- Lepsza wycena rynkowa.
- AI do klasyfikacji niejednoznacznych opisow.
- Analiza zdjec.
- Zewnetrzne powiadomienia: email, Telegram, Discord albo SMS.
- PostgreSQL.
- Docker.
- Bardziej rozbudowany dashboard.

## 28. Ryzyka

### 28.1. Ryzyka techniczne

- OLX moze zmienic strukture HTML.
  - Skutek: parser przestaje wyciagac ceny, linki albo parametry.
  - Ograniczenie: testy parserow na zapisanych przykladach HTML, parser warnings, logowanie brakujacych pol.

- OLX moze ograniczyc dostep po zbyt wielu requestach.
  - Skutek: czesc profili nie zostanie przeskanowana w danym przebiegu.
  - Ograniczenie: opoznienia, jitter, limity, backoff, cooldown profilu i kolejka na kolejne przebiegi.

- Strony szczegolow moga wymagac renderowania JS.
  - Skutek: `httpx` moze nie wystarczyc do pobrania wszystkich danych.
  - Ograniczenie: najpierw statyczny HTML, pozniej opcjonalny fallback przez Playwright tylko dla potrzebnych przypadkow.

- Paginacja OLX moze zachowywac sie inaczej dla roznych filtrow.
  - Skutek: scraper moze pominac strony albo wejsc w powtorzona strone.
  - Ograniczenie: preferowanie linku `Dalej`, wykrywanie powtorzonych URL-i i powtorzonych zestawow ofert.

### 28.2. Ryzyka danych

- Wyniki wyszukiwania moga byc niepelne przy zbyt szerokich zapytaniach.
  - Skutek: baza cen moze nie reprezentowac calego rynku.
  - Ograniczenie: profile rozmiarow, limity stron, cykliczne skany i historia ofert.

- Opisy ofert moga byc niejednoznaczne.
  - Skutek: system moze nie wykryc wady albo blednie odrzucic dobra oferte.
  - Ograniczenie: reguly opisowe, status `needs_review`, pelny opis w Excelu.

- Cena atrakcyjna moze wynikac z ukrytej wady.
  - Skutek: falszywy alert.
  - Ograniczenie: czerwone flagi, wymog recznej weryfikacji, zachowanie opisu i parametrow.

- Dopasowanie modelu TV moze byc niedokladne.
  - Skutek: zly `comparable_key` i bledny scoring.
  - Ograniczenie: `comparison_confidence`, minimalna liczba ofert porownawczych, status `weak_match`.

- Baza cen moze byc za mala dla rzadkich modeli.
  - Skutek: brak wiarygodnej ceny referencyjnej.
  - Ograniczenie: minimalny prog ofert porownawczych i `needs_review` zamiast `opportunity`.

### 28.3. Ryzyka biznesowe

- Cena w OLX nie musi byc cena transakcyjna.
  - Skutek: marza moze byc zawyzona albo zanizona.
  - Ograniczenie: safety factor przy cenie odsprzedazy i reczna walidacja.

- Lokalizacja w ofercie moze nie wystarczyc do dokladnego kosztu transportu.
  - Skutek: bledne oszacowanie profitu.
  - Ograniczenie: konserwatywne koszty, reczna decyzja uzytkownika.

- Okazje moga znikac bardzo szybko.
  - Skutek: Excel moze byc opozniony wzgledem rynku.
  - Ograniczenie: czestszy tryb `lodz_alerts`, panel alertow, pozniej zewnetrzne powiadomienia.

### 28.4. Ryzyka prawno-operacyjne

- Zakres zgody/researchu moze miec ograniczenia.
  - Skutek: niektore sposoby pobierania danych moga byc niedozwolone poza ustalonym zakresem.
  - Ograniczenie: trzymanie sie publicznych stron, brak logowania, brak danych kontaktowych, brak obchodzenia prywatnych obszarow.

- Dane moga zawierac informacje niepotrzebne do celu.
  - Skutek: niepotrzebne ryzyko przechowywania danych.
  - Ograniczenie: nie pobierac telefonow, emaili i prywatnych danych kontaktowych; zapisywac tylko dane potrzebne do oceny ofert.

## 29. Otwarte pytania

Na tym etapie glowne decyzje MVP sa juz ustalone. Ponizsze kwestie moga zostac doprecyzowane przed implementacja albo ustawione jako edytowalne parametry w panelu.

### 29.1. Pytania do decyzji przed implementacja

- Ktore zakresy rozmiarow OLX wlaczyc domyslnie na start: wszystkie, czy tylko najbardziej flipowalne?
- Jakie domyslne koszty przyjac do liczenia profitu: transport, ewentualne czyszczenie, drobne akcesoria, margines bezpieczenstwa?
- Czy `Lodz alerty` maja pokazywac tylko oferty z wysokim confidence, czy rowniez `needs_review` z duzym potencjalnym rabatem?
- Jak dlugo oferta ma pozostawac aktywna, jesli przestala pojawiac sie w wynikach OLX, ale jej strona szczegolow jeszcze dziala?

### 29.2. Decyzje doprecyzowane

- Oferty z istotnymi uszkodzeniami, np. uszkodzona matryca, brak obrazu albo nie wlacza sie, maja byc oznaczane jako `rejected` i nie powinny trafiac do normalnych okazji flipowych.
- Oferty odrzucone moga zostac zapisane w bazie i historii, aby system mial pelniejszy obraz rynku oraz mozliwosc audytu decyzji.

### 29.3. Parametry edytowalne w panelu

- Zakres ceny: domyslnie 300-700 PLN.
- Sprzedawca: domyslnie prywatny.
- Stan: domyslnie uzywane.
- Promien Lodzi: domyslnie 50 km.
- Minimalny profit alertu: domyslnie 150 PLN.
- Minimalny rabat wzgledem rynku: domyslnie 30%.
- Minimalna liczba ofert porownawczych: domyslnie 3.
- Minimalna pewnosc porownania: domyslnie `medium`.
- Limit stron dla trybu `national`.
- Limit stron dla trybu `lodz_alerts`.
- Limit pobierania szczegolow na przebieg.
- Interwaly harmonogramu.
- Reguly opisowe i ich wagi.

## 30. Decyzje projektowe na start

Decyzje dla pierwszej implementacji MVP:

- Zrodlo danych: OLX, bez oficjalnego API.
- Pobieranie danych: publiczne strony ofert i wynikow wyszukiwania.
- Brak logowania do OLX w MVP.
- Brak pobierania telefonow, emaili i prywatnych danych kontaktowych.
- Zakres geograficzny `national`: cala Polska.
- Zakres geograficzny `lodz_alerts`: Lodz i okolice, domyslnie 50 km.
- Profile wyszukiwania roznia sie tylko zakresem rozmiaru TV.
- Globalne filtry dla wszystkich profili: cena 300-700 PLN, oferty prywatne, stan uzywane.
- Kategorie rozmiarow korzystaja z natywnych filtrow OLX.
- Dane szczegolowe pobierane sa co najmniej raz dla kazdej nowej oferty uzywanej do bazy cen albo scoringu.
- Pobieranie szczegolow ma limit na przebieg i kolejke na kolejne przebiegi.
- Oferty z istotnymi uszkodzeniami trafiaja do `rejected`.
- Ogolnopolski skan buduje baze cen podobnych modeli TV.
- Scoring dla Lodzi opiera sie na porownaniu lokalnej ceny z ogolnopolska cena referencyjna podobnego modelu.
- Slabe dopasowania modeli dostaja `weak_match` albo `needs_review`, a nie automatycznie `opportunity`.
- `Lodz alerty` sa czescia MVP.
- W MVP alerty sa widoczne w Excelu i panelu; zewnetrzne powiadomienia push sa poza MVP.
- Excel jest raportem generowanym z bazy, a nie miejscem trwalej konfiguracji.
- Reczne decyzje uzytkownika sa zapisywane w bazie/panelu.
- Ustawienia, reguly opisowe i progi scoringu sa edytowane w prostym panelu webowym.
- YAML sluzy tylko jako techniczny seed, eksport, backup albo fallback.
- Baza MVP: SQLite.
- Architektura MVP: jedna aplikacja Python, bez mikroserwisow.
- Stack startowy: FastAPI, httpx, selectolax, SQLite, openpyxl.
- Projekt ma byc gotowy do uruchomienia lokalnie i pozniejszego przeniesienia na serwer/VPS.
