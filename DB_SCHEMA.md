# DB Schema - Scraper Ofert TV

Ten dokument opisuje proponowany schemat SQLite dla MVP. SQLite jest zrodlem prawdy, a Excel jest raportem generowanym z bazy.

Typy sa opisane pod SQLite:

- `INTEGER` dla liczb calkowitych, timestampow i boolean 0/1.
- `REAL` dla wartosci procentowych i scoringu.
- `TEXT` dla stringow, dat ISO i JSON.
- `created_at`, `updated_at`, `started_at`, `finished_at` jako tekst ISO 8601 UTC/local konsekwentnie wedlug implementacji.

## 1. Konwencje

- Cena: `price_pln INTEGER`, bez pola waluty.
- URL oferty: `url TEXT`, `canonical_url TEXT`.
- OLX ID: `olx_offer_id TEXT`.
- JSON w SQLite: pola z sufiksem `_json`.
- Boolean: `0` albo `1`.
- Decyzje uzytkownika nie nadpisuja statusu systemowego.
- Deduplikacja: OLX ID, canonical URL, a awaryjnie hash.

## 2. `schema_migrations`

Historia wykonanych migracji.

```sql
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);
```

## 3. `settings`

Ustawienia aplikacji edytowane z panelu.

```sql
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  description TEXT,
  updated_at TEXT NOT NULL
);
```

Przykladowe klucze:

- `global_filters`
- `national_scan`
- `lodz_alerts`
- `rate_limit`
- `details_fetch_policy`
- `scheduler`
- `excel_export`

## 4. `size_profiles`

Profile wyszukiwania roznia sie tylko rozmiarem TV.

```sql
CREATE TABLE size_profiles (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  olx_size_value TEXT NOT NULL,
  min_inches INTEGER,
  max_inches INTEGER,
  enabled INTEGER NOT NULL DEFAULT 1,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Przykladowe `id`: `under_30`, `30_39`, `40_49`, `50_59`, `60_69`, `70_79`, `over_80`.

## 5. `description_rules`

Reguly opisowe edytowane w panelu.

```sql
CREATE TABLE description_rules (
  id TEXT PRIMARY KEY,
  enabled INTEGER NOT NULL DEFAULT 1,
  category TEXT NOT NULL,
  severity TEXT NOT NULL,
  label TEXT NOT NULL,
  applies_to TEXT NOT NULL,
  match_mode TEXT NOT NULL,
  patterns_json TEXT NOT NULL,
  score_delta REAL NOT NULL DEFAULT 0,
  action TEXT NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Kategorie: `red_flag`, `warning`, `positive`, `exclude`, `info`.

Akcje: `flag`, `reject`, `boost`, `info`.

## 6. `scoring_settings`

Progi scoringu i alertow.

```sql
CREATE TABLE scoring_settings (
  id TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Przykladowe `id`:

- `default`
- `lodz_alerts`
- `market_reference`

## 7. `search_runs`

Jeden przebieg skanu.

```sql
CREATE TABLE search_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  profiles_total INTEGER NOT NULL DEFAULT 0,
  profiles_done INTEGER NOT NULL DEFAULT 0,
  listing_pages_fetched INTEGER NOT NULL DEFAULT 0,
  offers_seen INTEGER NOT NULL DEFAULT 0,
  offers_new INTEGER NOT NULL DEFAULT 0,
  offers_known INTEGER NOT NULL DEFAULT 0,
  details_queued INTEGER NOT NULL DEFAULT 0,
  details_fetched INTEGER NOT NULL DEFAULT 0,
  details_skipped INTEGER NOT NULL DEFAULT 0,
  alerts_created INTEGER NOT NULL DEFAULT 0,
  error_count INTEGER NOT NULL DEFAULT 0,
  stop_reason TEXT,
  config_snapshot_json TEXT,
  notes TEXT
);
```

`mode`: `national`, `lodz_alerts`, `manual_export`, `recalc_market`.

## 8. `search_profile_runs`

Przebieg pojedynczego profilu rozmiaru w ramach skanu.

```sql
CREATE TABLE search_profile_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  search_run_id INTEGER NOT NULL,
  size_profile_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  search_url TEXT NOT NULL,
  page_limit INTEGER,
  pages_fetched INTEGER NOT NULL DEFAULT 0,
  offers_seen INTEGER NOT NULL DEFAULT 0,
  offers_new INTEGER NOT NULL DEFAULT 0,
  offers_known INTEGER NOT NULL DEFAULT 0,
  details_queued INTEGER NOT NULL DEFAULT 0,
  error_count INTEGER NOT NULL DEFAULT 0,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  stop_reason TEXT,
  parser_warnings_json TEXT,
  FOREIGN KEY (search_run_id) REFERENCES search_runs(id),
  FOREIGN KEY (size_profile_id) REFERENCES size_profiles(id)
);
```

Mozliwe statusy: `running`, `success`, `partial`, `failed`, `temporarily_blocked`, `skipped`.

## 9. `offers`

Aktualny stan oferty.

```sql
CREATE TABLE offers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL DEFAULT 'olx',
  olx_offer_id TEXT,
  url TEXT NOT NULL,
  canonical_url TEXT,
  url_hash TEXT NOT NULL,
  title TEXT,
  raw_title TEXT,
  price_pln INTEGER,
  raw_price TEXT,
  negotiable INTEGER,
  is_free INTEGER NOT NULL DEFAULT 0,
  seller_type TEXT,
  seller_name TEXT,
  seller_profile_url TEXT,
  condition_value TEXT,
  city TEXT,
  district TEXT,
  region TEXT,
  raw_location TEXT,
  distance_from_lodz_km REAL,
  olx_size_bucket TEXT,
  detected_size_inches INTEGER,
  brand TEXT,
  model TEXT,
  technology TEXT,
  resolution TEXT,
  comparable_key TEXT,
  comparison_confidence TEXT,
  system_status TEXT NOT NULL DEFAULT 'new',
  user_decision TEXT NOT NULL DEFAULT 'none',
  user_note TEXT,
  contacted_at TEXT,
  purchased_at TEXT,
  ignored_until TEXT,
  manual_priority INTEGER,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  last_detail_fetch_at TEXT,
  gone_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Indeksy:

```sql
CREATE UNIQUE INDEX idx_offers_olx_offer_id
ON offers(olx_offer_id)
WHERE olx_offer_id IS NOT NULL;

CREATE UNIQUE INDEX idx_offers_canonical_url
ON offers(canonical_url)
WHERE canonical_url IS NOT NULL;

CREATE UNIQUE INDEX idx_offers_url_hash
ON offers(url_hash);

CREATE INDEX idx_offers_status ON offers(system_status);
CREATE INDEX idx_offers_user_decision ON offers(user_decision);
CREATE INDEX idx_offers_comparable_key ON offers(comparable_key);
CREATE INDEX idx_offers_location ON offers(city, region);
CREATE INDEX idx_offers_last_seen ON offers(last_seen_at);
```

Statusy systemowe:

- `new`
- `queued_details`
- `active`
- `market_reference`
- `candidate`
- `opportunity`
- `needs_review`
- `weak_match`
- `stale_reference`
- `rejected`
- `gone`
- `alerted`

Decyzje uzytkownika:

- `none`
- `watch`
- `contacted`
- `purchased`
- `ignored`
- `bad_match`
- `not_profitable`

## 10. `offer_snapshots`

Historia danych z kolejnych skanow.

```sql
CREATE TABLE offer_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  search_run_id INTEGER,
  search_profile_run_id INTEGER,
  scan_mode TEXT NOT NULL,
  size_profile_id TEXT,
  listing_page_url TEXT,
  listing_page_number INTEGER,
  listing_position INTEGER,
  title TEXT,
  price_pln INTEGER,
  raw_price TEXT,
  negotiable INTEGER,
  city TEXT,
  district TEXT,
  region TEXT,
  raw_location TEXT,
  description TEXT,
  params_json TEXT,
  photo_count INTEGER,
  main_photo_url TEXT,
  listing_thumbnail_url TEXT,
  parser_warnings_json TEXT,
  scraped_at TEXT NOT NULL,
  FOREIGN KEY (offer_id) REFERENCES offers(id),
  FOREIGN KEY (search_run_id) REFERENCES search_runs(id),
  FOREIGN KEY (search_profile_run_id) REFERENCES search_profile_runs(id),
  FOREIGN KEY (size_profile_id) REFERENCES size_profiles(id)
);
```

Indeksy:

```sql
CREATE INDEX idx_offer_snapshots_offer ON offer_snapshots(offer_id);
CREATE INDEX idx_offer_snapshots_scraped ON offer_snapshots(scraped_at);
CREATE INDEX idx_offer_snapshots_run ON offer_snapshots(search_run_id);
```

## 11. `offer_price_history`

Historia zmian ceny.

```sql
CREATE TABLE offer_price_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  price_pln INTEGER,
  raw_price TEXT,
  detected_at TEXT NOT NULL,
  source_snapshot_id INTEGER,
  FOREIGN KEY (offer_id) REFERENCES offers(id),
  FOREIGN KEY (source_snapshot_id) REFERENCES offer_snapshots(id)
);
```

Indeksy:

```sql
CREATE INDEX idx_price_history_offer ON offer_price_history(offer_id);
CREATE INDEX idx_price_history_detected ON offer_price_history(detected_at);
```

## 12. `details_queue`

Kolejka pobierania szczegolow.

```sql
CREATE TABLE details_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  reason TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 100,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  last_error TEXT,
  available_after TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  finished_at TEXT,
  FOREIGN KEY (offer_id) REFERENCES offers(id)
);
```

Statusy: `pending`, `processing`, `done`, `failed`, `skipped`.

Indeksy:

```sql
CREATE INDEX idx_details_queue_status_priority
ON details_queue(status, priority, available_after);

CREATE INDEX idx_details_queue_offer
ON details_queue(offer_id);
```

## 13. `comparable_groups`

Grupy podobnych modeli TV.

```sql
CREATE TABLE comparable_groups (
  comparable_key TEXT PRIMARY KEY,
  brand TEXT,
  model TEXT,
  detected_size_inches INTEGER,
  olx_size_bucket TEXT,
  technology TEXT,
  resolution TEXT,
  normalized_condition TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## 14. `market_price_references`

Referencyjne ceny rynkowe dla grup.

```sql
CREATE TABLE market_price_references (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  comparable_key TEXT NOT NULL,
  reference_price_pln INTEGER,
  min_price_pln INTEGER,
  median_price_pln INTEGER,
  avg_price_pln REAL,
  p25_price_pln INTEGER,
  p75_price_pln INTEGER,
  offers_count INTEGER NOT NULL,
  sample_offer_ids_json TEXT,
  excluded_offer_ids_json TEXT,
  confidence TEXT NOT NULL,
  calculated_at TEXT NOT NULL,
  valid_until TEXT,
  FOREIGN KEY (comparable_key) REFERENCES comparable_groups(comparable_key)
);
```

Indeksy:

```sql
CREATE INDEX idx_market_refs_key_time
ON market_price_references(comparable_key, calculated_at);
```

## 15. `rule_matches`

Wyniki regul opisowych dla ofert.

```sql
CREATE TABLE rule_matches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  rule_id TEXT NOT NULL,
  snapshot_id INTEGER,
  category TEXT NOT NULL,
  severity TEXT NOT NULL,
  action TEXT NOT NULL,
  score_delta REAL NOT NULL DEFAULT 0,
  matched_text TEXT,
  matched_field TEXT,
  matched_at TEXT NOT NULL,
  FOREIGN KEY (offer_id) REFERENCES offers(id),
  FOREIGN KEY (rule_id) REFERENCES description_rules(id),
  FOREIGN KEY (snapshot_id) REFERENCES offer_snapshots(id)
);
```

Indeksy:

```sql
CREATE INDEX idx_rule_matches_offer ON rule_matches(offer_id);
CREATE INDEX idx_rule_matches_rule ON rule_matches(rule_id);
```

## 16. `offer_scores`

Historia scoringu oferty.

```sql
CREATE TABLE offer_scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  market_reference_id INTEGER,
  score REAL,
  system_status TEXT NOT NULL,
  reference_price_pln INTEGER,
  expected_resale_price_pln INTEGER,
  estimated_costs_pln INTEGER,
  estimated_profit_pln INTEGER,
  market_discount_percent REAL,
  comparable_offers_count INTEGER,
  comparison_confidence TEXT,
  scoring_reasons_json TEXT,
  calculated_at TEXT NOT NULL,
  FOREIGN KEY (offer_id) REFERENCES offers(id),
  FOREIGN KEY (market_reference_id) REFERENCES market_price_references(id)
);
```

Indeksy:

```sql
CREATE INDEX idx_offer_scores_offer ON offer_scores(offer_id);
CREATE INDEX idx_offer_scores_status ON offer_scores(system_status);
CREATE INDEX idx_offer_scores_calculated ON offer_scores(calculated_at);
```

## 17. `user_offer_notes`

Decyzje i notatki uzytkownika.

```sql
CREATE TABLE user_offer_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  decision TEXT NOT NULL,
  note TEXT,
  contacted_at TEXT,
  purchased_at TEXT,
  ignored_until TEXT,
  manual_priority INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (offer_id) REFERENCES offers(id)
);
```

Indeksy:

```sql
CREATE INDEX idx_user_notes_offer ON user_offer_notes(offer_id);
CREATE INDEX idx_user_notes_decision ON user_offer_notes(decision);
```

## 18. `alert_events`

Alerty Lodz i historia powodow alertu.

```sql
CREATE TABLE alert_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  search_run_id INTEGER,
  alert_type TEXT NOT NULL,
  status TEXT NOT NULL,
  score REAL,
  reference_price_pln INTEGER,
  offer_price_pln INTEGER,
  estimated_profit_pln INTEGER,
  market_discount_percent REAL,
  comparison_confidence TEXT,
  comparable_offers_count INTEGER,
  reason_json TEXT,
  first_created_at TEXT NOT NULL,
  last_triggered_at TEXT NOT NULL,
  suppressed_until TEXT,
  FOREIGN KEY (offer_id) REFERENCES offers(id),
  FOREIGN KEY (search_run_id) REFERENCES search_runs(id)
);
```

Statusy: `new`, `repeated`, `suppressed`, `resolved`, `ignored`.

Indeksy:

```sql
CREATE INDEX idx_alert_events_offer ON alert_events(offer_id);
CREATE INDEX idx_alert_events_status ON alert_events(status);
CREATE INDEX idx_alert_events_triggered ON alert_events(last_triggered_at);
```

## 19. `export_runs`

Historia eksportow Excel.

```sql
CREATE TABLE export_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  export_type TEXT NOT NULL,
  status TEXT NOT NULL,
  output_path TEXT NOT NULL,
  archived_path TEXT,
  rows_offers INTEGER NOT NULL DEFAULT 0,
  rows_lodz_alerts INTEGER NOT NULL DEFAULT 0,
  rows_market INTEGER NOT NULL DEFAULT 0,
  rows_scan_history INTEGER NOT NULL DEFAULT 0,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  error_message TEXT
);
```

## 20. Widoki pomocnicze

Implementacja moze dodac widoki SQL, jesli uproszcza eksport i panel.

Rekomendowane widoki:

- `v_latest_offer_scores` - ostatni scoring dla kazdej oferty.
- `v_lodz_alert_candidates` - aktualne alerty Lodz do Excela.
- `v_market_latest` - najnowsza referencja cenowa dla `comparable_key`.

Widoki nie sa wymagane w pierwszej migracji, ale sa dozwolone.

## 21. Minimalny seed MVP

Po migracji baza powinna zawierac:

- global filters: cena 300-700 PLN, prywatne, uzywane,
- size profiles OLX,
- rate limit defaults,
- details fetch policy,
- scoring defaults,
- Lodz alert defaults,
- podstawowe reguly opisowe.

## 22. Uwagi migracyjne

- Nie usuwaj danych uzytkownika w migracjach.
- Migracje musza byc idempotentne albo oznaczane w `schema_migrations`.
- Zmiany schematu wymagaja aktualizacji DB_SCHEMA.md.
- Jesli implementacja wymaga uproszczenia schematu, zapytaj architekta przed zmiana.
