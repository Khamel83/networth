"""
ASHLEY KAFMAN'S BEAUTIFUL EMAIL TEMPLATES
ONE_SHOT style: Simple but pretty, maximum impact
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import base64
from datetime import datetime

class PrettyTennisEmails:
    def __init__(self):
        self.club_name = "Ashley's Tennis Matching"
        self.club_email = "[redacted-email]"  # Ashley will update this
        self.brand_colors = {
            'primary': '#4CAF50',      # Tennis green
            'secondary': '#2196F3',    # Trust blue
            'accent': '#FFC107',       # Tennis ball yellow
            'dark': '#1A237E',         # Professional dark
            'light': '#F5F5F5'         # Clean white
        }

    def create_tennis_ball_art(self):
        """Create ASCII tennis ball art"""
        return """
          .--.
        /,-o /
       /_  _/
      /   _  \\
     /        \\
    /          \\
    |            |
    |            |
     \\          /
      \\        /
       \\      /
        \\    /
         \\  /
          \\/
        """

    def create_clean_divider(self):
        """Create pretty divider"""
        return "•" * 15

    def match_notification_email(self, player, opponent, match_details):
        """Beautiful but simple match notification"""
        subject = f"🎾 Tennis Match: {opponent['name']} ({self.club_name})"

        body = f"""
{self.create_tennis_ball_art()}

┌─────────────────────────────────────────────────────┐
│  🎾 TENNIS MATCH FOUND! {self.club_name}                   │
└─────────────────────────────────────────────────────┘

Hi {player['name']} 🎾

Great news! You've been matched with {opponent['name']}.

{self.create_clean_divider()}

📊  MATCH DETAILS
┌───────────────┬─────────────────────────────────────┐
│  Opponent     │ {opponent['name']} (Skill: {opponent['skill_level']})    │
│  Date         │ {match_details['date']}                      │
│  Time         │ {match_details['suggested_time']}            │
│  Location     │ {match_details['location']}                 │
│  Match Type   │ Singles                                   │
└───────────────┴─────────────────────────────────────┘

{self.create_clean_divider()}

🎯  NEXT STEPS
1. Can you play at this time?

   ┌─┐  YES, I can play:    {self.web_url}/confirm/{match_details['match_id']}/yes/{player['id']}
   │ │  [Click here for contact info]
   └─┘

   ┌─┐  NO, I can't play: {self.web_url}/confirm/{match_details['match_id']}/no/{player['id']}
   │ │  [I'll find you another match soon]
   └─┘

{self.create_clean_divider()}

💡  REMEMBER
• No obligation if you can't make it
• Your privacy is protected
• Contact details only shared after confirmation
• This matching system gets better with your feedback

{self.create_clean_divider()}

Have fun on the court! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return subject, body

    def match_confirmed_email(self, player, opponent, match_details):
        """Beautiful confirmation email"""
        subject = f"✅ TENNIS MATCH CONFIRMED: {opponent['name']}"

        body = f"""
✅✅✅ TENNIS MATCH CONFIRMED ✅✅✅

┌─────────────────────────────────────────────────────┐
│  Your match with {opponent['name']} is ON! 🎾          │
└─────────────────────────────────────────────────────┘

Hi {player['name']},

{opponent['name']} confirmed! Time to hit the courts 🎾

{self.create_clean_divider()}

📊  YOUR MATCH
┌─────────────────────────┬────────────────────────────────┐
│  🤝 Opponent             │ {opponent['name']} (Skill: {opponent['skill_level']}) │
│  📅 Date                  │ {match_details['date']}                │
│  ⏰ Time                  │ {match_details['suggested_time']}          │
│  📍 Location              │ {match_details['location']}              │
│  🏓 Match Type            │ Singles                              │
└─────────────────────────┴────────────────────────────────┘

{self.create_clean_divider()}

📞  CONTACT INFORMATION
┌─────────────────────────┬────────────────────────────────┐
│  📱 Phone                │ {opponent['phone']}                     │
│  📧 Email                │ {opponent['email']}                     │
└─────────────────────────┴────────────────────────────────┘

{self.create_clean_divider()}

💬  GET STARTED
Contact {opponent['name']} to coordinate!

💭  Suggested message:
"Hi {opponent['name']}! I'm your tennis match from {self.club_name}. When works for you this week?"

{self.create_clean_divider()}

📅  FOLLOW UP
In 3 days, I'll ask how your match went to improve future matches.

{self.create_clean_divider()}

Have a fantastic game! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return subject, body

    def feedback_request_email(self, player, opponent):
        """Beautiful feedback request"""
        subject = f"🎾 How was your match with {opponent['name']}?"

        body = f"""
🎾🎾🎾 HOW WAS YOUR MATCH? 🎾🎾🎾

┌─────────────────────────────────────────────────────┐
│  Your feedback helps us find better matches! 🏆        │
└─────────────────────────────────────────────────────┘

Hi {player['name']},

Hope you had a great time with {opponent['name']}! 🎾

{self.create_clean_divider()}

💭  QUICK FEEDBACK
Just reply to this email and tell me:

✅  Did you play the match?
✅  How was the skill level match?
✅  Did you enjoy playing with {opponent['name']}?
✅  Would you play with them again?

{self.create_clean_divider()}

💬  EXAMPLE REPLY:
"Yes we played! Skill was perfect, had fun, would play again.
Played at Beverly Hills courts - great courts, sunny day!"

{self.create_clean_divider()}

🎯  WHY YOUR FEEDBACK MATTERS
• Improves skill matching algorithms
• Helps find compatible playing partners
• Builds better tennis community
• Gets you more suitable matches

{self.create_clean_divider()}

Just hit reply with your thoughts - I'll read every one! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return subject, body

    def weekly_summary_email(self, stats):
        """Beautiful weekly summary for Ashley"""
        subject = f"📊 Weekly Tennis Matching Summary - {self.club_name}"

        body = f"""
┌─────────────────────────────────────────────────────┐
│  📊 WEEKLY TENNIS MATCHING SUMMARY - {self.club_name}     │
└─────────────────────────────────────────────────────┘

Hi Ashley Kaufman!

Here's your weekly tennis community report 🎾

{self.create_clean_divider()}

🎾  COMMUNITY STATS
┌───────────────────────┬────────────────────────────────┐
│  👥 Total Players       │ {stats['total_players']}                         │
│  🆕 New Players        │ {stats['new_players']}                            │
│  ✅ Active Players      │ {stats['active_players']}                           │
│  🎮 Matches Made        │ {stats['matches_made']}                             │
└───────────────────────┴────────────────────────────────┘

{self.create_clean_divider()}

📈  MATCHING RESULTS
┌───────────────────────┬────────────────────────────────┐
│  ✅ Matches Confirmed   │ {stats['matches_confirmed']}                     │
│  📊 Acceptance Rate      │ {stats['acceptance_rate']}%                        │
│  🏆 Total Matches Played │ {stats['total_matches_played']}                   │
│  ⭐ Avg Feedback Score   │ {stats['avg_feedback_score']}/5                     │
└───────────────────────┴────────────────────────────────┘

{self.create_clean_divider()}

💡  FEEDBACK INSIGHTS
• Most popular playing time: {stats['popular_times']}
• Best matched locations: {stats['popular_locations']}
• Average skill rating: {stats['avg_skill_match']}/5
• Player satisfaction: {stats['avg_enjoyment']}/5

{self.create_clean_divider()}

🔧  SYSTEM STATUS
• Uptime: {stats['uptime']}
• Last match run: {stats['last_match_run']}
• Database backups: {stats['backup_status']}
• System health: {stats['health_status']}

{self.create_clean_divider()}

🚀  RECOMMENDATIONS FOR NEXT WEEK
{stats['recommendations']}

{self.create_clean_divider()}

🎾  GREAT JOB GROWING LA'S TENNIS COMMUNITY!

Keep doing what you're doing - players love the simple,
direct matching approach! 🎾

---
{self.club_name} Automation
Ashley Kaufman
        """.strip()

        return subject, body

    def no_match_email(self, player):
        """Encouraging no-match email"""
        subject = f"🎾 No Tennis Match This Week - {self.club_name}"

        body = f"""
🌟 NO MATCH THIS WEEK - BUT DON'T WORRY! 🌟

┌─────────────────────────────────────────────────────┐
│  Great tennis matches are on the way! 🎾              │
└─────────────────────────────────────────────────────┘

Hi {player['name']},

No compatible tennis match was found for you this week.
But don't worry - great matches take time! 🎾

{self.create_clean_divider()}

🤔  WHY NO MATCH THIS WEEK?

It might be because:
• Limited available players in your skill level
• Schedule preferences don't align perfectly
• Location preferences are very specific
• You're already very active in the matching system

{self.create_clean_divider()}

🔧  WHAT YOU CAN DO:

💬  UPDATE PREFERENCES
Reply to this email with:
• "I can play: Monday, Wednesday, Friday"
• "I'm willing to travel 20 miles"
• "Any time works for me"

📊  EXPAND YOUR OPTIONS
• Try playing with slightly different skill levels
• Consider different times of day
• Explore new tennis courts in your area

{self.create_clean_divider()}

🎯  POSITIVE VIBES
The more flexible your preferences, the more matches you'll get!
Your perfect tennis partner is out there - we'll find them! 🎾

{self.create_clean_divider()}

💪  KEEP PLAYING
Every week brings new players and new opportunities.
Your next match could be the one you've been waiting for!

I'll keep looking for matches and email you as soon as I find one! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return subject, body

    def send_pretty_email(self, to_email, subject, body, is_html=False):
        """Send beautiful formatted email"""
        try:
            msg = MIMEText(body, 'plain') if not is_html else MIMEText(body, 'html')
            msg['Subject'] = subject
            msg['From'] = self.club_email
            msg['To'] = to_email

            # Set professional headers
            msg['X-Mailer'] = f'{self.club_name} Matching System'
            msg['X-Priority'] = '3'  # Normal priority
            msg['Precedence'] = 'bulk'

            # Send via Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()

            gmail_password = os.getenv('GMAIL_PASSWORD')
            if gmail_password:
                server.login(self.club_email, gmail_password)
                server.send_message(msg)
                print(f"✅ Beautiful email sent to {to_email}")

            server.quit()
            return True
        except Exception as e:
            print(f"❌ Email failed to {to_email}: {e}")
            return False

# Quick test
if __name__ == "__main__":
    pretty = PrettyTennisEmails()

    # Test a match notification
    player = {"name": "John", "skill_level": 3.5, "id": "123"}
    opponent = {"name": "Sarah", "skill_level": 3.5, "id": "456", "phone": "555-1234", "email": "sarah@example.com"}
    match = {
        "date": "Tomorrow, Nov 22",
        "suggested_time": "6 PM",
        "location": "Beverly Hills",
        "match_id": "abc123"
    }

    subject, body = pretty.match_notification_email(player, opponent, match)
    print("Beautiful Match Notification:")
    print("=" * 60)
    print(f"Subject: {subject}")
    print("=" * 60)
    print(body)
    print("=" * 60)