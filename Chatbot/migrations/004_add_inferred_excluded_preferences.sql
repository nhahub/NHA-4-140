-- Migration 004: Add inferred and excluded preference columns
-- Cluster A (Bugs 1, 4, 5) — preference modeling gap

ALTER TABLE user_preferences
  ADD COLUMN IF NOT EXISTS inferred_body_types TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS inferred_min_seats INTEGER,
  ADD COLUMN IF NOT EXISTS inferred_use_case TEXT,
  ADD COLUMN IF NOT EXISTS excluded_body_types TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS excluded_brands TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS excluded_models TEXT[] DEFAULT '{}';
