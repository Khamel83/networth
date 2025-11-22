# ASHLEY'S MORNING SETUP - 5 MINUTES MAX

## What You Need From Ashley (3 questions):

### 1. Domain Status
"Do you already own networthtennis.club or should I buy it?"

**If YES (she owns it):**
- "What's your domain registrar (GoDaddy, Squarespace, etc.)?"
- "Can you set up email forwarding: matches@networthtennis.club → ashleybrooke.kaufman@gmail.com?"

**If NO (needs to buy):**
- "I'll buy networthtennis.club for $20/year"
- "I'll set up the email forwarding for you"

### 2. Gmail App Password
"Can you generate a Gmail App Password? (2 minutes)"

**Steps (show her on your phone):**
1. Open Google: "App Password Gmail"
2. Sign into your Google Account
3. Select "Mail" → "Other device"
4. Copy the 16-character password
5. Send it to me

### 3. Player List
"Can you send your tennis players in any format? Even a text or email thread works."

**Accept anything:**
- Excel file, CSV, Google Sheets link
- Email with names/emails/phones
- Text message list
- Screenshot of contacts

---

## MY SETUP (After you get answers):

### Command 1: Clone & Setup (2 minutes)
```bash
git clone https://github.com/Khamel83/networth
cd networth
echo "GMAIL_EMAIL=matches@networthtennis.club" > .env
echo "GMAIL_PASSWORD=her-app-password-here" >> .env
```

### Command 2: Import Players (1 minute)
```bash
python3 simple_final.py --ashley-import whatever-she-sent-you.csv
```

### Command 3: Run Matching (30 seconds)
```bash
python3 simple_final.py --run-matching
```

### Command 4: Schedule Daily (1 minute)
```bash
# Run this once, it runs forever every morning
echo "0 2 * * * cd $(pwd) && python3 simple_final.py --run-matching" | crontab -
```

---

## RESULT:
- ✅ Professional tennis matching service running
- ✅ Daily matches at 2 AM automatically
- ✅ Beautiful emails from matches@networthtennis.club
- ✅ All player replies go to her regular Gmail
- ✅ Zero maintenance - runs forever

**Total time for Ashley:** 5 minutes to answer questions
**Total setup time for you:** 5 minutes to run commands

**That's it!** Tennis matches start flowing tomorrow morning. 🎾