"""
NET WORTH Tennis - Configuration
================================
All user-defined elements in one place:
- Branding (name, colors, tagline)
- Email copy (subjects, body text)
- Courts list
- Skill levels

Edit this file to customize the ladder for a different league.
"""

# =============================================================================
# BRANDING
# =============================================================================

LEAGUE_NAME = "NET WORTH"
LEAGUE_TAGLINE = "East Side LA Women's Tennis"
SITE_URL = "https://networthtennis.com"  # Fallback, also set via SITE_URL env var

# Colors (hex codes)
COLORS = {
    'background': '#0a0a0a',       # Near black
    'card_bg': '#121212',          # Dark gray
    'border': '#2a2a2a',           # Subtle border
    'text_primary': '#e8e8e8',     # Off-white
    'text_secondary': '#888888',   # Gray
    'gold': '#D4AF37',             # Accent - headers, buttons
    'lime': '#CCFF00',             # Accent - highlights, opponent names
    'red': '#DC143C',              # Urgent/warning
}

# =============================================================================
# EMAIL SUBJECTS
# =============================================================================

EMAIL_SUBJECTS = {
    # Beginning of month - new pairings
    'new_pairing': "Your {period} Tennis Match",

    # Mid-month reminder
    'mid_month': "Quick check-in: {period} match",

    # End of month / last chance
    'last_chance': "Last chance: {period} ends soon!",

    # Match recorded confirmation
    'score_confirmed': "Match Recorded!",

    # Welcome email
    'welcome': "Welcome to {league_name}!",

    # Outstanding match from previous month
    'outstanding': "Did you finish your {period} match?",
}

# =============================================================================
# EMAIL COPY
# =============================================================================

EMAIL_COPY = {
    # Pairing email (beginning of month)
    'pairing_intro': "You've been paired for {period}!",
    'pairing_instructions': "Coordinate with your opponent to schedule your match this month. Play 2 sets and report your score when done.",

    # Mid-month reminder
    'mid_month_intro': "Just checking in on your {period} match.",
    'mid_month_body': "Haven't played yet? No rush - you have {days_left} days left this month.",

    # Last chance
    'last_chance_intro': "{period} ends in just a few days!",
    'last_chance_body': "If you can't make it work, no worries - just let us know and we'll pair you with someone else next month.",

    # Outstanding match reminder
    'outstanding_intro': "Quick question about your {period} match",
    'outstanding_body': "Did you and {opponent_name} ever get to play? If so, report the score anytime. If not, no problem - just wanted to check in.",

    # Welcome
    'welcome_how_it_works': """
1. Each month you'll be paired with another player
2. Coordinate with them to schedule your match
3. Play 2 sets at any approved court
4. Report your score on the dashboard
5. Climb the ladder based on games won!
""",

    # Report score button
    'button_report_score': "Report Score →",
    'button_view_ladder': "View Ladder →",
    'button_set_availability': "Set Availability →",
}

# =============================================================================
# COURTS (Approved venues)
# =============================================================================

APPROVED_COURTS = [
    "Vermont Canyon",
    "Griffith Park - Riverside",
    "Griffith Park - Merry-Go-Round",
    "Echo Park",
    "Hermon Park",
    "Eagle Rock",
    "Cheviot Hills",
    "Poinsettia Park",
]

# For email display
COURTS_DISPLAY = " • ".join(APPROVED_COURTS[:7])  # First 7 for brevity

# =============================================================================
# SKILL LEVELS
# =============================================================================

SKILL_LEVELS = [
    ('4.5', '4.5 Advanced+'),
    ('4.0', '4.0 Advanced'),
    ('3.5+', '3.5+ Intermediate+'),
    ('3.5', '3.5 Intermediate'),
    ('3.0', '3.0 Beginner+'),
    ('2.5', '2.5 Beginner'),
]

# =============================================================================
# TIME SLOTS
# =============================================================================

TIME_SLOTS = {
    'morning': 'Mornings (6am-12pm)',
    'afternoon': 'Afternoons (12pm-6pm)',
    'evening': 'Evenings (6pm-10pm)',
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_site_url():
    """Get site URL from env or fallback to config"""
    import os
    return os.environ.get('SITE_URL', SITE_URL)


def format_subject(template_key, **kwargs):
    """Format an email subject with variables"""
    template = EMAIL_SUBJECTS.get(template_key, template_key)
    kwargs['league_name'] = LEAGUE_NAME
    return template.format(**kwargs)


def get_courts_html():
    """Get courts list formatted for email HTML"""
    return f'<div class="court-list">{COURTS_DISPLAY}</div>'
