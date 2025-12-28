# TODO - NET WORTH Tennis

Project task tracking following [todo.md](https://github.com/todomd/todo.md) spec.

---

## Backlog

_No pending tasks_

---

## In Progress

_No tasks in progress_

---

## Done

### Ashley's UI/UX Feedback (December 2024)

All 5 feature requests implemented and deployed:

- [x] **Join page:** Changed "Favorite Players" to "Favorite Pro Players" with updated placeholder
- [x] **Rules page:** Added forfeit rescheduling copy ("no forfeit points if rescheduled")
- [x] **Dashboard:** Added "Record Your Score" section with 12-month grid
- [x] **Profiles page:** New `/profiles` player directory with card grid layout
- [x] **Sit Out button:** Green when active, red when paused

### Additional Improvements

- [x] Added "Players" nav link to header and footer across all pages
- [x] Added `/profiles` route to vercel.json
- [x] Updated profile.html to display email and phone for logged-in members
- [x] Fixed profile links to only be clickable when player.id exists (prevents broken links)

---

## Completed Releases

### v1.1.0 - Ashley's Feedback (Dec 28, 2025)

**Commits:**
- `31e582c` - Implement Ashley's UI/UX feedback (5 items)
- `20acaf3` - Add /profiles route to vercel.json
- `98a1c88` - Fix: Add Players link to footer, prevent broken profile links

**Files Changed:**
- `public/join.html` - Favorite Pro Players field
- `public/rules.html` - Forfeit rescheduling copy
- `public/dashboard.html` - Record Your Score section, Sit Out styling
- `public/profiles.html` - NEW player directory page
- `public/profile.html` - Email/phone display for members
- `public/index.html` - Players footer link, profile link fix
- `vercel.json` - /profiles route

---
*Last updated: Dec 28, 2025*
