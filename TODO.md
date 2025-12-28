# TODO - Ashley's Feedback Implementation Plan

Project task tracking following [todo.md](https://github.com/todomd/todo.md) spec.

## Feature Plan: Ashley's UI/UX Feedback (December 2024)

### Overview
Implementing 5 feature requests from Ashley to improve the NET WORTH Tennis site UX.

---

## 1. Join Now Flow - Favorite Pro Players

**Files:** `public/join.html`
**Complexity:** Simple (copy change only)

### Tasks
- [ ] Change label from "Favorite Players" to "Favorite Pro Players"
- [ ] Update placeholder text from "Any players you especially enjoy playing with?" to "Which pros are you following this season?"

### Changes Required
```
Line 531-533 in join.html:
- Label: "Favorite Players (optional)" → "Favorite Pro Players (optional)"
- Placeholder: Change to match description
```

---

## 2. Game Play & Scoring - Forfeit Copy Update

**Files:** `public/rules.html`
**Complexity:** Simple (copy change only)

### Tasks
- [ ] Update forfeit section to add "If a match is successfully rescheduled, no forfeit points should be applied."

### Changes Required
```
Line 367 in rules.html - Add additional bullet point after "If feasible, rescheduling is encouraged..."
```

---

## 3. My Info Page - Match Score Recording

**Files:** `public/dashboard.html`
**Complexity:** Medium (new UI section + logic)

### Tasks
- [ ] Add new "Record Your Score" section with month boxes
- [ ] Create 12 month input boxes (January-December)
- [ ] Add numeric-only validation
- [ ] Wire up to existing score submission API

### Implementation Notes
- This needs to complement the existing "Report Score" modal
- Could show completed months vs pending months
- Consider showing scores for completed months (read-only) with input for current month
- Use existing `/api/matches` endpoint

### UI Design
```
Section Title: "Record Your Score"
Description: "Record your scores in the boxes below."

Grid of month boxes:
[Jan] [Feb] [Mar] [Apr]
[May] [Jun] [Jul] [Aug]
[Sep] [Oct] [Nov] [Dec]
```

---

## 4. NEW: Profiles Page (All Players Directory)

**Files:** NEW `public/profiles.html`, possibly `api/players.py` updates
**Complexity:** Complex (new page + API integration)

### Tasks
- [ ] Create new `profiles.html` page
- [ ] Build player grid UI with cards
- [ ] Display name + photo (tennis ball placeholder)
- [ ] Link each card to individual `profile.html?id=xxx`
- [ ] Add navigation link to profiles page in header/footer

### Implementation Notes
- Reuse existing `/api/players` endpoint
- Profile cards need: avatar (or tennis ball emoji), name, maybe tier badge
- Click-through goes to existing `profile.html` which already shows:
  - Name, Email, Phone (needs verification), Membership type, Availability, Favorite pro players

### UI Design
```
Page Title: "Meet the Players"
Grid layout (responsive):
- 3-4 columns on desktop
- 2 columns on tablet
- 1 column on mobile

Each card:
┌─────────────────┐
│     [Avatar]    │
│   Player Name   │
│   Player Badge  │
└─────────────────┘
```

### Existing profile.html Check
Current profile.html already displays:
- Name
- Avatar or tennis ball placeholder
- Membership tier (Player/Social Butterfly)
- Stats (Rank, Games Won, Matches)
- Availability grid
- Favorite players

**Missing from current profile.html:**
- Email (need to add)
- Phone number (need to add)

---

## 5. Sit Out Button - Visual State Fix

**Files:** `public/dashboard.html`
**Complexity:** Simple (CSS/styling fix)

### Tasks
- [ ] Verify button changes color from active (greenish/default) to inactive (red/disabled) when clicked
- [ ] Test the `updatePauseUI()` function behavior

### Current Implementation (Lines 1551-1566)
```javascript
function updatePauseUI(isPaused) {
    if (isPaused) {
        badge.textContent = 'Sitting Out';
        badge.className = 'status-badge paused';  // yellow/warning color
        btn.textContent = "I'm Back!";
        btn.className = 'btn-status-toggle btn-rejoin';
    } else {
        badge.textContent = 'Active';
        badge.className = 'status-badge active';  // green color
        btn.textContent = 'Sit Out This Month';
        btn.className = 'btn-status-toggle btn-sit-out';
    }
}
```

### Issue Analysis
The current implementation changes to yellow (warning) when paused, not red. Ashley wants:
- **Active state:** Green (current: green via `--success-green`)
- **Paused state:** Red/disabled (current: yellow via `--warning-yellow`)

### Fix Required
Change `.status-badge.paused` and `.btn-sit-out` colors:
- `.status-badge.paused` should use `--error-red` instead of `--warning-yellow`
- Button should also toggle to red when in "sitting out" state

---

## Dependencies

```
1. Join Flow (no deps)
2. Scoring Copy (no deps)
3. Score Recording (needs API review)
4. Profiles Page (needs profile.html updates)
   └── Update profile.html to show email/phone
5. Sit Out Button (no deps)
```

## Recommended Implementation Order

1. **Simple copy changes first:** #1, #2, #5 (quick wins)
2. **Profile page + profile.html updates:** #4 (bigger feature)
3. **Score recording:** #3 (needs UX decision)

---

### Backlog

### In Progress

### Done
- [x] 1. Update Join page "Favorite Players" to "Favorite Pro Players"
- [x] 2. Update forfeit copy on Game Play & Scoring page
- [x] 3. Add score recording section to My Info page
- [x] 4. Build Profiles page with player directory
- [x] 4a. Update profile.html to show email and phone
- [x] 5. Fix Sit Out button to use red/disabled styling when paused
- [x] Add "Players" nav link to all pages
- [x] Add /profiles route to vercel.json

---
*Updated by OneShot skills. Say `(ONE_SHOT)` to re-anchor.*
