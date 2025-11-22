# Gmail API Setup for NET WORTH Email Automation

## Ashley's Gmail Setup Instructions

### Step 1: Google Cloud Console Setup
1. Go to https://console.cloud.google.com
2. Create new project: "networth-tennis-email"
3. Enable Gmail API:
   - Go to "APIs & Services" → "Library"
   - Search "Gmail API" → Click "Enable"

### Step 2: Create Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Application type: "Web application"
4. Name: "NET WORTH Tennis"
5. Authorized redirect URIs: "http://localhost:8080/"
6. Click "Create"
7. Download the JSON file (save as `gmail_credentials.json`)

### Step 3: Enable Less Secure Apps (Temporary)
1. Go to Ashley's Google Account: https://myaccount.google.com
2. Security → "Less secure app access" → Turn ON
3. **Note**: We'll replace this with proper OAuth later

### Step 4: Install Required Python Packages
```bash
pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Step 5: Test Gmail Connection
```python
# test_gmail.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def test_gmail():
    flow = InstalledAppFlow.from_client_secrets_file('gmail_credentials.json', SCOPES)
    creds = flow.run_local_server(port=8080)

    service = build('gmail', 'v1', credentials=creds)

    # Send test email
    message = "Subject: Test Email\n\nThis is a test from NET WORTH Tennis System."

    service.users().messages().send(
        userId='me',
        body={'raw': base64.urlsafe_b64encode(message.encode()).decode()}
    ).execute()

if __name__ == '__main__':
    test_gmail()
```

### Step 6: Production Email Service
```python
# email_service.py
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import sqlite3
import json
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class NetWorthEmailService:
    def __init__(self):
        self.service = self._get_gmail_service()

    def _get_gmail_service(self):
        """Initialize Gmail service with cached credentials"""
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file('gmail_credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)

            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def send_match_suggestion(self, player_email, player_name, suggested_opponent):
        """Send personalized match suggestion email"""
        subject = f"NET WORTH: Tennis Match Suggestion with {suggested_opponent['name']}"

        body = f"""
Hi {player_name},

Great news! We've found a potential tennis match for you:

🎾 **Opponent**: {suggested_opponent['name']}
📊 **Skill Level**: {suggested_opponent['skill']}
📍 **Preferred Courts**: {suggested_opponent['preferred_courts']}
⏰ **Availability**: {suggested_opponent['availability']}

**Why this match?**
- Similar skill level (within 0.5 points)
- Compatible playing schedules
- You haven't played each other recently

**Next Steps:**
1. Contact {suggested_opponent['name']} at {suggested_opponent['email']}
2. Schedule a match at one of your preferred courts
3. Report your score on the NET WORTH website

Ready to play? The courts are waiting!

Best regards,
NET WORTH Tennis Ladder
East Side Women's Tennis Community

---
*To unsubscribe from match suggestions, reply with "UNSUBSCRIBE"*
        """

        return self._send_email(player_email, subject, body)

    def send_match_reminder(self, player_email, player_name, opponent_name, court, match_time):
        """Send match reminder email"""
        subject = f"Reminder: Your Tennis Match Tomorrow with {opponent_name}"

        body = f"""
Hi {player_name},

This is your friendly reminder for tomorrow's tennis match:

🎾 **Opponent**: {opponent_name}
📍 **Court**: {court}
⏰ **Time**: {match_time}

**Don't forget:**
- Water bottle
- Tennis racket
- Proper tennis shoes
- Positive attitude!

Weather looks great for tennis tomorrow. Have an amazing match!

After your match, remember to report your score on the NET WORTH website.

Best regards,
NET WORTH Tennis Ladder
        """

        return self._send_email(player_email, subject, body)

    def send_score_followup(self, player_email, player_name, opponent_name, match_date):
        """Send follow-up email for unreported scores"""
        subject = f"Score Follow-up: Your Match with {opponent_name}"

        body = f"""
Hi {player_name},

We noticed you haven't reported the score from your match with {opponent_name} on {match_date}.

Reporting scores is important because:
- It updates the ladder rankings
- Helps us suggest better matches for you
- Tracks your progress over time

**Report your score in 2 minutes:**
Visit www.networthtennis.com and click "Report Match Score"

Questions about scoring? Just reply to this email!

Thanks for being part of the NET WORTH community!

Best regards,
NET WORTH Tennis Ladder
        """

        return self._send_email(player_email, subject, body)

    def send_weekly_ladder_update(self, player_email, player_name, rank_change, total_players):
        """Send weekly ladder update"""
        subject = f"NET WORTH: Your Weekly Ladder Update"

        if rank_change > 0:
            change_text = f"🎉 You moved UP {rank_change} position{'s' if rank_change > 1 else ''}!"
        elif rank_change < 0:
            change_text = f"You moved down {abs(rank_change)} position{'s' if abs(rank_change) > 1 else ''}"
        else:
            change_text = "Your position remained the same"

        body = f"""
Hi {player_name},

Here's your NET WORTH ladder update for this week:

🏆 **Your Position**: {rank_change_text}
👥 **Total Players**: {total_players} active players
📈 **Keep playing**: Every match improves your ranking!

**This Week's Top Movers:**
[Top 3 players with biggest improvements]

**Looking for your next match?**
We've analyzed your profile and have 3 suggested opponents waiting for you in your NET WORTH dashboard.

Keep playing, keep improving!

Best regards,
NET WORTH Tennis Ladder
        """

        return self._send_email(player_email, subject, body)

    def send_welcome_email(self, player_email, player_name):
        """Send welcome email to new players"""
        subject = "Welcome to NET WORTH Tennis Ladder!"

        body = f"""
Welcome to NET WORTH, {player_name}! 🎾

We're excited to have you join our East Side women's tennis community. Here's what you need to know:

**Getting Started:**
1. **Login**: Use your email and password "tennis123"
2. **Update Profile**: Add your playing preferences
3. **Find Matches**: Check your weekly match suggestions
4. **Report Scores**: Help keep the ladder accurate

**What Makes NET WORTH Different:**
✅ Women-only community (safe and supportive)
✅ East Side focused (hyperlocal courts and players)
✅ Free forever (no premium features or hidden costs)
✅ Privacy-first (we don't sell your data)
✅ Real tennis players (not just an app)

**Your Current Ranking:**
You're starting at position #[RANK] out of [TOTAL] players. Every match you play and win will move you up the ladder!

**Questions?** Just reply to this email. We're here to help you get more matches and improve your game.

Let's play some tennis!

Best regards,
Ashley and the NET WORTH Team
        """

        return self._send_email(player_email, subject, body)

    def _send_email(self, to_email, subject, body):
        """Send email using Gmail API"""
        message = MIMEText(body)
        message['to'] = to_email
        message['from'] = 'ashley@networthtennis.com'  # Ashley's email
        message['subject'] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            print(f"Email sent to {to_email}: Message ID {result['id']}")
            return True

        except Exception as e:
            print(f"Error sending email to {to_email}: {str(e)}")
            return False

# Usage Example:
if __name__ == '__main__':
    email_service = NetWorthEmailService()

    # Send a test email
    email_service.send_welcome_email("test@example.com", "Test Player")
```

### Step 7: Cron Job Setup
```bash
# Add to crontab: crontab -e
# Send weekly match suggestions (Monday 9AM)
0 9 * * 1 cd /home/ubuntu/dev/networth && python3 send_weekly_suggestions.py

# Send match reminders (Daily 6PM)
0 18 * * * cd /home/ubuntu/dev/networth && python3 send_match_reminders.py

# Send score follow-ups (Thursday 6PM)
0 18 * * 4 cd /home/ubuntu/dev/networth && python3 send_score_followups.py

# Send weekly ladder updates (Friday 5PM)
0 17 * * 5 cd /home/ubuntu/dev/networth && python3 send_weekly_ladder_updates.py
```

## Files to Create:
1. `gmail_credentials.json` - Download from Google Cloud Console
2. `email_service.py` - Email sending functionality
3. `send_weekly_suggestions.py` - Automated match suggestions
4. `send_match_reminders.py` - Match reminder emails
5. `send_score_followups.py` - Score reporting follow-ups
6. `send_weekly_ladder_updates.py` - Ladder ranking updates

## Security Notes:
- Store credentials securely
- Use environment variables for sensitive data
- Implement rate limiting for Gmail API
- Monitor email deliverability

This setup gives us professional email automation without any third-party services or costs.