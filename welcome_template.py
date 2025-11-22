"""
Welcome email template for Ashley Kaufman's Tennis Matching System
"""

def create_divider():
    return "•" * 15

def welcome_email(name, skill_level, location_zip):
    """Beautiful welcome email for new players"""
    club_name = "Ashley's Tennis Matching"

    return f"""
🎾
┌─────────────────────────────────────────────────────┐
│  WELCOME TO {club_name}!                             │
└─────────────────────────────────────────────────────┘

Hi {name},

I'm so excited to have you join our LA tennis community! 🎾

{create_divider()}

📊  YOUR PROFILE:
• Name: {name}
• Skill Level: {skill_level}
• Location: {location_zip}
• Preferred: Monday, Wednesday, Saturday evenings
• Status: Active and ready to match!

{create_divider()}

🎯  HOW IT WORKS:
1. I run matching algorithms daily
2. When I find compatible partners, I'll email you
3. You'll get beautiful match notifications
4. Simply click to confirm, then get contact info
5. Coordinate directly and enjoy playing!

{create_divider()}

💫  NEXT STEPS:
• Sit tight and wait for your first match email
• Feel free to reply to any email to update preferences
• Check spam folder and add to contacts
• Tell your tennis friends about us!

{create_divider()}

✅  WHAT MAKES US DIFFERENT:
• NO app downloads required
• NO profiles to maintain
• NO browsing endless options
• NO messaging back and forth
• Just direct tennis connections

{create_divider()}

🎾  LOOKING FORWARD:
Your first tennis match could be as soon as tomorrow!
I'm already working on finding you great playing partners who match your skill level and schedule.

Questions? Just reply to this email - I'll answer personally!

Can't wait to get you on the court! 🎾

---
Ashley Kaufman
{club_name}

P.S. This isn't another tennis app - it's a real tennis
matching service that actually gets people playing!
    """.strip()

# Quick test
if __name__ == "__main__":
    print(welcome_email("John Doe", "3.5", "90210"))