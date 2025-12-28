# Ashley Christmas 2025 - Implementation Checklist

## GLOBAL
- [x] Color scheme: pink #d165a4, orange #ec613e, peach #e7b4b5
- [x] Grainy texture overlay
- [x] Poppins font for headings
- [x] Inter font for body
- [x] Two views: logged in vs not logged in

### Not Logged In Navigation
- [x] How It Works link
- [x] Courts link
- [x] Game Play & Scoring link (was Rules)
- [x] Join Now button
- [x] Sign In button
- [ ] NO Rankings link (verify hidden)

### Logged In Navigation
- [x] Rankings link
- [x] How It Works link
- [x] Courts link
- [x] Game Play & Scoring link
- [x] My Profile button (was My Dashboard)
- [x] Sign Out button

---

## LANDING PAGE (index.html)
- [x] Header: "A WOMEN'S TENNIS LEAGUE ON LA'S EAST SIDE"
- [x] Title: "Net Worth" (was "Climb the Ladder")
- [x] Tagline: "Tennis. Events. Community."
- [ ] Nav links go to actual pages, not anchors (line 66) - PARTIAL: Courts still #anchor
- [x] Membership section with tiers
- [x] Tier 1: Players - $35/year with all features listed
- [x] Tier 2: Social Butterflies - $45/year with features listed
- [x] Join Us! button
- [x] Rankings section hidden for non-logged-in

---

## RANKINGS
- [x] Renamed "Ladder" → "Rankings"
- [x] Title: "League Rankings" (was "The Ladder")
- [x] No "Monthly Rankings" header
- [x] No ratings column
- [x] No trend column
- [x] Player thumbnails (photos or tennis ball)
- [x] Thumbnails clickable to profile (when logged in)

---

## PROFILE PAGES (profile.html)
- [x] Photo (or tennis ball default)
- [x] Name display
- [x] Membership tier badge
- [x] Availability slots display
- [x] Favorite players display

---

## JOIN PAGE (join.html)
- [x] Name field (required)
- [x] Email field (required)
- [x] Phone field (required)
- [x] Tier selection: Player $35 / Social Butterfly $45
- [x] Availability multi-select (6 slots)
- [x] Availability greyed out if Social Butterfly selected
- [x] Favorite players field
- [x] Contact footer: Ash and Natalie links

---

## DASHBOARD - PLAYER TIER
- [x] Sit Out button at TOP of page
- [x] Sit out explanatory text
- [x] Section title: "My Info" (was "Preferences")
- [x] Name field (editable, cannot be blank)
- [ ] Email field (editable, cannot be blank) - ISSUE: Currently read-only
- [x] Phone field (cannot be blank)
- [x] 6-slot availability checkboxes
- [x] Favorite players field
- [x] Button: "Save My Info" (was "Save preferences")
- [x] Save button turns white when changes pending
- [x] Stats row (Games Won, Matches, Ranking)
- [x] This Month's Match section
- [x] Match History section

---

## DASHBOARD - SOCIAL BUTTERFLY TIER
- [ ] No match status/stats/matches sections - FIXED in HTML
- [ ] My Info section with Name, Email, Phone - FIXED in HTML
- [ ] "I want to start playing!" button - FIXED in HTML
- [ ] Explanatory text under button - FIXED in HTML
- [ ] Availability greyed out until upgrade clicked - FIXED in HTML
- [ ] When upgrade clicked: availability becomes required - NEEDS JS
- [ ] Favorite players field - FIXED in HTML
- [ ] Save My Info button - FIXED in HTML

---

## LOGIN PAGE (login.html)
- [x] No "Player Login" heading
- [x] "Not in the league yet? Join us" with link
- [x] Supabase explanation text
- [x] "Back to Net Worth" link (was "Back to ladder")

---

## HOW IT WORKS (section in index.html)
- [x] No "The System" heading
- [x] Block 1: Get Paired - correct text
- [x] Block 2: Play Your Match - correct text
- [x] Block 3: Log Your Score - correct text
- [x] Extra text about playing more matches
- [x] "Need to Take a Month Off?" special block

---

## COURTS (section in index.html)
- [x] No "Home Turf" heading
- [x] Title: "Recommended Courts" (was "Approved Courts")
- [x] "Feel free to work out other options" text

---

## RULES → GAME PLAY & SCORING (rules.html)
- [x] Page renamed to "Game Play and Scoring"
- [x] Match Format section
- [x] How Sets End section
- [x] Maximum Possible Score section
- [x] Reporting Your Score section
- [x] Forfeits & Special Situations section

---

## FOOTER (all pages)
- [x] "Game Play & Scoring" link (was "Rules")
- [x] "Contact Us" mailto both Ash and Natalie

---

## EMAIL TEMPLATES
- [x] Matching email: "Go ahead... make the first move 😉"
- [x] Subject: "You're matched for {{Month}} 🎾"
- [ ] Supabase magic link email customized - USER DID THIS MANUALLY

---

## BACKEND - RMS MATCHING
- [x] RMS calculation (avg games won, last 3 matches)
- [x] Performance bands: developing/competitive/strong/dominant
- [x] Match within bands
- [x] Anti-staleness (avoid same matchup within 3 months)
- [x] Admin flex (remove Natalie/Ashley if odd count)
- [x] Social Butterflies excluded from matching

---

## BACKEND - BUSINESS LOGIC
- [x] Sit-out button behavior (indefinite pause)
- [x] Sit-out confirmation email
- [x] Rejoin confirmation email
- [x] Social Butterfly → Player upgrade
- [x] Availability required for players
- [x] Profile API handles name updates
- [x] Profile API handles favorite_players

---

## ADMIN
- [x] Natalie (nmcoffen@gmail.com) as admin - USER CONFIRMED

---

## KNOWN LIMITATIONS
- Email editing disabled (would require Supabase auth email change)
- Courts nav uses anchor instead of separate page (no courts.html exists)

---

## STILL NEEDS WORK
1. Social Butterfly dashboard JS (populate form, save, upgrade flow)
2. Test Social Butterfly view end-to-end
