# NET WORTH Tennis Ladder - Complete Deployment Instructions

## 🎯 Current Status
✅ **Data**: Ashley's 40 players imported (30 active, 10 inactive)
✅ **Code**: Safe version ready (no emails/texts sent)
✅ **Domain**: networthtennis.com purchased
🚧 **Next Steps**: Domain setup + Gmail config

## 📋 What You Have Now

### Working System Features
- ✅ **30 Active Players**: Ashley's current ladder members
- ✅ **Ranking System**: Based on total games won (their current system)
- ✅ **Monthly Pairings**: Automatically matches top vs bottom for competitive balance
- ✅ **LA East Side Focus**: Uses Ashley's recommended courts
- ✅ **Safe Mode**: Shows what would be emailed without actually sending

### Current Ladder Top 10
1. Kim Ndombe (51 pts)
2. Natalie Coffen (50 pts)
3. Sara Chrisman (49 pts)
4. Arianna Hairston (48 pts)
5. Alik Apelian (45 pts)
6. Hannah Shin (45 pts)
7. Hanna Pavlova (41 pts)
8. Maddy Whitby (38 pts)
9. Allison Dunne (37 pts)
10. Ashley Brooke Kaufman (33 pts)

## 🚀 Deployment Steps

### Step 1: Domain Configuration (10 minutes)

**You own networthtennis.com - point it to your server:**

```bash
# Get your server IP
curl ifconfig.me

# Go to your domain registrar (where you bought networthtennis.com)
# Set DNS A record:
@ (root) -> YOUR_SERVER_IP
www -> YOUR_SERVER_IP
```

### Step 2: Gmail App Password (5 minutes)

**Ashley needs to create this for sending emails:**

1. **Go to**: https://myaccount.google.com/apppasswords
2. **Select**: "Mail" → "Other device"
3. **Generate**: 16-character password
4. **Save**: This is your `GMAIL_PASSWORD`

**Environment variables:**
```bash
# Create .env file
echo "GMAIL_EMAIL=matches@networthtennis.com" > .env
echo "GMAIL_PASSWORD=paste-16-char-app-password-here" >> .env
```

### Step 3: Deploy Code (2 minutes)

```bash
# Clone the repository
git clone https://github.com/Khamel83/networth.git
cd networth

# Test the system (safe mode)
python3 networth_safe.py --setup
python3 networth_safe.py --ladder
python3 networth_safe.py --pairings
```

### Step 4: Web Server Setup (5 minutes)

**Option A: Simple Python server (for testing)**
```bash
# Install flask for web interface
pip install flask

# Run simple web server
python3 -m http.server 8000
# Access at http://your-server-ip:8000
```

**Option B: Production web server**
```bash
# Install nginx
sudo apt update
sudo apt install nginx

# Configure nginx for networthtennis.com
sudo nano /etc/nginx/sites-available/networthtennis.com
```

### Step 5: Configure Email (5 minutes)

```bash
# Test email system (preview mode only)
python3 networth_safe.py --preview-emails

# When ready to send real emails, switch to:
python3 simple_final.py --send-monthly-pairings
```

## 📧 How Email System Works

### What Gets Sent Monthly
1. **Match Pairings**: "You're matched with Sarah, contact: 555-1234"
2. **Bye Notifications**: "You have a bye this month"
3. **Ladder Updates**: Current rankings and standings

### Email Preview Example
```
TO: Natalie Coffen <nmcoffen@gmail.com>
SUBJECT: 🎾 NET WORTH November Match: Isa Quiros

Your NET WORTH November tennis ladder match has been scheduled!

OPPONENT: Isa Quiros
CONTACT: Isabella.quiros@gmail.com | 954-805-7657
SKILL LEVEL: 2.5-3.0 (Beginner-Intermediate)
SUGGESTED COURT: Hermon Park
SUGGESTED DATE: Around November 15, 2025

WHAT TO DO:
• Contact Isa directly to schedule
• Play 2-set format (total games won count toward ranking)
• Split court costs and bring fresh balls
• Report your score after the match

Current ladder rankings: https://networthtennis.com

Game on! 🎾
```

## 🎾 Monthly Workflow

### Automatic Monthly Process
```bash
# This runs automatically each month:
1. Generate pairings (top vs bottom players)
2. Send match notifications via email
3. Update ladder rankings
4. Handle odd players (bye system)
```

### Manual Commands (Ashley can use)
```bash
# View current ladder
python3 networth_safe.py --ladder

# See this month's pairings
python3 networth_safe.py --pairings

# Preview emails without sending
python3 networth_safe.py --preview-emails

# Send real monthly pairings
python3 simple_final.py --send-monthly-pairings
```

## 🔧 System Configuration Files

### .env file (create this)
```bash
GMAIL_EMAIL=matches@networthtennis.com
GMAIL_PASSWORD=your-16-character-app-password
```

### Monthly automation (cron job)
```bash
# Edit crontab
crontab -e

# Add monthly job (runs 1st of each month at 9am)
0 9 1 * * cd /path/to/networth && python3 simple_final.py --send-monthly-pairings
```

## 🎯 Current Working Demo

**Right now you can:**
```bash
cd /home/ubuntu/dev/networth

# See Ashley's ladder
python3 networth_safe.py --ladder

# See this month's pairings (already generated)
python3 networth_safe.py --pairings

# Preview what emails would be sent (no actual emails sent)
python3 networth_safe.py --preview-emails
```

## 🚨 Important Safety Features

### Current Safe Mode
- ✅ **No emails sent** - only shows previews
- ✅ **No texts sent** - phone numbers stored but not used
- ✅ **Local data only** - works completely offline
- ✅ **Matched with real players** - uses Ashley's actual ladder

### When Ready to Go Live
1. **Setup Gmail App Password** (Ashley's responsibility)
2. **Point domain to server** (DNS configuration)
3. **Switch from networth_safe.py to simple_final.py** for real emails
4. **Test with one player first** before sending to everyone

## 📞 Next Steps

### Immediate (You can do now)
1. **Test the system locally**: `python3 networth_safe.py --ladder`
2. **Point networthtennis.com** to your server IP
3. **Decide on web server** (nginx vs simple python)

### When Ready for Live Emails
1. **Ask Ashley** for Gmail App Password
2. **Configure** .env file with email credentials
3. **Send test email** to yourself first
4. **Go live** with monthly pairings

## 🎾 Result

**You'll have:**
- Professional tennis ladder system
- Automatic monthly pairings
- Email notifications to 30 players
- Live ladder rankings at networthtennis.com
- Zero maintenance after setup

**All data is imported and ready to go!**