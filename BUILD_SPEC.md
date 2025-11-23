# 🎾 NET WORTH Full Platform - Build Specification

## Why We Haven't Built This Yet

**Current state:**
- ✅ Backend API exists (login, get ladder, report score)
- ✅ Static HTML ladder page
- ❌ NO web forms for login
- ❌ NO player dashboard
- ❌ NO admin panel
- ❌ NO score reporting UI

**We built the API but not the UI.**

---

## OPTION B: Full Self-Service Platform

Players can:
- ✅ Log in via web browser
- ✅ View personal dashboard
- ✅ Report match scores
- ✅ View match history
- ✅ See personal stats
- ✅ Challenge other players

Admins can:
- ✅ Add/remove players
- ✅ Approve/reject scores
- ✅ Manage all data
- ✅ Export reports

---

## BUILD PHASES

### PHASE 1: Core Player Features (4-6 hours)
**Goal:** Players can log in and report scores

### PHASE 2: Admin Panel (3-4 hours)
**Goal:** You can manage everything via web interface

### PHASE 3: PostgreSQL Migration (1-2 hours)
**Goal:** Reliable, production-ready database

### PHASE 4: Polish & Launch (2-3 hours)
**Goal:** Ready for 40 players

**TOTAL: 10-15 hours of development**

---

## DETAILED TASK BREAKDOWN

---

## PHASE 1: CORE PLAYER FEATURES

### Task 1.1: Session Management System
**Time:** 1 hour

**What:**
- Implement Flask session management
- Set secure session cookies
- Handle login state across pages
- Auto-logout after inactivity

**Files to create/modify:**
- `production_server.py` - Add session config
- Add `secret_key` to environment variables

**Deliverable:**
- Players stay logged in across page refreshes
- Secure cookie-based sessions

---

### Task 1.2: Login Page (Web UI)
**Time:** 1 hour

**What:**
- Create login form (email + password)
- Style matching the ladder design
- Error messages for wrong credentials
- Redirect to dashboard on success

**Files to create:**
- `login.html` - Login form page
- Update `production_server.py` - Add `/login` route

**Design:**
```
┌─────────────────────────────────┐
│   NET WORTH Tennis Ladder       │
│                                 │
│   ┌───────────────────────┐    │
│   │ Email:                │    │
│   │ [________________]    │    │
│   │                       │    │
│   │ Password:             │    │
│   │ [________________]    │    │
│   │                       │    │
│   │    [  Login  ]        │    │
│   └───────────────────────┘    │
│                                 │
│   ← Back to Ladder              │
└─────────────────────────────────┘
```

**Deliverable:**
- Working login form at `/login`
- Sets session cookie on success
- Shows error if credentials wrong

---

### Task 1.3: Player Dashboard
**Time:** 2 hours

**What:**
- Personal dashboard showing:
  - Player name, rank, record
  - Recent matches
  - Upcoming challenges
  - Quick stats

**Files to create:**
- `dashboard.html` - Player dashboard page
- Update `production_server.py` - Add `/dashboard` route

**Design:**
```
┌────────────────────────────────────────────────┐
│ NET WORTH Tennis          Ashley Collins  Logout│
├────────────────────────────────────────────────┤
│                                                │
│  Your Stats                                    │
│  ┌──────────────────────────────────────────┐ │
│  │ Rank: #1 / 40     Record: 12-3          │ │
│  │ Skill Level: 4.0  Win Rate: 80%         │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Recent Matches                                │
│  ┌──────────────────────────────────────────┐ │
│  │ Nov 15  vs Jennifer Martinez    W 6-4,6-2│ │
│  │ Nov 10  vs Alyssa Perry        L 4-6,6-7│ │
│  │ Nov 5   vs Carolina Ciappa     W 6-3,6-1│ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Actions                                       │
│  [Report Score]  [View Full History]          │
│                                                │
└────────────────────────────────────────────────┘
```

**Deliverable:**
- Dashboard page at `/dashboard`
- Requires login (redirect to `/login` if not logged in)
- Shows personalized player data

---

### Task 1.4: Report Score Form
**Time:** 1.5 hours

**What:**
- Form to report match results
- Select opponent from dropdown
- Enter set scores
- Submit for confirmation

**Files to create:**
- `report_score.html` - Score reporting form
- Update `production_server.py` - Modify `/api/report-score` endpoint

**Design:**
```
┌─────────────────────────────────────┐
│ Report Match Score                  │
├─────────────────────────────────────┤
│                                     │
│ Opponent:                           │
│ [▼ Select player... ____________]  │
│                                     │
│ Match Date:                         │
│ [2025-11-23___]                    │
│                                     │
│ Set 1:                              │
│ You: [6] Opponent: [4]             │
│                                     │
│ Set 2:                              │
│ You: [6] Opponent: [2]             │
│                                     │
│ Set 3 (if played):                  │
│ You: [_] Opponent: [_]             │
│                                     │
│ Notes (optional):                   │
│ [________________________]          │
│                                     │
│ [Cancel]  [Submit Score]            │
│                                     │
└─────────────────────────────────────┘
```

**Deliverable:**
- Score reporting form at `/report-score`
- Dropdown populated with all players
- Saves to database with status "pending"
- Shows confirmation message

---

### Task 1.5: Match History Page
**Time:** 1 hour

**What:**
- View all past matches
- Filter by date, opponent
- Show confirmed vs pending scores

**Files to create:**
- `history.html` - Match history page
- Update `production_server.py` - Add `/history` route

**Design:**
```
┌─────────────────────────────────────────────────┐
│ Match History                                   │
├─────────────────────────────────────────────────┤
│                                                 │
│ Date       Opponent           Result    Status │
│ ───────────────────────────────────────────────│
│ Nov 15    Jennifer Martinez   W 6-4,6-2 ✓ Conf │
│ Nov 10    Alyssa Perry        L 4-6,6-7 ✓ Conf │
│ Nov 5     Carolina Ciappa     W 6-3,6-1 ✓ Conf │
│ Nov 1     [redacted-name]       W 6-2,6-4 ⏳ Pend│
│                                                 │
└─────────────────────────────────────────────────┘
```

**Deliverable:**
- Match history at `/history`
- Shows all matches for logged-in player
- Indicates pending vs confirmed

---

## PHASE 2: ADMIN PANEL

### Task 2.1: Admin Authentication
**Time:** 30 minutes

**What:**
- Admin login (separate from player login)
- Admin role in database
- Protected admin routes

**Files to modify:**
- `production_server.py` - Add admin check decorator
- Add admin user to database

**Deliverable:**
- Admin can log in at `/admin/login`
- Admin role enforced on admin routes

---

### Task 2.2: Admin Dashboard
**Time:** 1.5 hours

**What:**
- Overview of system
- Total players, pending scores, recent activity
- Quick actions

**Files to create:**
- `admin_dashboard.html` - Admin dashboard
- Update `production_server.py` - Add `/admin` route

**Design:**
```
┌───────────────────────────────────────────────┐
│ NET WORTH Admin Panel                  Logout │
├───────────────────────────────────────────────┤
│                                               │
│ System Overview                               │
│ ┌─────────────────────────────────────────┐  │
│ │ Total Players: 40                       │  │
│ │ Active Players: 38                      │  │
│ │ Pending Scores: 3                       │  │
│ │ Matches This Month: 67                  │  │
│ └─────────────────────────────────────────┘  │
│                                               │
│ Quick Actions                                 │
│ [Add Player] [Review Scores] [Export Data]   │
│                                               │
│ Recent Activity                               │
│ ┌─────────────────────────────────────────┐  │
│ │ Ashley reported score vs Jennifer       │  │
│ │ New player: Sarah Johnson joined        │  │
│ │ Score confirmed: Alyssa vs Carolina     │  │
│ └─────────────────────────────────────────┘  │
│                                               │
└───────────────────────────────────────────────┘
```

**Deliverable:**
- Admin dashboard at `/admin`
- System stats displayed
- Quick action buttons

---

### Task 2.3: Add Player Form
**Time:** 1 hour

**What:**
- Form to add new players
- Validate email uniqueness
- Set initial skill level
- Auto-generate player ID

**Files to create:**
- `admin_add_player.html` - Add player form
- Update `production_server.py` - Add `/admin/players/add` route

**Design:**
```
┌─────────────────────────────────────┐
│ Add New Player                      │
├─────────────────────────────────────┤
│                                     │
│ Name:                               │
│ [____________________________]      │
│                                     │
│ Email:                              │
│ [____________________________]      │
│                                     │
│ Skill Level (NTRP):                 │
│ [▼ 3.0 ____]                       │
│                                     │
│ Initial Ranking:                    │
│ ○ Bottom of ladder                  │
│ ○ Middle of ladder                  │
│ ○ Custom position: [___]            │
│                                     │
│ [Cancel]  [Add Player]              │
│                                     │
└─────────────────────────────────────┘
```

**Deliverable:**
- Add player form at `/admin/players/add`
- Validates email
- Creates player in database
- Sends welcome email (future)

---

### Task 2.4: Manage Players Page
**Time:** 1 hour

**What:**
- List all players
- Edit/deactivate players
- View player details
- Search/filter

**Files to create:**
- `admin_players.html` - Player management page
- Update `production_server.py` - Add `/admin/players` route

**Design:**
```
┌────────────────────────────────────────────────┐
│ Manage Players                    [+ Add New]  │
├────────────────────────────────────────────────┤
│                                                │
│ Search: [____________] [Active ▼] [Search]    │
│                                                │
│ Name              Email              Actions   │
│ ─────────────────────────────────────────────│
│ Ashley Collins    ashley@...    [Edit] [View] │
│ Jennifer Martinez jennifer@...  [Edit] [View] │
│ Alyssa Perry      alyssa@...    [Edit] [View] │
│ ...                                            │
│                                                │
│ Showing 1-20 of 40      [← 1 2 3 →]           │
│                                                │
└────────────────────────────────────────────────┘
```

**Deliverable:**
- Player list at `/admin/players`
- Search/filter functionality
- Edit/deactivate actions

---

### Task 2.5: Review Pending Scores
**Time:** 1.5 hours

**What:**
- View all pending score reports
- Approve or reject
- See both players' perspectives if both reported
- Handle disputes

**Files to create:**
- `admin_scores.html` - Score review page
- Update `production_server.py` - Add `/admin/scores` route

**Design:**
```
┌──────────────────────────────────────────────┐
│ Review Pending Scores                        │
├──────────────────────────────────────────────┤
│                                              │
│ Match Report #1                              │
│ ┌──────────────────────────────────────────┐│
│ │ Reported by: Ashley Collins              ││
│ │ Date: Nov 20, 2025                       ││
│ │ Opponent: Jennifer Martinez              ││
│ │ Score: 6-4, 6-2 (Ashley won)             ││
│ │ Status: Pending opponent confirmation    ││
│ │                                          ││
│ │ [Approve] [Reject] [Contact Players]    ││
│ └──────────────────────────────────────────┘│
│                                              │
│ Match Report #2                              │
│ ┌──────────────────────────────────────────┐│
│ │ ⚠️ DISPUTE                               ││
│ │ Player 1: Alyssa (won 6-3, 6-4)          ││
│ │ Player 2: Carolina (won 6-4, 6-3)        ││
│ │                                          ││
│ │ [Approve P1] [Approve P2] [Manual Edit] ││
│ └──────────────────────────────────────────┘│
│                                              │
└──────────────────────────────────────────────┘
```

**Deliverable:**
- Score review at `/admin/scores`
- Approve/reject functionality
- Dispute resolution UI
- Updates ladder rankings on approval

---

## PHASE 3: POSTGRESQL MIGRATION

### Task 3.1: Set Up PostgreSQL on Railway
**Time:** 20 minutes

**What:**
- Add PostgreSQL database in Railway dashboard
- Get connection string
- Add to environment variables

**Steps:**
1. Railway dashboard → Add Database → PostgreSQL
2. Copy DATABASE_URL
3. Add to environment variables

**Deliverable:**
- PostgreSQL instance running on Railway
- Connection URL in env vars

---

### Task 3.2: Convert Schema
**Time:** 30 minutes

**What:**
- Create PostgreSQL schema matching SQLite
- Add proper indexes
- Set up foreign keys

**Files to create:**
- `schema.sql` - PostgreSQL schema definition
- `migrate.py` - Migration script

**Deliverable:**
- PostgreSQL tables created
- Indexes configured
- Ready for data import

---

### Task 3.3: Migrate Data
**Time:** 30 minutes

**What:**
- Export data from SQLite
- Import into PostgreSQL
- Verify data integrity

**Files to create:**
- `data_migration.py` - Data migration script

**Deliverable:**
- All 40 players migrated
- All match history preserved
- No data loss

---

### Task 3.4: Update Application Code
**Time:** 30 minutes

**What:**
- Replace sqlite3 with psycopg2
- Update all database queries
- Test all endpoints

**Files to modify:**
- `production_server.py` - Replace db connection logic
- `requirements_backend.txt` - Add psycopg2

**Deliverable:**
- App works with PostgreSQL
- All features functional
- Better concurrent write handling

---

## PHASE 4: POLISH & LAUNCH

### Task 4.1: Navigation & UX
**Time:** 1 hour

**What:**
- Consistent header/nav across all pages
- Breadcrumbs
- Mobile responsive design
- Smooth transitions

**Files to modify:**
- All HTML files - Add consistent header
- Add shared CSS file

**Deliverable:**
- Professional, cohesive UI
- Mobile-friendly
- Easy navigation

---

### Task 4.2: Error Handling & Validation
**Time:** 1 hour

**What:**
- Client-side form validation
- Server-side validation
- Friendly error messages
- Loading states

**Files to modify:**
- All forms - Add validation
- All routes - Add error handling

**Deliverable:**
- Prevents bad data entry
- Clear error messages
- Good UX

---

### Task 4.3: Security Hardening
**Time:** 1 hour

**What:**
- CSRF protection
- SQL injection prevention (parameterized queries)
- Rate limiting
- Secure session cookies

**Files to modify:**
- `production_server.py` - Add security middleware

**Deliverable:**
- Production-ready security
- Protected against common attacks

---

### Task 4.4: Testing & QA
**Time:** 1 hour

**What:**
- Test all user flows
- Test admin functions
- Test edge cases
- Fix bugs

**Deliverable:**
- All features work
- No critical bugs
- Ready for users

---

## SUMMARY BY FILE

### New Files to Create:
1. `login.html` - Player login page
2. `dashboard.html` - Player dashboard
3. `report_score.html` - Score reporting form
4. `history.html` - Match history
5. `admin_dashboard.html` - Admin overview
6. `admin_add_player.html` - Add player form
7. `admin_players.html` - Manage players
8. `admin_scores.html` - Review scores
9. `schema.sql` - PostgreSQL schema
10. `migrate.py` - Migration script
11. `data_migration.py` - Data migrator
12. `static/style.css` - Shared styles

### Files to Modify:
1. `production_server.py` - Add all routes, session management
2. `requirements_backend.txt` - Add dependencies
3. `index.html` - Add "Login" button

### Database Changes:
1. Add `admin` boolean to players table
2. Add `session_tokens` table (or use Flask sessions)
3. Migrate to PostgreSQL

---

## DEVELOPMENT TIMELINE

### Week 1 (10-15 hours):
- **Day 1-2:** Phase 1 (Core Player Features) - 6 hours
- **Day 3:** Phase 2 (Admin Panel) - 4 hours
- **Day 4:** Phase 3 (PostgreSQL) - 2 hours
- **Day 5:** Phase 4 (Polish) - 3 hours

### Alternative: Staged Release

**MVP (Minimum Viable Product):**
- Tasks 1.1, 1.2, 1.3, 1.4 only (4 hours)
- Players can log in and report scores
- You review in database manually

**V2 (Admin Panel):**
- Add Phase 2 later (4 hours)

**V3 (Production Ready):**
- Add Phases 3 & 4 (4 hours)

---

## NEXT STEPS - IMMEDIATE ACTIONS

### Step 1: Approve This Plan
- Review the spec above
- Confirm features needed
- Prioritize phases

### Step 2: I Build MVP (4-6 hours)
- Phase 1: Core player features
- Get players using the system
- Iterate based on feedback

### Step 3: Add Admin Panel (3-4 hours)
- Phase 2: Admin features
- You can manage everything

### Step 4: Production Hardening (3-4 hours)
- Phase 3: PostgreSQL
- Phase 4: Polish

### Step 5: Launch
- Deploy to Railway
- Point networthtennis.com
- Invite players

---

## QUESTIONS TO ANSWER

1. **Should I start building immediately?**
   - I can build Phase 1 (MVP) right now

2. **Do you want all phases or staged release?**
   - MVP first (4 hours), then iterate?
   - Or full build (15 hours)?

3. **Any feature changes needed?**
   - Anything to add/remove from spec?

4. **Timeline constraints?**
   - When do you need this live?

---

## READY TO BUILD

Say the word and I'll start with:

**Phase 1, Task 1.1: Session Management**

Then move through each task systematically until we have a fully working platform.

**Estimated completion: 10-15 hours of focused development**

Let's build this! 🎾
