# Ashley's Christmas 2025 Feedback - Master Tracking Document

**Date Received:** December 27, 2025
**Source:** Ashley Kaufman via email
**Status:** Implementation In Progress
**Branch:** `feature/ashley-christmas-2025`

---

## Design Inspiration

**Reference Image:** `ashley_design_concept.png`

### Color Palette
- Pink: `#d165a4`
- Orange: `#ec613e`
- Peach: `#e7b4b5`
- Gradient: Pink → Orange → Peach (diagonal)

### Typography
- Sans-serif font (geometric style like in reference image)
- Selected: **Poppins** for headings, **Inter** for body

### Effects
- Grainy texture overlay (subtle noise effect)
- Clean, modern, feminine aesthetic

---

## Admin Changes

- [ ] Add Natalie (nmcoffen@gmail.com) as admin

---

## Throughout Site (Global)

- [ ] Update color scheme to pink/orange/peach gradient
- [ ] Add grainy texture overlay
- [ ] Switch to sans-serif fonts (Poppins/Inter)
- [ ] Two different views: logged in vs not logged in

### Not Logged In Navigation
- How It Works
- Courts
- Game Play & Scoring (was Rules)
- Join Now (button)
- Sign In (button)

### Logged In Navigation
- Rankings
- How It Works
- Courts
- Game Play & Scoring
- My Profile (button)
- Sign Out (button)

---

## PAGE: Landing Page (index.html)

### Copy Changes
- [ ] "East Side Los Angeles Women's Tennis" → "A WOMEN'S TENNIS LEAGUE ON LA'S EAST SIDE"
- [ ] "Climb the Ladder" → "Net Worth"
- [ ] Tagline: "Tennis. Events. Community."
- [ ] Remove tabs jumping to parts of main page; make them go to actual pages

### New Membership Section
```
Join the league!

Create your player profile and send your membership fee via Venmo @NCOFFEN (Natalie).
If you join after the month has started, you'll be matched in the next month.

Membership Options:

TIER 1: THE PLAYERS - $35/year
- Monthly match assignments
- New website for match coordination + score submission
- Two Grand Slam watch parties
- Access to additional clinics, training sessions, and events
- Access to the WhatsApp community

TIER 2: THE SOCIAL BUTTERFLIES - $45/year
- Two Grand Slam watch parties
- Access to additional clinics, training sessions, and events
- Access to the WhatsApp community
- No matches included in this tier

[Join Us!] button
```

---

## PAGE: Rankings (was "Ladder")

- [ ] Rename "Ladder" → "Rankings"
- [ ] Remove "Monthly Rankings" header
- [ ] "The Ladder" → "League Rankings"
- [ ] Remove ratings column
- [ ] Remove trend column (build out later)
- [ ] Add player thumbnails (photos or tennis ball default)
- [ ] Make thumbnails clickable to profile pages

---

## PAGE: Profile Pages (NEW)

### Fields to Display
- Photo (or tennis ball default)
- Name
- Membership tier (Player / Social Butterfly)
- Availability slots
- Favorite players

### Join Flow Collects
- Name* (required)
- Email* (required)
- Phone number* (required)
- Membership tier* (checkbox):
  - [ ] Player - $35 (Monthly match assignments plus access to all league events and community)
  - [ ] Social Butterfly - $45 (All the social events and community, with no matches assigned)
- Availability (multi-select) - *greyed out if Social Butterfly selected*:
  - Weekdays before 9am
  - Weekdays 9-5
  - Weekdays after 5pm
  - Weekends before 9am
  - Weekends 9-5
  - Weekends after 5pm
- Fave players (text input)

### Join Flow Footer
```
Have ideas for the league or want to help plan events?
Get in touch with Ash (hyperlinked: ashleybrooke.kaufman@gmail.com) and Natalie (hyperlinked: nmcoffen@gmail.com)!
```

---

## PAGE: Personal Player Profile (Dashboard) - Player Tier

- [ ] Move "Sit Out This Month" button to TOP (not nested under preferences)
- [ ] Add explanatory text under sit out button:
```
Clicking this button pauses match assignments until you click back in.
If you rejoin mid-month, you'll be assigned starting the following month.
You'll receive email confirmations for each month you're paused.
```
- [ ] Rename "Preferences" → "My Info"
- [ ] Name - editable - cannot be blank
- [ ] Email - editable - cannot be blank
- [ ] Phone number - cannot be blank
- [ ] Availability categories (new):
  - Weekdays before 9am
  - Weekdays 9-5
  - Weekdays after 5pm
  - Weekends before 9am
  - Weekends 9-5
  - Weekends after 5pm
- [ ] "Save preferences" → "Save my info"
- [ ] Button turns white/highlighted when changes need saving

---

## PAGE: Personal Player Profile (Dashboard) - Social Butterfly Tier

- [ ] No playing, ranking sections
- [ ] "Preferences" → "My Info"
- [ ] Name - editable - cannot be blank
- [ ] Email - editable - cannot be blank
- [ ] Phone number - cannot be blank
- [ ] "I want to start playing!" button with text:
```
Clicking this button adds you to the match queue for the following month.
If you need to sit out in the future, be sure to return to your profile and update your status before each month's match assignments.
```
- [ ] When clicked: user becomes "Player" tier
- [ ] Availability section appears and must be filled before saving
- [ ] Availability section greyed out for Social Butterflies until they click "I want to start playing!"

---

## PAGE: Login (login.html)

- [ ] Remove "Player Login" - this is for anyone to login
- [ ] "Not in the league yet, contact organizer" → "Not in the league yet? Join us" (hyperlinked to join flow)
- [ ] Add explanatory text:
```
After entering your email, you'll receive a sign-in link from Supabase Auth (noreply@mail.app.supabase.io).
Click the link in that email to access your profile. No password required.
```
- [ ] "Back to ladder" → "Back to Net Worth" (hyperlinked to landing page)

---

## PAGE: Post-Email Entry Confirmation

- [ ] Remove "Back to ladder"
- [ ] Should read: "Back to Net Worth" (hyperlinked to landing page)

---

## PAGE: How It Works

- [ ] Remove "The System" heading

### Block 1 - Get Paired
```
At the start of each month, you'll be automatically paired with an opponent through our league platform.
You'll both receive an email connecting you, so all you need to do is reply and coordinate availability.

You can also check each other's player profiles to see stated availability,
but scheduling is always at your mutual convenience.
```

### Block 2 - Play Your Match
```
You decide the date, time, and location that work best for both of you.
```

### Block 3 - Log Your Score
```
After your match, simply log into the league website and record your score.
```

### After Blocks
```
Want to play more than just one match? Go for it! Feel free to reach out to other players and set up additional matches.
Just note that only one match per month counts toward your ranking.
```

### Special Block - Need to Take a Month Off?
```
Life happens. If you need to sit out for a month (or more), you can toggle your availability directly in your player dashboard.

- Simply mark yourself as unavailable for the upcoming month
- You'll receive a reminder at the end of each month to update your availability
- Toggling off ensures you won't be assigned a match while you're away

We ask everyone to please be thoughtful about updating their availability so match assignments stay smooth for the whole league.
```

---

## PAGE: Courts

- [ ] Remove "Home Turf" heading
- [ ] "Approved Courts" → "Recommended Courts"
- [ ] Add block: "Feel free to work out other options with your opponent!"

---

## PAGE: Rules → "Game Play and Scoring"

- [ ] Rename page: "Rules" → "Game Play and Scoring"

### Section: How Scoring Works - Match Format
```
Matches are played as two sets. Rankings are based on total games won, not on winning or losing the match.

Example:
- Player 1 wins Set 1 6–2 and loses Set 2 4–6
- Player 1 total games won: 10
- Player 2 total games won: 8
```

### Section: How Sets End
```
Each set is played to 6 games. If the score reaches 6–5, one additional game is played to determine how the set ends.

- If the leading player wins the next game, the set ends 7–5.
- If the trailing player wins the next game, the set ends 6–6.
- There are no tiebreakers.

Example:
- Player A leads 6–5.
- Player A wins the next game → 7–5, set over.
- Player B wins the next game → 6–6, set ends as a draw.
```

### Section: Maximum Possible Score
```
Because matches consist of two sets and each set can end with a maximum of 7 games won,
the highest possible total score in a match is 14 games.

Example:
- Set 1: 7–5
- Set 2: 7–5
- Total games won by the winner: 14
```

### Section: Reporting Your Score
```
After your match, report your total games won in the appropriate month.

Guidelines:
- Scores must be recorded in the correct month.
- Always report a score, even if your total is 0.
```

### Section: Forfeits & Special Situations

#### Forfeit Without Playing
```
- Opponent receives 6 points.
- You receive 0 points.
- If feasible, rescheduling is encouraged, even if the month has already passed.
```

#### Match Ends Early Due to Injury
```
You and your opponent may agree to record the score as-is or reschedule to finish the match.

If the injured player chooses to forfeit, the winner receives either 6 points or the number of games already won, whichever is higher.
```

---

## PAGE: Footer (all pages)

- [ ] "Rules" link → "Game Play & Scoring"
- [ ] Add "Contact Us" → mailto:ashleybrooke.kaufman@gmail.com,nmcoffen@gmail.com

---

## EMAIL: Matching/Pairing Email

**Subject:** You're matched for {{Month}} 🎾

**Body:**
```
Hi {{Player 1}} and {{Player 2}},

You've been matched for a league game in {{Month}}.

Go ahead… make the first move 😉
Please reply all with a few dates and times you're available so you can get your match on the calendar.

You're free to choose the date, time, and location that work best for both of you.

You can view match details and log your score here:
👉 {{League Link}}

Have fun and happy hitting,
Net Worth
```

---

## EMAIL: Login Confirmation (Supabase)

- [ ] Update CTA: "Click here to be logged into your Net Worth player profile"

---

## MATCHING LOGIC: Performance Bands (RMS)

### Rolling Match Score (RMS)
- Calculate: Average total games won per match
- Look at last 3 completed matches (or fewer if new)

### Performance Bands (Internal Only)
- Developing: RMS ≤ 6
- Competitive: RMS 6.1–9
- Strong: RMS 9.1–12
- Dominant: RMS > 12

### Monthly Matching Logic
1. Build eligible player pool
2. Group players by performance band
3. Within each band: randomize and pair
4. Odd player floats one band up or down
5. New players (no RMS): match together when possible
6. Anti-staleness: avoid same matchup within last 3 months
7. Small league (<8 players): skip banding, match randomly

### Admin Flex (Odd Player Handling)
- If odd count: remove Natalie first
- If Natalie unavailable: remove Ashley
- Admin player simply sits out that month

---

## BUSINESS LOGIC: Membership Tiers

### Who Is Eligible for Matching
- User role = Player
- User is marked as available
- User is not sitting out
- User joined before match generation runs
- **Social Butterflies are NEVER included in match assignments**

### Timing
- Matches generated once per month (1st of month)
- Status changes after match run apply to next month

### Sit-Out Button Behavior
- Clicking "Sit Out": immediately marks unavailable, removes from current/future pools
- Status persists month-to-month until user actively clicks back in
- Clicking back in before match run = eligible that month
- Clicking back in after month started = eligible next month
- **System never auto-reinstates - opting back in is always explicit**

### Email Confirmations
- When user clicks "Sit Out": send confirmation email
- End of each month: if user still opted out, send reminder/confirmation
- When user clicks back in: send confirmation with eligible month

### Social Butterfly → Player Upgrade
- Role changes from Social Butterfly → Player
- Availability section becomes required and enabled
- User cannot save until availability completed
- User added to match queue for following month
- Confirmation messaging clarifies when matching begins

---

## DECISIONS MADE

1. **Tier Migration:** Default all existing players to 'Player' tier
2. **Availability Migration:** Start fresh with new slots (clear old data)
3. **RMS Matching:** Implement now (not Phase 2)
4. **Font:** Poppins (matching design concept geometric sans-serif)
5. **Profile Photos:** Add photo upload (with tennis ball fallback)
6. **Content Management:** Extract to JSON templates for easy editing
7. **Supabase Email:** Include customization instructions

---

## FILES TO CREATE/MODIFY

### New Files
- `public/profile.html` - Player profile pages
- `api/upload.py` - Photo upload endpoint
- `content/landing.json` - Landing page content
- `content/how-it-works.json` - How it works content
- `content/courts.json` - Courts content
- `content/rules.json` - Game Play & Scoring content
- `content/emails.json` - Email templates
- `content/ui.json` - UI labels and form text

### Modified Files
- `public/index.html` - Visual rebrand + new copy + membership section
- `public/login.html` - Visual rebrand + copy updates
- `public/dashboard.html` - New availability + sit-out button + tier logic
- `public/join.html` - New fields + tier selection + photo upload
- `public/rules.html` - Complete rewrite as "Game Play and Scoring"
- `public/admin.html` - Visual rebrand
- `public/support.html` - Visual rebrand
- `public/privacy.html` - Visual rebrand
- `api/pairings.py` - RMS-based matching algorithm
- `api/profile.py` - New fields + tier handling
- `api/join.py` - New fields handling
- `api/email.py` - New matching email template
- `api/config.py` - Updated branding colors
- `supabase-final-setup.sql` - Schema updates

### Database Changes
```sql
-- New columns
ALTER TABLE players ADD COLUMN membership_tier VARCHAR(20) DEFAULT 'player';
ALTER TABLE players ADD COLUMN avatar_url TEXT;
ALTER TABLE players ADD COLUMN favorite_players TEXT;
ALTER TABLE players ADD COLUMN rms_score DECIMAL(4,2);
ALTER TABLE players ADD COLUMN rms_band VARCHAR(20);

-- Replace availability columns
ALTER TABLE players DROP COLUMN IF EXISTS available_morning;
ALTER TABLE players DROP COLUMN IF EXISTS available_afternoon;
ALTER TABLE players DROP COLUMN IF EXISTS available_evening;
ALTER TABLE players ADD COLUMN avail_weekday_early BOOLEAN DEFAULT false;
ALTER TABLE players ADD COLUMN avail_weekday_day BOOLEAN DEFAULT false;
ALTER TABLE players ADD COLUMN avail_weekday_late BOOLEAN DEFAULT false;
ALTER TABLE players ADD COLUMN avail_weekend_early BOOLEAN DEFAULT false;
ALTER TABLE players ADD COLUMN avail_weekend_day BOOLEAN DEFAULT false;
ALTER TABLE players ADD COLUMN avail_weekend_late BOOLEAN DEFAULT false;

-- Add Natalie as admin
UPDATE players SET is_admin = true WHERE email = 'nmcoffen@gmail.com';
```

---

## PROGRESS TRACKER

- [ ] Phase 1: Database schema updates
- [ ] Phase 2: Visual rebrand
- [ ] Phase 3: Two site views (nav)
- [ ] Phase 4: Profile system
- [ ] Phase 5: Join flow updates
- [ ] Phase 6: Page-by-page copy
- [ ] Phase 7: Email templates
- [ ] Phase 8: RMS matching algorithm
- [ ] Phase 9: Business logic
- [ ] Phase 10: Photo upload system
- [ ] Phase 11: Content templates
- [ ] Phase 12: Supabase email docs
- [ ] Testing
- [ ] Merge to master
