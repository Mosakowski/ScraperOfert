# Plan stabilnego pobierania ofert

## 1. Rozpoznawanie odpowiedzi

- Najpierw interpretować HTTP 404/410 jako niedostępne ogłoszenie, 403/429 jako ograniczenie dostępu.
- CAPTCHA rozpoznawać po widocznym wyzwaniu, nie po słowie `captcha` w skryptach strony.
- Zachować diagnostykę statusu i powodu; po potwierdzonej blokadzie przerwać bieżący worker.

## 2. Trafność kolejki

- Nie kolejkować wyników rozszerzonego wyszukiwania OLX (`extended_search`).
- Dla gotowych kategorii elektroniki TV i laptopy odrzucić oferty z innych działów OLX (CID różny od 99); pozostałe kategorie zachować bez tego ograniczenia.
- Zadania ze świeżych skanów i bez wcześniejszych prób pobierać przed starymi ponowieniami. Istniejące niepasujące zadania pomijać przy pobieraniu kolejki.

## 3. Budżet ruchu

- Domyślnie ograniczyć do 5 stron na profil i 40 stron w całym skanie, nawet gdy stare ustawienia dopuszczają więcej.
- Scheduler ma pobierać do 20 detali w cyklu profilu i rozkładać starty profili w czasie.
- Limiter ma egzekwować limit żądań na minutę; przy blokadzie odłożyć zadanie na kilka godzin.

## Weryfikacja

- Testy klasyfikacji 410 i prawdziwego wyzwania, doboru zadań oraz budżetu skanu.
- Krótki przebieg na zapisanych danych; ruch do OLX dopiero po sprawdzeniu zmian.

## Stan wykonania

- Zaimplementowano klasyfikację HTTP przed kontrolą widocznego wyzwania CAPTCHA.
- Parser list akceptuje tylko linki ofert OLX. Kolejka dla TV/laptopów odrzuca rozszerzone wyniki, obce działy i ogłoszenia bez sygnału danej kategorii w adresie. To jest heurystyka: oferta z samym numerem modelu może wymagać ręcznego dodania do kolejki.
- Budżet skanu, liczba detali na cykl i rozłożenie profili są dostępne w ustawieniu `traffic_policy`, z wartościami domyślnymi 5/40/20/10 minut. Limiter egzekwuje żądania na minutę, a zadanie zatrzymane przez blokadę czeka 6 godzin.
- Po wdrożeniu wykonano kopie bazy i oczyszczono oczekującą kolejkę. Krótki pobór detali potwierdził kontynuowanie pracy po wcześniejszym fałszywym alarmie.
