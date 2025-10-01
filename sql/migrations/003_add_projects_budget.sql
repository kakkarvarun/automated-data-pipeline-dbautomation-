-- Idempotent add column (works on MySQL 8.0+ with IF NOT EXISTS)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget DECIMAL(10,2);