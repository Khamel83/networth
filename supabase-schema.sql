-- NET WORTH Tennis Ladder - Supabase Schema
-- Run this in the Supabase SQL Editor to set up your database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Players table
CREATE TABLE IF NOT EXISTS players (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    skill_level VARCHAR(50) DEFAULT '3.5 Intermediate+',
    rank INTEGER DEFAULT 99,
    points INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    trend VARCHAR(20) DEFAULT 'neutral', -- 'up', 'down', 'neutral'
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    court_preference VARCHAR(255),
    availability TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    winner_id UUID REFERENCES players(id) ON DELETE SET NULL,
    loser_id UUID REFERENCES players(id) ON DELETE SET NULL,
    winner_score VARCHAR(50) NOT NULL,
    loser_score VARCHAR(50) NOT NULL,
    court VARCHAR(255),
    notes TEXT,
    played_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reported_by UUID REFERENCES players(id) ON DELETE SET NULL,
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_players_rank ON players(rank) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_players_email ON players(email);
CREATE INDEX IF NOT EXISTS idx_matches_played_at ON matches(played_at DESC);
CREATE INDEX IF NOT EXISTS idx_matches_winner ON matches(winner_id);
CREATE INDEX IF NOT EXISTS idx_matches_loser ON matches(loser_id);

-- Function to update rankings after a match
CREATE OR REPLACE FUNCTION update_player_rankings()
RETURNS TRIGGER AS $$
BEGIN
    -- Update winner stats
    UPDATE players
    SET
        wins = wins + 1,
        points = points + 3,
        trend = 'up',
        updated_at = NOW()
    WHERE id = NEW.winner_id;

    -- Update loser stats
    UPDATE players
    SET
        losses = losses + 1,
        points = GREATEST(0, points - 1),
        trend = 'down',
        updated_at = NOW()
    WHERE id = NEW.loser_id;

    -- Recalculate all ranks based on points
    WITH ranked AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY points DESC, wins DESC, created_at ASC) as new_rank
        FROM players
        WHERE is_active = true
    )
    UPDATE players p
    SET rank = r.new_rank
    FROM ranked r
    WHERE p.id = r.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update rankings on new match
DROP TRIGGER IF EXISTS trigger_update_rankings ON matches;
CREATE TRIGGER trigger_update_rankings
    AFTER INSERT ON matches
    FOR EACH ROW
    EXECUTE FUNCTION update_player_rankings();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for players updated_at
DROP TRIGGER IF EXISTS trigger_players_updated_at ON players;
CREATE TRIGGER trigger_players_updated_at
    BEFORE UPDATE ON players
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Row Level Security (RLS)
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

-- Policies: Anyone can read players
CREATE POLICY "Players are viewable by everyone"
    ON players FOR SELECT
    USING (true);

-- Policies: Authenticated users can update their own player
CREATE POLICY "Users can update own player"
    ON players FOR UPDATE
    USING (auth.uid()::text = id::text);

-- Policies: Anyone can read matches
CREATE POLICY "Matches are viewable by everyone"
    ON matches FOR SELECT
    USING (true);

-- Policies: Authenticated users can insert matches
CREATE POLICY "Authenticated users can report matches"
    ON matches FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- Insert real player data from NET WORTH Tennis East Side LA
INSERT INTO players (email, name, skill_level, rank, points, wins, losses, trend, is_active)
VALUES
    ('kimberly@ndombe.com', 'Kim Ndombe', '4.5 Advanced+', 1, 1510, 18, 0, 'up', true),
    ('nmcoffen@gmail.com', 'Natalie Coffen', '4.5 Advanced+', 2, 1500, 16, 1, 'up', true),
    ('Sara.Chrisman@gmail.com', 'Sara Chrisman', '4.5 Advanced+', 3, 1490, 14, 2, 'neutral', true),
    ('ariannahairston@gmail.com', 'Arianna Hairston', '4.5 Advanced+', 4, 1480, 12, 3, 'neutral', true),
    ('hannah.shin4@gmail.com', 'Hannah Shin', '4.5 Advanced+', 5, 1450, 10, 4, 'up', true),
    ('aapelian@gmail.com', 'Alik Apelian', '4.5 Advanced+', 6, 1450, 8, 5, 'neutral', true),
    ('sayhellotohanna@gmail.com', 'Hanna Pavlova', '4.2 Advanced', 7, 1410, 6, 6, 'down', true),
    ('Madeline.whitby@gmail.com', 'Maddy Whitby', '4.1 Advanced', 8, 1380, 4, 7, 'neutral', true),
    ('Allison.n.dunne@gmail.com', 'Allison Dunne', '4.0 Advanced', 9, 1370, 2, 8, 'up', true),
    ('Ashleybrooke.kaufman@gmail.com', 'Ashley Brooke Kaufman', '4.0 Advanced', 10, 1330, 0, 9, 'neutral', true),
    ('kaitlinmariekelly@gmail.com', 'Kaitlin Kelly', '4.0 Advanced', 11, 1320, 0, 10, 'neutral', true),
    ('Pagek.eaton@gmail.com', 'Page Eaton', '4.0 Advanced', 12, 1300, 0, 11, 'neutral', true),
    ('BySarahYun@gmail.com', 'Sarah Yun', '3.8 Intermediate+', 13, 1290, 0, 12, 'neutral', true),
    ('Laurenjaneberger@gmail.com', 'Laurie Berger', '3.7 Intermediate+', 14, 1260, 0, 13, 'neutral', true),
    ('Katelinmorey@gmail.com', 'Katie Morey', '3.6 Intermediate', 15, 1240, 0, 14, 'neutral', true),
    ('Alyssa.j.perry@gmail.com', 'Alyssa Perry', '3.5 Intermediate', 16, 1200, 0, 15, 'neutral', true),
    ('admin@networthtennis.com', 'Admin', '4.0+ Advanced', 99, 0, 0, 0, 'neutral', true)
ON CONFLICT (email) DO NOTHING;

-- Make admin@networthtennis.com an admin
UPDATE players SET is_admin = true WHERE email = 'admin@networthtennis.com';
