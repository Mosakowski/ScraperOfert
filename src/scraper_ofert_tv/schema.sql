CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  description TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS size_profiles (
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

CREATE TABLE IF NOT EXISTS description_rules (
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

CREATE TABLE IF NOT EXISTS scoring_settings (
  id TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_runs (
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

CREATE TABLE IF NOT EXISTS search_profile_runs (
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

CREATE TABLE IF NOT EXISTS offers (
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_offers_olx_offer_id
ON offers(olx_offer_id)
WHERE olx_offer_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_offers_canonical_url
ON offers(canonical_url)
WHERE canonical_url IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_offers_url_hash
ON offers(url_hash);

CREATE INDEX IF NOT EXISTS idx_offers_status ON offers(system_status);
CREATE INDEX IF NOT EXISTS idx_offers_user_decision ON offers(user_decision);
CREATE INDEX IF NOT EXISTS idx_offers_comparable_key ON offers(comparable_key);
CREATE INDEX IF NOT EXISTS idx_offers_location ON offers(city, region);
CREATE INDEX IF NOT EXISTS idx_offers_last_seen ON offers(last_seen_at);

CREATE TABLE IF NOT EXISTS offer_snapshots (
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

CREATE INDEX IF NOT EXISTS idx_offer_snapshots_offer ON offer_snapshots(offer_id);
CREATE INDEX IF NOT EXISTS idx_offer_snapshots_scraped ON offer_snapshots(scraped_at);
CREATE INDEX IF NOT EXISTS idx_offer_snapshots_run ON offer_snapshots(search_run_id);

CREATE TABLE IF NOT EXISTS offer_price_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  price_pln INTEGER,
  raw_price TEXT,
  detected_at TEXT NOT NULL,
  source_snapshot_id INTEGER,
  FOREIGN KEY (offer_id) REFERENCES offers(id),
  FOREIGN KEY (source_snapshot_id) REFERENCES offer_snapshots(id)
);

CREATE INDEX IF NOT EXISTS idx_price_history_offer ON offer_price_history(offer_id);
CREATE INDEX IF NOT EXISTS idx_price_history_detected ON offer_price_history(detected_at);

CREATE TABLE IF NOT EXISTS details_queue (
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

CREATE INDEX IF NOT EXISTS idx_details_queue_status_priority
ON details_queue(status, priority, available_after);

CREATE INDEX IF NOT EXISTS idx_details_queue_offer
ON details_queue(offer_id);

CREATE TABLE IF NOT EXISTS comparable_groups (
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

CREATE TABLE IF NOT EXISTS market_price_references (
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

CREATE INDEX IF NOT EXISTS idx_market_refs_key_time
ON market_price_references(comparable_key, calculated_at);

CREATE TABLE IF NOT EXISTS rule_matches (
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

CREATE INDEX IF NOT EXISTS idx_rule_matches_offer ON rule_matches(offer_id);
CREATE INDEX IF NOT EXISTS idx_rule_matches_rule ON rule_matches(rule_id);

CREATE TABLE IF NOT EXISTS offer_scores (
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

CREATE INDEX IF NOT EXISTS idx_offer_scores_offer ON offer_scores(offer_id);
CREATE INDEX IF NOT EXISTS idx_offer_scores_status ON offer_scores(system_status);
CREATE INDEX IF NOT EXISTS idx_offer_scores_calculated ON offer_scores(calculated_at);

CREATE TABLE IF NOT EXISTS user_offer_notes (
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

CREATE INDEX IF NOT EXISTS idx_user_notes_offer ON user_offer_notes(offer_id);
CREATE INDEX IF NOT EXISTS idx_user_notes_decision ON user_offer_notes(decision);

CREATE TABLE IF NOT EXISTS alert_events (
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

CREATE INDEX IF NOT EXISTS idx_alert_events_offer ON alert_events(offer_id);
CREATE INDEX IF NOT EXISTS idx_alert_events_status ON alert_events(status);
CREATE INDEX IF NOT EXISTS idx_alert_events_triggered ON alert_events(last_triggered_at);

CREATE TABLE IF NOT EXISTS export_runs (
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
