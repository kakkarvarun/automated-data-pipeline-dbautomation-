USE companydb;
SET @idx_exists := (
  SELECT COUNT(*) FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'trips_chicago'
    AND index_name = 'idx_trips_start_ts'
);
SET @ddl := IF(@idx_exists > 0,
  'DO 0',
  'CREATE INDEX idx_trips_start_ts ON trips_chicago (trip_start_timestamp)'
);
PREPARE s FROM @ddl; EXECUTE s; DEALLOCATE PREPARE s;
CREATE TABLE IF NOT EXISTS daily_trips (
  trip_date DATE PRIMARY KEY,
  trips_count BIGINT,
  last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
INSERT INTO daily_trips (trip_date, trips_count, last_refreshed)
SELECT DATE(trip_start_timestamp) AS trip_date, COUNT(*) AS trips_count, NOW()
FROM trips_chicago
WHERE trip_start_timestamp IS NOT NULL
GROUP BY DATE(trip_start_timestamp)
ON DUPLICATE KEY UPDATE
  trips_count = VALUES(trips_count),
  last_refreshed = NOW();
