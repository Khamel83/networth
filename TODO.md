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

### Gmail Email System (January 2025)

Complete email automation rewrite:

- [x] Removed Resend integration (user request)
- [x] Implemented Gmail SMTP via Ashley's account (`ashleybrooke.kaufman@gmail.com`)
- [x] Created 5 email templates in `api/email.py`:
  - Welcome email (on signup)
  - Match assignment (on pairing)
  - Availability check (27th of month)
  - Final reminder (last day of month)
  - Mid-month reminder (15th of month)
- [x] Updated `api/join.py` to send welcome emails
- [x] Updated `api/pairings.py` to send match assignment emails
- [x] Updated GitHub Actions schedule for automated emails
- [x] Fixed join flow: changed from delete+insert to UPDATE for re-registrations (RLS blocks deletes)

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
- [x] Admin approval gate for new player signups

---

## Known Limitations

- **No DELETE on players table:** RLS has no delete policy. All code uses UPDATE to deactivate instead.
- **Gmail SMTP on Vercel:** Untested until SMTP_PASSWORD is configured.

---

## Environment Setup Required

To enable email sending, add to Vercel environment variables:
```
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  (Gmail app password from Ashley's account)
```

---

*Last updated: Jan 8, 2026*
