"""
ASHLEY KAFMAN'S TENNIS EMAIL TEMPLATES
Simple, professional, mobile-first emails that actually work
"""

class TennisEmailTemplates:
    def __init__(self):
        self.club_name = "Ashley's Tennis Matching"
        self.club_email = "ashley-tennis@example.com"
        self.web_url = "https://ashleytennis.com"

    def match_notification_email(self, player1, player2, match_details):
        """Send when two players are matched"""
        template = f"""
🎾 TENNIS MATCH FOUND! {self.club_name}

Hi {player1['name']},

Great news! You've been matched with {player2['name']} for tennis.

📊 MATCH DETAILS:
• Opponent: {player2['name']} (Skill: {player2['skill_level']})
• Suggested Time: {match_details['suggested_time']}
• Suggested Location: {match_details['location']}

🎯 NEXT STEPS:
1. Can you play at this time? Click below:
   [YES, I can play] {self.web_url}/confirm/{match_details['match_id']}/yes?player={player1['id']}
   [NO, I can't play] {self.web_url}/confirm/{match_details['match_id']}/no?player={player1['id']}

2. Once you confirm, I'll share {player2['name']}'s contact details

3. Coordinate directly with your match and enjoy playing!

💡 REMEMBER:
• No obligation if you can't make it - just click "NO"
• Your privacy is protected - contact details only shared after confirmation
• This matching system gets better with your feedback

Questions? Reply to this email.

Have fun on the court! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return template

    def match_confirmed_email(self, player1, player2, match_details):
        """Send when both players confirm a match"""
        template = f"""
✅ TENNIS MATCH CONFIRMED! {self.club_name}

Hi {player1['name']},

Great news! {player2['name']} also confirmed. Your match is on! 🎾

📊 MATCH DETAILS:
• Opponent: {player2['name']} (Skill: {player2['skill_level']})
• Date: {match_details['date']}
• Suggested Time: {match_details['suggested_time']}
• Location: {match_details['location']}

📞 CONTACT INFORMATION:
• Phone: {player2['phone']}
• Email: {player2['email']}

💬 GET STARTED:
Contact {player2['name']} to coordinate exact time and court location.
Suggested message: "Hi {player2['name']}! I'm your tennis match from {self.club_name}. When works for you?"

🎯 REMEMBER:
• Communicate directly with your match
• Confirm court location and exact time
• Have fun and play fair

3 days from now, I'll ask how your match went to improve future matches.

Have a great game! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return template

    def follow_up_email(self, player, opponent, days_since_match=3):
        """Follow up 3 days after match for feedback"""
        template = f"""
🎾 How was your match? {self.club_name}

Hi {player['name']},

Hope you had a great match with {opponent['name']}! 🎾

I'd love to hear how it went - your feedback helps me make better matches for everyone.

Just reply to this email and tell me:
✅ Did you play the match?
✅ How was the skill level match? (Too easy / Just right / Too hard)
✅ Did you enjoy playing with {opponent['name']}?
✅ Would you play with them again?

Example reply:
"Yes we played! Skill was perfect, had fun, would play again. Played at Beverly Hills courts."

Your feedback helps improve matching for everyone - just hit reply!

Thanks for being part of {self.club_name}! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return template

    def no_match_email(self, player):
        """Send when no match found for this round"""
        template = f"""
🎾 No Tennis Match This Week {self.club_name}

Hi {player['name']},

No compatible tennis match was found for you this week.

This might be because:
• Limited available players in your skill level
• Schedule preferences don't align
• Location preferences are very specific

🔧 WHAT YOU CAN DO:
• Reply to this email to update your preferred times/days
• Expand your location radius ( willing to travel further?)
• Consider different skill level matching

I'll keep looking for matches and email you as soon as I find one!

Thanks for your patience! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return template

    def welcome_email(self, player):
        """Welcome email for new players"""
        template = f"""
🎾 Welcome to {self.club_name}!

Hi {player['name']},

Welcome! I'm excited to help you find great tennis matches in LA.

📊 YOUR PROFILE:
• Skill Level: {player['skill_level']}
• Location: {player['location_zip']}
• Preferred Days: {', '.join(player['preferred_days'])}
• Preferred Times: {', '.join(player['preferred_times'])}

🎯 HOW IT WORKS:
• I run matching algorithms daily
• When I find a compatible partner, I'll email you
• You'll get match notifications with details
• Confirm if you can play, then get contact info
• Simple, no app required!

📧 NEXT STEPS:
• Sit tight and wait for your first match email
• Feel free to reply to this email if you want to update preferences
• Check your spam folder and add ashley@{self.club_email.lower().replace(' ', '')} to contacts

Questions? Just reply to this email!

Looking forward to getting you on the court! 🎾

---
Ashley Kaufman
{self.club_name}
        """.strip()

        return template

    def weekly_summary_email(self, stats):
        """Weekly summary for Ashley (admin)"""
        template = f"""
📊 WEEKLY TENNIS MATCHING SUMMARY {self.club_name}

Hi Ashley Kaufman,

Here's your weekly tennis matching report:

🎾 COMMUNITY STATS:
• Total Players: {stats['total_players']}
• New Players This Week: {stats['new_players']}
• Active Players: {stats['active_players']}

🎯 MATCHING RESULTS:
• Matches Made: {stats['matches_made']}
• Matches Confirmed: {stats['matches_confirmed']}
• Acceptance Rate: {stats['acceptance_rate']}%
• Total Matches Played: {stats['total_matches_played']}

💡 FEEDBACK INSIGHTS:
• Average Skill Match Rating: {stats['avg_skill_match']}/5
• Average Enjoyment Rating: {stats['avg_enjoyment']}/5
• Most Common Playing Times: {stats['popular_times']}
• Most Common Locations: {stats['popular_locations']}

🔧 SYSTEM STATUS:
• Uptime: {stats['uptime']}
• Last Match Run: {stats['last_match_run']}
• Database Backups: {stats['backup_status']}

🎲 NEXT WEEK:
{stats['recommendations']}

Great job growing the tennis community! 🎾

---
{self.club_name} Automation
        """.strip()

        return template

# Usage Example
def send_tennis_email(template_func, *args, **kwargs):
    """Send email using Gmail SMTP"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        import os

        # Create email
        email_body = template_func(*args, **kwargs)
        msg = MIMEText(email_body)
        msg['Subject'] = extract_subject(email_body)
        msg['From'] = os.getenv('GMAIL_EMAIL')
        msg['To'] = kwargs.get('to_email', '')

        # Send via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(os.getenv('GMAIL_EMAIL'), os.getenv('GMAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

def extract_subject(email_body):
    """Extract subject from email body (first line with emoji)"""
    lines = email_body.strip().split('\n')
    for line in lines:
        if line.strip().startswith('🎾') or line.strip().startswith('✅') or line.strip().startswith('📊'):
            return line.strip()
    return "Tennis Matching Update"

# Quick test
if __name__ == "__main__":
    templates = TennisEmailTemplates()

    # Test a match notification
    player1 = {"name": "John", "skill_level": 3.5, "id": "123"}
    player2 = {"name": "Sarah", "skill_level": 3.5, "id": "456"}
    match_details = {"suggested_time": "6 PM", "location": "Beverly Hills"}

    email = templates.match_notification_email(player1, player2, match_details)
    print("Match Notification Email:")
    print("=" * 50)
    print(email)
    print("=" * 50)