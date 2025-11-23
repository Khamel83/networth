-- NET WORTH Tennis Ladder - PostgreSQL Schema
-- Complete database schema for production deployment

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS match_reports CASCADE;
DROP TABLE IF EXISTS monthly_matches CASCADE;
DROP TABLE IF EXISTS match_history CASCADE;
DROP TABLE IF EXISTS players CASCADE;

-- Players table
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    skill_level DECIMAL(2,1) NOT NULL CHECK (skill_level >= 2.0 AND skill_level <= 7.0),
    is_active BOOLEAN DEFAULT TRUE,
    total_score INTEGER DEFAULT 1000,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for performance
CREATE INDEX idx_players_email ON players(email);
CREATE INDEX idx_players_active ON players(is_active);
CREATE INDEX idx_players_score ON players(total_score DESC);

-- Match reports table
CREATE TABLE match_reports (
    id SERIAL PRIMARY KEY,
    player1_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    player2_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    reporter_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    player1_set1 INTEGER DEFAULT 0 CHECK (player1_set1 >= 0 AND player1_set1 <= 7),
    player1_set2 INTEGER DEFAULT 0 CHECK (player1_set2 >= 0 AND player1_set2 <= 7),
    player1_set3 INTEGER DEFAULT 0 CHECK (player1_set3 >= 0 AND player1_set3 <= 7),
    player2_set1 INTEGER DEFAULT 0 CHECK (player2_set1 >= 0 AND player2_set1 <= 7),
    player2_set2 INTEGER DEFAULT 0 CHECK (player2_set2 >= 0 AND player2_set2 <= 7),
    player2_set3 INTEGER DEFAULT 0 CHECK (player2_set3 >= 0 AND player2_set3 <= 7),
    player1_total INTEGER DEFAULT 0,
    player2_total INTEGER DEFAULT 0,
    match_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
    notes TEXT,
    confirmed_by UUID REFERENCES players(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for match_reports
CREATE INDEX idx_match_reports_player1 ON match_reports(player1_id);
CREATE INDEX idx_match_reports_player2 ON match_reports(player2_id);
CREATE INDEX idx_match_reports_status ON match_reports(status);
CREATE INDEX idx_match_reports_date ON match_reports(match_date DESC);

-- Match history table (for historical records)
CREATE TABLE match_history (
    id SERIAL PRIMARY KEY,
    player1_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    player2_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    player1_score INTEGER NOT NULL,
    player2_score INTEGER NOT NULL,
    winner_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    match_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_match_history_player1 ON match_history(player1_id);
CREATE INDEX idx_match_history_player2 ON match_history(player2_id);
CREATE INDEX idx_match_history_date ON match_history(match_date DESC);

-- Monthly matches tracking
CREATE TABLE monthly_matches (
    id SERIAL PRIMARY KEY,
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    month_year VARCHAR(7) NOT NULL, -- Format: YYYY-MM
    matches_played INTEGER DEFAULT 0,
    matches_won INTEGER DEFAULT 0,
    UNIQUE(player_id, month_year)
);

CREATE INDEX idx_monthly_matches_player ON monthly_matches(player_id);
CREATE INDEX idx_monthly_matches_month ON monthly_matches(month_year);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_match_reports_updated_at BEFORE UPDATE ON match_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW ladder_rankings AS
SELECT
    ROW_NUMBER() OVER (ORDER BY total_score DESC) as rank,
    id,
    name,
    email,
    skill_level,
    total_score,
    wins,
    losses,
    CASE
        WHEN (wins + losses) > 0 THEN ROUND((wins::decimal / (wins + losses) * 100), 1)
        ELSE 0
    END as win_percentage
FROM players
WHERE is_active = TRUE
ORDER BY total_score DESC;

CREATE VIEW pending_scores_detail AS
SELECT
    mr.id,
    mr.match_date,
    mr.status,
    mr.notes,
    mr.created_at,
    p1.name as player1_name,
    p1.email as player1_email,
    p2.name as player2_name,
    p2.email as player2_email,
    reporter.name as reporter_name,
    mr.player1_set1,
    mr.player1_set2,
    mr.player1_set3,
    mr.player2_set1,
    mr.player2_set2,
    mr.player2_set3,
    mr.player1_total,
    mr.player2_total,
    CASE
        WHEN mr.player1_total > mr.player2_total THEN p1.name
        ELSE p2.name
    END as winner_name
FROM match_reports mr
JOIN players p1 ON mr.player1_id = p1.id
JOIN players p2 ON mr.player2_id = p2.id
JOIN players reporter ON mr.reporter_id = reporter.id
WHERE mr.status = 'pending'
ORDER BY mr.created_at DESC;

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO railway;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO railway;

-- Sample comment for documentation
COMMENT ON TABLE players IS 'Tennis ladder players with rankings and statistics';
COMMENT ON TABLE match_reports IS 'Match score reports pending or confirmed';
COMMENT ON TABLE match_history IS 'Historical record of all confirmed matches';
COMMENT ON TABLE monthly_matches IS 'Monthly activity tracking per player';

-- Success message
SELECT 'PostgreSQL schema created successfully!' as message;
