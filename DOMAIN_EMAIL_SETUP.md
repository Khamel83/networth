# DOMAIN + EMAIL SETUP - TECHNICAL GUIDE

## For You (Tech Setup Person)

### Domain Configuration (networthtennis.club)

**Email Forwarding Setup:**
1. Go to domain registrar (GoDaddy, Squarespace, etc.)
2. Find "Email Forwarding" or "Email Routing"
3. Set up: `matches@networthtennis.club` → `ashleybrooke.kaufman@gmail.com`

**DNS Records (if needed):**
```
Type: MX
Value: aspmx.l.google.com
Priority: 1

Type: TXT
Value: "v=spf1 include:_spf.google.com ~all"
```

### Gmail App Password Generation

**For Ashley (show her on your phone):**
1. Open browser → "Gmail App Password"
2. Sign in to Google Account
3. Select app: "Mail" → "Other device"
4. Copy 16-character password: `abcd efgh ijkl mnop`
5. Send this password to yourself for setup

### System Configuration

**In the .env file:**
```bash
GMAIL_EMAIL=matches@networthtennis.club
GMAIL_PASSWORD=abcd-efgh-ijkl-mnop  # Her app password
```

**Email Headers (in pretty_emails.py):**
- From: `matches@networthtennis.club`
- Reply-to: `matches@networthtennis.club`
- Players see professional domain, replies go to Ashley's Gmail

### Confirmation Pages (networthtennis.club)

**Two simple HTML pages:**

**Page 1: /confirm/{match_id}/yes/{player_id}**
```html
<!DOCTYPE html>
<html>
<head><title>Match Confirmed! 🎾</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
<h1>✅ TENNIS MATCH CONFIRMED!</h1>
<p>Your match is ON! You'll receive contact info shortly.</p>
<p>Game on! 🎾</p>
</body>
</html>
```

**Page 2: /confirm/{match_id}/no/{player_id}**
```html
<!DOCTYPE html>
<html>
<head><title>No Problem! 🎾</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
<h1>🌟 NO PROBLEM!</h1>
<p>We'll find you another match soon.</p>
<p>Your perfect tennis partner is out there! 🎾</p>
</body>
</html>
```

### Deployment (GitHub Pages - Free)

1. Create `docs` folder in GitHub repo
2. Put HTML files in `docs` folder
3. In GitHub Settings → Pages:
   - Source: Deploy from a branch
   - Branch: main/docs
4. Site publishes automatically at: `https://Khamel83.github.io/networth`
5. Custom domain: Point `networthtennis.club` to GitHub Pages

---

## RESULT:
- Professional tennis matching service
- `matches@networthtennis.club` sends beautiful emails
- `networthtennis.club/confirm/...` handles confirmations
- Ashley manages everything from her regular Gmail
- Zero technical knowledge required from Ashley

**Total setup time:** 30 minutes
**Ongoing maintenance:** Zero