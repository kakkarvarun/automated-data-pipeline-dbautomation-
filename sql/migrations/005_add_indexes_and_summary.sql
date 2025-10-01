-- 005_add_indexes_and_summary.sql

-- Add index on start timestamp if not present (MySQL ignores duplicate creation gracefully)
CREATE INDEX IF NOT EXISTS idx_trips_start_ts ON trips_chicago (trip_start_timestamp);

-- Daily summary table (idempotent)
CREATE TABLE IF NOT EXISTS daily_trips (
  trip_date DATE PRIMARY KEY,
  trips_count BIGINT,
  last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Populate/refresh summary safely (idempotent via upsert)
INSERT INTO daily_trips (trip_date, trips_count, last_refreshed)
SELECT DATE(trip_start_timestamp) AS trip_date, COUNT(*) AS trips_count, NOW()
FROM trips_chicago
GROUP BY DATE(trip_start_timestamp)
ON DUPLICATE KEY UPDATE
  trips_count = VALUES(trips_count),
  last_refreshed = NOW();
