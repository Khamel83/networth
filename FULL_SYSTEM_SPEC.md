# NET WORTH - Complete Tennis Management System Specification

## Core Features (Minimum Viable Complete System)

### 1. Player Authentication & Profiles
- ✅ Email + password login (tennis123 for all initially)
- ✅ Player profiles with preferences
- ✅ Skill level verification
- ✅ Contact information management

### 2. Smart Partner Matching Algorithm
- **Skill-based matching**: Match players within 0.5 skill level
- **Location-based**: East side LA court preferences
- **Availability matching**: Weekday/weekend preferences
- **Frequency preferences**: How often players want to play
- **Previous matches**: Avoid recent opponents (30-day cooldown)

### 3. Court Information System
- **East Side Court Database**:
  - Vermont Canyon
  - Griffith Park - Riverside
  - Griffith Park - Merry-Go-Round
  - Echo Park
  - Hermon Park
  - Eagle Rock
  - Cheviot Hills
  - Poinsettia Park
- **Court Details**: Lighting, parking, surface conditions
- **Availability tracking**: Court busy times
- **User recommendations**: Court ratings and comments

### 4. Match Management System
- **Match Scheduling**: Calendar integration
- **Score Reporting**: Simple form entry
- **Match Confirmation**: Both players confirm scores
- **Ladder Updates**: Automatic ranking updates
- **Match History**: Complete player match record

### 5. Email Automation System
- **Weekly Match Suggestions**: Personalized partner recommendations
- **Match Reminders**: 24h before scheduled matches
- **Score Follow-ups**: 3 days after matches for unreported scores
- **Ladder Updates**: Weekly ranking changes
- **New Player Welcome**: Onboarding sequence

### 6. Ranking & Analytics
- **Dynamic Ladder**: Real-time ranking updates
- **Win Rate Tracking**: Individual performance metrics
- **Match Frequency**: Playing activity tracking
- **Skill Progression**: Improvement over time
- **Head-to-Head Stats**: Player vs player history

## Technical Implementation

### Database Schema
```sql
-- Enhanced Players Table
ALTER TABLE players ADD COLUMN preferred_courts TEXT; -- JSON array
ALTER TABLE players ADD COLUMN availability TEXT; -- JSON: weekdays/weekends/flexible
ALTER TABLE players ADD COLUMN match_frequency TEXT; -- weekly/biweekly/monthly
ALTER TABLE players ADD COLUMN last_opponent_date DATE;
ALTER TABLE players ADD COLUMN preferred_match_times TEXT; -- morning/afternoon/evening
ALTER TABLE players ADD COLUMN is_looking_for_match BOOLEAN DEFAULT FALSE;

-- Courts Table
CREATE TABLE courts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    surface TEXT,
    lighting BOOLEAN,
    parking TEXT,
    notes TEXT,
    rating DECIMAL(3,2),
    active BOOLEAN DEFAULT TRUE
);

-- Match Suggestions Table
CREATE TABLE match_suggestions (
    id TEXT PRIMARY KEY,
    player1_id TEXT,
    player2_id TEXT,
    suggested_date DATE,
    status TEXT DEFAULT 'pending', -- pending/accepted/declined/expired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player1_id) REFERENCES players (id),
    FOREIGN KEY (player2_id) REFERENCES players (id)
);

-- Enhanced Match Reports
ALTER TABLE match_reports ADD COLUMN court_id TEXT;
ALTER TABLE match_reports ADD COLUMN match_time TIME;
ALTER TABLE match_reports ADD COLUMN duration_minutes INTEGER;
ALTER TABLE match_reports ADD COLUMN weather TEXT;
```

### Email Templates
1. **Match Suggestion**: "You've been matched with [Player] - similar skill level"
2. **Match Reminder**: "Your match tomorrow at [Court] - confirm attendance"
3. **Score Request**: "How did your match with [Player] go? Report score here"
4. **Weekly Ladder**: "Ladder updates: You moved up/down X positions this week"
5. **New Player**: "Welcome to NET WORTH! Here's how to get started"

### Partner Matching Algorithm
```python
def find_matches(player_id):
    player = get_player(player_id)
    all_players = get_all_active_players()

    matches = []
    for other in all_players:
        if other.id == player_id: continue
        if other.id == player.last_opponent_id: continue  # 30-day cooldown

        # Skill compatibility (within 0.5 level)
        if abs(skill_level_to_number(player.skill) - skill_level_to_number(other.skill)) > 0.5:
            continue

        # Availability compatibility
        if not availability_matches(player.availability, other.availability):
            continue

        # Calculate match score
        score = calculate_match_score(player, other)
        if score > 0.7:  # Good match threshold
            matches.append({'player': other, 'score': score})

    return sorted(matches, key=lambda x: x['score'], reverse=True)[:3]
```

### Automated Email Schedule
- **Monday 9AM**: Weekly match suggestions
- **Daily 6PM**: Next-day match reminders
- **Thursday 6PM**: Score follow-ups for unreported matches
- **Friday 5PM**: Weekly ladder summary
- **Real-time**: New match confirmations and instant notifications

## Non-Interactive Deployment (Headless Operation)

### Automatic Processes
```bash
# Daily cron jobs
0 9 * * 1 python3 send_weekly_suggestions.py    # Monday 9AM
0 18 * * * python3 send_match_reminders.py       # Daily 6PM
0 18 * * 4 python3 send_score_followups.py      # Thursday 6PM
0 17 * * 5 python3 send_ladder_updates.py        # Friday 5PM
```

### API Endpoints (for web interface)
- `POST /api/match-suggest` - Generate new matches
- `POST /api/report-score` - Submit match results
- `GET /api/player-matches/{id}` - Player's match history
- `PUT /api/player-preferences/{id}` - Update preferences
- `POST /api/court-feedback` - Submit court ratings

## Implementation Priority

### Phase 1: Core Functionality (Week 1)
1. Enhanced database schema
2. Partner matching algorithm
3. Basic email automation
4. Score reporting system

### Phase 2: User Experience (Week 2)
1. Court information system
2. Preference management UI
3. Match scheduling interface
4. Mobile responsiveness

### Phase 3: Automation & Analytics (Week 3)
1. Advanced email sequences
2. Performance analytics
3. Match history insights
4. Ladder statistics

## Gmail API Setup Requirements

### Google Cloud Configuration
- Enable Gmail API
- Create service account
- Generate OAuth credentials
- Set up domain-wide delegation

### Email Authentication
- Use Ashley's email for sending
- Set up proper SPF/DKIM records
- Configure email templates
- Test deliverability

## Success Metrics
- **Match Rate**: % of suggestions that result in actual matches
- **Player Activity**: Matches per player per month
- **Ladder Movement**: Players actively changing positions
- **Email Engagement**: Open rates and click-through rates
- **User Satisfaction**: Player feedback and retention

## Privacy & Data Protection
- Minimal data collection
- No third-party analytics
- Secure email handling
- Player consent for communications
- GDPR-like data protection standards

This system will provide everything playtennisla.com offers but focused specifically on East Side women's tennis, with better privacy and no cost barriers.