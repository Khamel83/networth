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

-- Insert sample data
INSERT INTO players (email, name, skill_level, rank, points, wins, losses, trend, is_active)
VALUES
    ('kim@example.com', 'Kim Ndombe', '4.0+ Advanced', 1, 51, 8, 1, 'neutral', true),
    ('sarah@example.com', 'Sarah Kaplan', '4.0 Advanced', 2, 47, 7, 2, 'up', true),
    ('jessica@example.com', 'Jessica Chen', '3.5-4.0 Int-Adv', 3, 43, 6, 2, 'up', true),
    ('maria@example.com', 'Maria Rodriguez', '4.0 Advanced', 4, 41, 6, 3, 'down', true),
    ('emily@example.com', 'Emily Watson', '3.5 Intermediate+', 5, 38, 5, 3, 'neutral', true),
    ('lisa@example.com', 'Lisa Park', '3.5-4.0 Int-Adv', 6, 35, 5, 4, 'up', true),
    ('anna@example.com', 'Anna Thompson', '3.5 Intermediate+', 7, 32, 4, 4, 'neutral', true),
    ('rachel@example.com', 'Rachel Kim', '3.0-3.5 Intermediate', 8, 28, 4, 5, 'down', true),
    ('diana@example.com', 'Diana Lee', '3.5 Intermediate+', 9, 25, 3, 5, 'up', true),
    ('michelle@example.com', 'Michelle Brown', '3.0-3.5 Intermediate', 10, 22, 3, 6, 'neutral', true),
    ('admin@networthtennis.com', 'Admin', '4.0+ Advanced', 99, 0, 0, 0, 'neutral', true)
ON CONFLICT (email) DO NOTHING;

-- Make admin@networthtennis.com an admin
UPDATE players SET is_admin = true WHERE email = 'admin@networthtennis.com';
