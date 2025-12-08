-- =============================================================
-- MIGRATION: Add Player Profile Fields
-- Run this in Supabase SQL Editor to add profile features
-- =============================================================

-- Add profile fields to players table
ALTER TABLE players
ADD COLUMN IF NOT EXISTS profile_picture TEXT,
ADD COLUMN IF NOT EXISTS neighborhood TEXT,
ADD COLUMN IF NOT EXISTS instagram_handle TEXT,
ADD COLUMN IF NOT EXISTS fun_fact TEXT;

-- Add some sample profile data for testing
-- (You can customize these later with real data)
-- Note: profile_picture intentionally left NULL - players will show initials

UPDATE players SET
    neighborhood = 'Silver Lake',
    instagram_handle = 'kimndombe',
    fun_fact = 'Favorite player: Serena Williams'
WHERE email = 'kimberly@ndombe.com';

UPDATE players SET
    neighborhood = 'Echo Park',
    instagram_handle = 'natalietennis',
    fun_fact = 'Favorite match: 2019 Wimbledon Final'
WHERE email = 'nmcoffen@gmail.com';

UPDATE players SET
    neighborhood = 'Los Feliz',
    instagram_handle = 'sarachrisman',
    fun_fact = 'Favorite player: Naomi Osaka'
WHERE email = 'sara.chrisman@gmail.com';

UPDATE players SET
    neighborhood = 'Highland Park',
    instagram_handle = 'ariannatennis',
    fun_fact = 'Favorite player: Coco Gauff'
WHERE email = 'ariannahairston@gmail.com';

UPDATE players SET
    neighborhood = 'Atwater Village',
    instagram_handle = 'alikapelian',
    fun_fact = 'Favorite match: 2023 Australian Open Final'
WHERE email = 'aapelian@gmail.com';

UPDATE players SET
    neighborhood = 'Eagle Rock',
    instagram_handle = 'hannahshintennis',
    fun_fact = 'Favorite player: Venus Williams'
WHERE email = 'hannah.shin4@gmail.com';

UPDATE players SET
    neighborhood = 'Downtown LA',
    instagram_handle = 'hannapavlova',
    fun_fact = 'Favorite player: Maria Sharapova'
WHERE email = 'sayhellotohanna@gmail.com';

UPDATE players SET
    neighborhood = 'Burbank',
    instagram_handle = 'maddywhitby',
    fun_fact = 'Favorite match: 2012 Wimbledon Final'
WHERE email = 'madeline.whitby@gmail.com';

UPDATE players SET
    neighborhood = 'Pasadena',
    instagram_handle = 'allisondunne',
    fun_fact = 'Favorite player: Iga Świątek'
WHERE email = 'allison.n.dunne@gmail.com';

UPDATE players SET
    neighborhood = 'Glendale',
    instagram_handle = 'ashleybrookekaufman',
    fun_fact = 'Favorite player: Billie Jean King'
WHERE email = 'ashleybrooke.kaufman@gmail.com';

-- Set default neighborhoods for remaining players
UPDATE players
SET neighborhood = 'East Side LA'
WHERE neighborhood IS NULL AND is_admin = false;

-- =============================================================
-- VERIFICATION
-- =============================================================
SELECT name, neighborhood, instagram_handle, fun_fact
FROM players
WHERE is_admin = false AND neighborhood IS NOT NULL
ORDER BY rank
LIMIT 15;
