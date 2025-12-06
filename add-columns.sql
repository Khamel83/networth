-- Add missing columns to players table
-- Run this in Supabase SQL Editor

-- Availability columns (simple boolean for time-of-day preferences)
ALTER TABLE players ADD COLUMN IF NOT EXISTS available_morning BOOLEAN DEFAULT true;
ALTER TABLE players ADD COLUMN IF NOT EXISTS available_afternoon BOOLEAN DEFAULT true;
ALTER TABLE players ADD COLUMN IF NOT EXISTS available_evening BOOLEAN DEFAULT true;

-- Pause feature (player can sit out until this date)
ALTER TABLE players ADD COLUMN IF NOT EXISTS unavailable_until DATE DEFAULT NULL;

-- Phone number (optional, for text coordination)
ALTER TABLE players ADD COLUMN IF NOT EXISTS phone TEXT DEFAULT NULL;

-- Verify columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'players'
AND column_name IN ('available_morning', 'available_afternoon', 'available_evening', 'unavailable_until', 'phone');
