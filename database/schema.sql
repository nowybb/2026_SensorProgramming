PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS cabinet (
  cabinet_id INTEGER PRIMARY KEY, name TEXT NOT NULL,
  mode TEXT NOT NULL CHECK(mode IN ('HOME','PUBLIC'))
);
CREATE TABLE IF NOT EXISTS compartment (
  compartment_id INTEGER PRIMARY KEY,
  cabinet_id INTEGER NOT NULL REFERENCES cabinet(cabinet_id),
  compartment_number INTEGER NOT NULL,
  availability TEXT NOT NULL DEFAULT 'AVAILABLE',
  shoe_status TEXT NOT NULL DEFAULT 'UNKNOWN',
  drying_status TEXT NOT NULL DEFAULT 'IDLE',
  fan_status TEXT NOT NULL DEFAULT 'OFF',
  door_status TEXT NOT NULL DEFAULT 'CLOSED',
  temperature REAL, humidity REAL, updated_at TEXT,
  UNIQUE(cabinet_id, compartment_number)
);
CREATE TABLE IF NOT EXISTS app_user (
  user_id INTEGER PRIMARY KEY,
  display_name TEXT,
  role TEXT NOT NULL DEFAULT 'USER', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS storage_session (
  session_id INTEGER PRIMARY KEY,
  compartment_id INTEGER NOT NULL REFERENCES compartment(compartment_id),
  user_id INTEGER REFERENCES app_user(user_id),
  auth_type TEXT NOT NULL, session_status TEXT NOT NULL,
  token_hash TEXT UNIQUE,
  reserved_at TEXT NOT NULL, token_expires_at TEXT,
  started_at TEXT, ended_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS active_storage_slot
 ON storage_session(compartment_id)
 WHERE session_status IN ('RESERVED','ACTIVE');
CREATE TABLE IF NOT EXISTS sensor_reading (
  reading_id INTEGER PRIMARY KEY,
  compartment_id INTEGER NOT NULL REFERENCES compartment(compartment_id),
  temperature REAL, humidity REAL, external_humidity REAL,
  fan_status TEXT NOT NULL, measured_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reading_slot_time
 ON sensor_reading(compartment_id, measured_at);
CREATE TABLE IF NOT EXISTS shoe_event (
  event_id TEXT PRIMARY KEY,
  compartment_id INTEGER REFERENCES compartment(compartment_id),
  session_id INTEGER REFERENCES storage_session(session_id),
  event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, details_json TEXT
);
CREATE TABLE IF NOT EXISTS drying_session (
  drying_id INTEGER PRIMARY KEY,
  compartment_id INTEGER NOT NULL REFERENCES compartment(compartment_id),
  session_id INTEGER REFERENCES storage_session(session_id),
  started_at TEXT NOT NULL, ended_at TEXT,
  initial_humidity REAL, final_humidity REAL,
  duration_seconds INTEGER, result TEXT
);
