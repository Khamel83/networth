"""
Vercel Serverless Function: Email Notifications
Uses Resend (free 3,000 emails/month) for sending:
- Monthly pairing notifications
- Match reminders
- Score confirmations
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime


def get_supabase_client():
    """Lazy initialization of Supabase client"""
    try:
        from supabase import create_client
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_ANON_KEY')
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


def send_email(to_email, subject, html_content, reply_to=None):
    """
    Send email via Resend API

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        reply_to: Optional reply-to address (used for pairing emails so replies go to opponent)
    """
    try:
        # KILL SWITCH - DO NOT SEND EMAILS UNLESS EXPLICITLY ENABLED
        email_enabled = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
        if not email_enabled:
            return {
                'success': True,
                'blocked': True,
                'message': 'Email sending is disabled (EMAIL_ENABLED=false)'
            }

        # ALLOWLIST MODE - If set, ONLY send to these emails (comma-separated)
        # Example: EMAIL_ALLOWLIST=tennis@khamel.com,ashleybrooke.kaufman@gmail.com
        allowlist = os.environ.get('EMAIL_ALLOWLIST', '').strip()
        if allowlist:
            allowed_emails = [e.strip().lower() for e in allowlist.split(',') if e.strip()]
            if to_email and to_email.lower() not in allowed_emails:
                return {
                    'success': True,
                    'blocked': True,
                    'message': f'Email not in allowlist: {to_email}'
                }

        import requests
        api_key = os.environ.get('RESEND_API_KEY')

        if not api_key:
            return {'success': False, 'error': 'RESEND_API_KEY not configured'}

        email_payload = {
            'from': os.environ.get('EMAIL_FROM', 'NET WORTH Tennis <noreply@networthtennis.com>'),
            'to': [to_email],
            'subject': subject,
            'html': html_content
        }

        # Reply-To trick: if set, replies go directly to opponent instead of noreply
        if reply_to:
            email_payload['reply_to'] = reply_to

        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=email_payload
        )

        if response.status_code == 200:
            return {'success': True, 'id': response.json().get('id')}
        else:
            return {'success': False, 'error': response.text}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_pairing_email_html(player1_name, player2_name, opponent_email, period_label,
                           player_availability="", opponent_availability=""):
    """
    Generate HTML for pairing notification email (sent to both players)

    This version uses the new design from Ashley's Christmas 2025 feedback.
    The email is sent to both players at once (Reply All to coordinate).
    """
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
                backdrop-filter: blur(10px);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                letter-spacing: -0.02em;
                text-transform: lowercase;
            }}
            .tagline {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                margin-top: 5px;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
            }}
            .card-title {{
                color: #d165a4;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .greeting {{
                font-size: 18px;
                line-height: 1.6;
                color: #1a1a1a;
                margin-bottom: 20px;
            }}
            .cta-text {{
                font-size: 16px;
                font-weight: 600;
                color: #d165a4;
                margin: 20px 0;
            }}
            .instruction {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 15px;
            }}
            .availability {{
                background: #f8f8f8;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }}
            .availability-title {{
                color: #d165a4;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 12px;
            }}
            .availability-row {{
                color: #666;
                font-size: 14px;
                margin: 8px 0;
            }}
            .availability-name {{
                font-weight: 600;
                color: #1a1a1a;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .signoff {{
                margin-top: 30px;
                color: #666;
                font-size: 15px;
                line-height: 1.6;
            }}
            .signoff-name {{
                font-weight: 600;
                color: #1a1a1a;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
                <p class="tagline">Tennis. Events. Community.</p>
            </div>

            <div class="card">
                <div class="card-title">You're Matched for {period_label}</div>

                <p class="greeting">Hi {player1_name} and {player2_name},</p>

                <p class="instruction">You've been matched for a league game in {period_label}.</p>

                <p class="cta-text">Go ahead... make the first move 😉</p>

                <p class="instruction">
                    Please reply all with a few dates and times you're available so you can get your match on the calendar.
                </p>

                <p class="instruction">
                    You're free to choose the date, time, and location that work best for both of you.
                </p>

                {f'''<div class="availability">
                    <div class="availability-title">Availability</div>
                    <div class="availability-row"><span class="availability-name">{player1_name}:</span> {player_availability or "Check their profile"}</div>
                    <div class="availability-row"><span class="availability-name">{player2_name}:</span> {opponent_availability or "Check their profile"}</div>
                </div>''' if player_availability or opponent_availability else ''}

                <p class="instruction">
                    You can view match details and log your score here:
                </p>

                <a href="{site_url}/dashboard" class="btn">View Match Details →</a>

                <div class="signoff">
                    <p>Have fun and happy hitting,</p>
                    <p class="signoff-name">Net Worth</p>
                </div>
            </div>

            <div class="footer">
                <p>Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_reminder_email_html(player_name, opponent_name, period_label, days_left):
    """Generate HTML for reminder email with new design"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
                text-align: center;
            }}
            .card-title {{
                color: #ec613e;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .days {{
                font-size: 48px;
                font-weight: 700;
                color: #ec613e;
                margin: 10px 0;
            }}
            .days-label {{
                color: #666;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin: 25px 0;
                text-align: left;
            }}
            .opponent {{
                color: #d165a4;
                font-weight: 600;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 10px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
            </div>

            <div class="card">
                <div class="card-title">Match Reminder</div>
                <div class="days">{days_left}</div>
                <div class="days-label">days left this month</div>

                <p class="message">
                    Hi {player_name}! Just a friendly reminder that you have {days_left} days left to play your match with <span class="opponent">{opponent_name}</span> this month.
                </p>

                <p class="message">
                    If you haven't connected yet, now's a great time to reach out!
                </p>

                <a href="{site_url}/dashboard" class="btn">Report Score →</a>
            </div>

            <div class="footer">
                <p>Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_welcome_email_html(player_name, membership_tier='player'):
    """Generate HTML for welcome email when new player joins"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    tier_text = "You'll receive your first match assignment at the start of next month" if membership_tier == 'player' else "Enjoy access to our events and community"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .tagline {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                margin-top: 5px;
            }}
            .welcome {{
                font-size: 28px;
                font-weight: 700;
                text-align: center;
                margin: 30px 0;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
            }}
            .card-title {{
                color: #d165a4;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .intro {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 20px;
            }}
            .next-steps {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            .next-steps li {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
                display: flex;
                align-items: flex-start;
                gap: 10px;
            }}
            .next-steps li:last-child {{
                border-bottom: none;
            }}
            .check {{
                color: #d165a4;
                font-weight: 600;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
                <p class="tagline">Tennis. Events. Community.</p>
            </div>

            <div class="welcome">Welcome, {player_name}!</div>

            <div class="card">
                <p class="intro">
                    You're officially part of LA's East Side women's tennis community. We're so glad you're here!
                </p>

                <div class="card-title">What Happens Next</div>
                <ul class="next-steps">
                    <li><span class="check">✓</span> {tier_text}</li>
                    <li><span class="check">✓</span> Log into your dashboard to set your availability preferences</li>
                    <li><span class="check">✓</span> Connect with the community in our WhatsApp group</li>
                </ul>

                <a href="{site_url}/dashboard" class="btn">Go to Dashboard →</a>
            </div>

            <div class="footer">
                <p>Happy hitting!</p>
                <p style="margin-top: 5px;">Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_score_confirmation_email_html(player_name, opponent_name, score_display, games_won, period_label):
    """Generate HTML for score confirmation email after match is reported"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
                text-align: center;
            }}
            .card-title {{
                color: #22c55e;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .score {{
                font-size: 42px;
                font-weight: 700;
                color: #1a1a1a;
                margin: 15px 0;
            }}
            .games {{
                font-size: 18px;
                font-weight: 600;
                color: #d165a4;
                margin: 10px 0;
            }}
            .opponent {{
                color: #666;
                font-size: 15px;
                margin-top: 15px;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
            </div>

            <div class="card">
                <div class="card-title">Match Recorded</div>
                <div class="score">{score_display}</div>
                <div class="games">+{games_won} games added to your total</div>
                <div class="opponent">vs {opponent_name} • {period_label}</div>

                <a href="{site_url}#rankings" class="btn">View Rankings →</a>
            </div>

            <div class="footer">
                <p>Thanks for playing!</p>
                <p style="margin-top: 5px;">Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_outstanding_match_email_html(player_name, opponent_name, opponent_email, period_label):
    """Generate HTML for outstanding match reminder (from previous months that weren't completed)"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
            }}
            .card-title {{
                color: #d165a4;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 20px;
            }}
            .period {{
                color: #d165a4;
                font-weight: 600;
            }}
            .opponent {{
                color: #1a1a1a;
                font-weight: 600;
            }}
            .options {{
                background: #f8f8f8;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }}
            .option {{
                color: #666;
                font-size: 14px;
                margin: 12px 0;
                display: flex;
                align-items: flex-start;
                gap: 10px;
            }}
            .option strong {{
                color: #1a1a1a;
            }}
            .no-pressure {{
                color: #888;
                font-style: italic;
                font-size: 14px;
                margin-top: 20px;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 15px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
            </div>

            <div class="card">
                <div class="card-title">Quick Check-in</div>
                <p class="message">
                    Hey {player_name}! Just wanted to check in about your <span class="period">{period_label}</span> match with <span class="opponent">{opponent_name}</span>.
                </p>

                <div class="options">
                    <div class="option">✓ <strong>Yes, we played!</strong> Report the score anytime - better late than never</div>
                    <div class="option">✗ <strong>Didn't work out?</strong> No worries at all - we'll pair you fresh next month</div>
                </div>

                <p class="no-pressure">
                    No pressure either way. Life happens! This is just a friendly check-in.
                </p>

                <a href="{site_url}/dashboard" class="btn">Report Score →</a>
            </div>

            <div class="footer">
                <p>Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_sitout_confirmation_email_html(player_name, period_label):
    """Generate HTML for sit-out confirmation email"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
            }}
            .card-title {{
                color: #d165a4;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 15px;
            }}
            .highlight {{
                color: #1a1a1a;
                font-weight: 600;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
            </div>

            <div class="card">
                <div class="card-title">You're Sitting Out</div>

                <p class="message">
                    Hi {player_name},
                </p>

                <p class="message">
                    This confirms you've chosen to sit out match assignments for <span class="highlight">{period_label}</span>.
                </p>

                <p class="message">
                    You won't be assigned a match until you toggle back in.
                </p>

                <p class="message">
                    To rejoin, just log into your dashboard and click the button to start playing again.
                </p>

                <a href="{site_url}/dashboard" class="btn">Go to Dashboard →</a>
            </div>

            <div class="footer">
                <p>See you back on the court soon!</p>
                <p style="margin-top: 5px;">Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_rejoin_confirmation_email_html(player_name, eligible_month):
    """Generate HTML for rejoin confirmation email"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
                text-align: center;
            }}
            .card-title {{
                color: #22c55e;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .welcome {{
                font-size: 24px;
                font-weight: 700;
                color: #1a1a1a;
                margin: 15px 0;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin: 15px 0;
            }}
            .highlight {{
                color: #d165a4;
                font-weight: 600;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
            </div>

            <div class="card">
                <div class="card-title">Welcome Back!</div>

                <p class="welcome">You're back in, {player_name}!</p>

                <p class="message">
                    Great news! You're back in the match queue.
                </p>

                <p class="message">
                    You'll be assigned a match starting <span class="highlight">{eligible_month}</span>.
                </p>

                <a href="{site_url}/dashboard" class="btn">Go to Dashboard →</a>
            </div>

            <div class="footer">
                <p>Looking forward to seeing you play!</p>
                <p style="margin-top: 5px;">Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_last_chance_email_html(player_name, opponent_name, opponent_email, period_label):
    """Generate HTML for last chance reminder (2-3 days before month ends)"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
                border: 2px solid #ec613e;
            }}
            .card-title {{
                color: #ec613e;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 700;
                margin-bottom: 15px;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 20px;
            }}
            .opponent {{
                color: #d165a4;
                font-weight: 600;
            }}
            .contact {{
                background: #f8f8f8;
                border-radius: 12px;
                padding: 15px;
                margin: 20px 0;
            }}
            .contact-label {{
                color: #d165a4;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 5px;
            }}
            .contact-email {{
                color: #1a1a1a;
                font-size: 15px;
            }}
            .no-worries {{
                color: #888;
                font-size: 14px;
                margin-top: 20px;
            }}
            .btn {{
                display: inline-block;
                background: #ec613e;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 15px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
            </div>

            <div class="card">
                <div class="card-title">Last Chance!</div>

                <p class="message">
                    Hey {player_name}, {period_label} ends in just a few days and you still haven't played your match with <span class="opponent">{opponent_name}</span>.
                </p>

                <div class="contact">
                    <p class="contact-label">Reach out now</p>
                    <p class="contact-email">{opponent_email}</p>
                </div>

                <p class="no-worries">
                    If you can't make it work, no worries - just let us know and we'll pair you with someone else next month.
                </p>

                <a href="{site_url}/dashboard" class="btn">Report Score →</a>
            </div>

            <div class="footer">
                <p>Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_monthly_availability_email_html():
    """Generate HTML for monthly availability check email (sent on 27th)"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .tagline {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                margin-top: 5px;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
            }}
            .card-title {{
                color: #d165a4;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 15px;
            }}
            .bullet-list {{
                color: #666;
                font-size: 14px;
                line-height: 1.8;
                margin: 15px 0;
                padding-left: 20px;
            }}
            .bullet-list li {{
                margin-bottom: 8px;
            }}
            .highlight {{
                color: #1a1a1a;
                font-weight: 600;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .signoff {{
                margin-top: 25px;
                color: #666;
                font-size: 15px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
                <p class="tagline">Tennis. Events. Community.</p>
            </div>

            <div class="card">
                <div class="card-title">Quick Check</div>

                <p class="message">Hi there,</p>

                <p class="message">Quick housekeeping note as we head into next month.</p>

                <p class="message">If you'd like to play next month, please make sure you're marked as <span class="highlight">active</span> in your player profile.</p>

                <p class="message">If you need to sit next month out, head to your profile and mark yourself as <span class="highlight">unavailable</span>.</p>

                <p class="message">A few things to keep in mind:</p>
                <ul class="bullet-list">
                    <li>Availability is player-controlled and does not reset automatically</li>
                    <li>If you pause, you'll stay paused until you turn playing back on</li>
                    <li>Pausing ensures you won't be assigned a match while you're away</li>
                </ul>

                <p class="message">We ask everyone to be thoughtful about updating their status so match assignments stay smooth for the whole league.</p>

                <a href="{site_url}/dashboard" class="btn">Update Your Status</a>

                <div class="signoff">
                    <p>Thanks,</p>
                    <p class="highlight">Net Worth Girlies</p>
                </div>
            </div>

            <div class="footer">
                <p>Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_final_availability_email_html():
    """Generate HTML for final availability reminder (sent on last day of month)"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
                border: 2px solid #ec613e;
            }}
            .card-title {{
                color: #ec613e;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 700;
                margin-bottom: 15px;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 15px;
            }}
            .highlight {{
                color: #1a1a1a;
                font-weight: 600;
            }}
            .bullet-list {{
                color: #666;
                font-size: 14px;
                line-height: 1.8;
                margin: 15px 0;
                padding-left: 20px;
            }}
            .bullet-list li {{
                margin-bottom: 8px;
            }}
            .note {{
                color: #888;
                font-size: 14px;
                font-style: italic;
                margin-top: 20px;
            }}
            .btn {{
                display: inline-block;
                background: #ec613e;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .signoff {{
                margin-top: 25px;
                color: #666;
                font-size: 15px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
            </div>

            <div class="card">
                <div class="card-title">Last Call</div>

                <p class="message">Hi there,</p>

                <p class="message">This is your <span class="highlight">final reminder</span> to check your playing status for next month.</p>

                <p class="message">Match assignments will be created tomorrow, so please visit your player profile today to confirm:</p>

                <ul class="bullet-list">
                    <li>You're marked <span class="highlight">active</span> if you want to play, or</li>
                    <li>You're marked <span class="highlight">unavailable</span> if you need to sit next month out</li>
                </ul>

                <p class="note">If no changes are made, your current status will carry over.</p>

                <a href="{site_url}/dashboard" class="btn">Update Your Status</a>

                <div class="signoff">
                    <p>Thanks for helping keep things running smoothly,</p>
                    <p class="highlight">Net Worth Girlies</p>
                </div>
            </div>

            <div class="footer">
                <p>Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_match_assignment_email_html(player1_name, player2_name, player1_availability, player2_availability,
                                     player1_phone, player2_phone, month_label):
    """Generate HTML for match assignment email (sent when matches are created)"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .tagline {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                margin-top: 5px;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
            }}
            .card-title {{
                color: #d165a4;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .greeting {{
                font-size: 18px;
                line-height: 1.6;
                color: #1a1a1a;
                margin-bottom: 20px;
            }}
            .cta-text {{
                font-size: 16px;
                font-weight: 600;
                color: #d165a4;
                margin: 20px 0;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 15px;
            }}
            .info-box {{
                background: #f8f8f8;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }}
            .info-title {{
                color: #d165a4;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 12px;
            }}
            .info-row {{
                color: #666;
                font-size: 14px;
                margin: 8px 0;
            }}
            .info-name {{
                font-weight: 600;
                color: #1a1a1a;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .signoff {{
                margin-top: 25px;
                color: #666;
                font-size: 15px;
            }}
            .signoff-name {{
                font-weight: 600;
                color: #1a1a1a;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
                <p class="tagline">Tennis. Events. Community.</p>
            </div>

            <div class="card">
                <div class="card-title">You're Matched for {month_label}</div>

                <p class="greeting">Hi {player1_name} and {player2_name},</p>

                <p class="message">You're matched for a Net Worth in {month_label}!</p>

                <p class="cta-text">Go ahead... make the first move 😉</p>

                <p class="message">Please reply all to this email to start coordinating a time to play.</p>

                <p class="message">Here's some info to help get things started:</p>

                <div class="info-box">
                    <div class="info-title">Availability</div>
                    <div class="info-row"><span class="info-name">{player1_name}:</span> {player1_availability or "Check their profile"}</div>
                    <div class="info-row"><span class="info-name">{player2_name}:</span> {player2_availability or "Check their profile"}</div>
                </div>

                <p class="message">You're always free to coordinate directly, and texting works too:</p>

                <div class="info-box">
                    <div class="info-title">Contact Info</div>
                    <div class="info-row"><span class="info-name">{player1_name}:</span> {player1_phone or "See profile"}</div>
                    <div class="info-row"><span class="info-name">{player2_name}:</span> {player2_phone or "See profile"}</div>
                </div>

                <p class="message">You can also view your current match and match history in your player profile.</p>

                <a href="{site_url}/dashboard" class="btn">Visit Your Dashboard</a>

                <div class="signoff">
                    <p>Have fun and happy hitting,</p>
                    <p class="signoff-name">Net Worth Girlies</p>
                </div>
            </div>

            <div class="footer">
                <p>Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_mid_month_reminder_email_html(player1_name, player2_name, month_label):
    """Generate HTML for mid-month match reminder email"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #d165a4 0%, #ec613e 50%, #e7b4b5 100%);
                color: #ffffff;
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                padding: 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                text-transform: lowercase;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                color: #1a1a1a;
                border-radius: 16px;
                padding: 30px;
                margin: 20px 0;
            }}
            .card-title {{
                color: #d165a4;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .greeting {{
                font-size: 18px;
                line-height: 1.6;
                color: #1a1a1a;
                margin-bottom: 20px;
            }}
            .message {{
                color: #666;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 15px;
            }}
            .highlight {{
                color: #d165a4;
                font-weight: 600;
            }}
            .note {{
                color: #888;
                font-size: 14px;
                font-style: italic;
                margin-top: 15px;
            }}
            .btn {{
                display: inline-block;
                background: #d165a4;
                color: #ffffff;
                padding: 14px 32px;
                text-decoration: none;
                font-weight: 600;
                border-radius: 50px;
                margin-top: 20px;
            }}
            .signoff {{
                margin-top: 25px;
                color: #666;
                font-size: 15px;
            }}
            .signoff-name {{
                font-weight: 600;
                color: #1a1a1a;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">net worth</div>
            </div>

            <div class="card">
                <div class="card-title">Friendly Reminder</div>

                <p class="greeting">Hi {player1_name} and {player2_name},</p>

                <p class="message">Just a friendly reminder to get your <span class="highlight">{month_label}</span> match on the calendar.</p>

                <p class="message">If you've already played, feel free to ignore this note (and nice work!).</p>

                <p class="message">If not, there's still plenty of time to coordinate and get out on the court.</p>

                <p class="note">You can always find match details in your player profile.</p>

                <a href="{site_url}/dashboard" class="btn">Visit Your Dashboard</a>

                <div class="signoff">
                    <p>See you out there,</p>
                    <p class="signoff-name">Net Worth Girlies</p>
                </div>
            </div>

            <div class="footer">
                <p>Net Worth Tennis</p>
            </div>
        </div>
    </body>
    </html>
    """


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """Send emails based on action type"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action')

            if action == 'send_pairings':
                # Send pairing emails for current month
                result = self._send_pairing_emails(data.get('period_label'))
                self._send_success(result)

            elif action == 'send_reminders':
                # Send reminder emails for unpaid matches
                result = self._send_reminder_emails(data.get('period_label'))
                self._send_success(result)

            elif action == 'send_welcome':
                # Send welcome email to new player
                result = self._send_welcome_email(
                    data.get('player_email'),
                    data.get('player_name')
                )
                self._send_success(result)

            elif action == 'send_score_confirmation':
                # Send score confirmation to both players after match reported
                result = self._send_score_confirmations(
                    data.get('match_id'),
                    data.get('period_label')
                )
                self._send_success(result)

            elif action == 'send_last_chance':
                # Send last chance reminders (for end of month)
                result = self._send_last_chance_emails(data.get('period_label'))
                self._send_success(result)

            elif action == 'send_outstanding_reminders':
                # Send reminders for matches from previous months that weren't completed
                result = self._send_outstanding_match_emails()
                self._send_success(result)

            elif action == 'send_single':
                # Send a single email (for testing or custom notifications)
                result = send_email(
                    data.get('to'),
                    data.get('subject'),
                    data.get('html')
                )
                if result['success']:
                    self._send_success(result)
                else:
                    self._send_error(500, result['error'])

            elif action == 'send_monthly_availability':
                # Send monthly availability reminder (27th of month)
                result = self._send_monthly_availability_emails()
                self._send_success(result)

            elif action == 'send_final_availability':
                # Send final availability reminder (last day of month)
                result = self._send_final_availability_emails()
                self._send_success(result)

            elif action == 'send_mid_month_reminder':
                # Send mid-month match reminder
                result = self._send_mid_month_reminder_emails(data.get('period_label'))
                self._send_success(result)

            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            self._send_error(500, str(e))

    def _send_pairing_emails(self, period_label=None):
        """Send pairing notification to all players with assignments"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get all pending assignments for this period (with availability fields)
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(id, name, email, avail_weekday_early, avail_weekday_day, avail_weekday_late, avail_weekend_early, avail_weekend_day, avail_weekend_late, available_morning, available_afternoon, available_evening), player2:players!player2_id(id, name, email, avail_weekday_early, avail_weekday_day, avail_weekday_late, avail_weekend_early, avail_weekend_day, avail_weekend_late, available_morning, available_afternoon, available_evening)')\
            .eq('period_label', period_label)\
            .eq('status', 'pending')\
            .execute()

        sent_count = 0
        errors = []

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']

            # Build availability text for each player
            p1_avail = self._get_availability_text(p1)
            p2_avail = self._get_availability_text(p2)

            # Send to player 1 (with reply-to set to player 2)
            html1 = get_pairing_email_html(
                p1['name'], p2['name'], p2['email'], period_label,
                player_availability=p1_avail,
                opponent_availability=p2_avail
            )
            result1 = send_email(
                p1['email'],
                f'Your {period_label} Tennis Match',
                html1,
                reply_to=p2['email']  # Reply goes to opponent!
            )
            if result1['success']:
                sent_count += 1
            else:
                errors.append(f"{p1['email']}: {result1.get('error', 'Unknown error')}")

            # Send to player 2 (with reply-to set to player 1)
            html2 = get_pairing_email_html(
                p2['name'], p1['name'], p1['email'], period_label,
                player_availability=p2_avail,
                opponent_availability=p1_avail
            )
            result2 = send_email(
                p2['email'],
                f'Your {period_label} Tennis Match',
                html2,
                reply_to=p1['email']  # Reply goes to opponent!
            )
            if result2['success']:
                sent_count += 1
            else:
                errors.append(f"{p2['email']}: {result2.get('error', 'Unknown error')}")

        return {
            'sent': sent_count,
            'assignments': len(assignments.data),
            'errors': errors if errors else None
        }

    def _get_availability_text(self, player):
        """Build human-readable availability string using 6-slot system"""
        # New 6-slot system
        weekday_early = player.get('avail_weekday_early', False)
        weekday_day = player.get('avail_weekday_day', False)
        weekday_late = player.get('avail_weekday_late', False)
        weekend_early = player.get('avail_weekend_early', False)
        weekend_day = player.get('avail_weekend_day', False)
        weekend_late = player.get('avail_weekend_late', False)

        # Check if any new fields exist
        has_new_slots = any([
            weekday_early, weekday_day, weekday_late,
            weekend_early, weekend_day, weekend_late
        ])

        # Fallback to old 3-slot system for backward compatibility
        if not has_new_slots:
            morning = player.get('available_morning', False)
            afternoon = player.get('available_afternoon', False)
            evening = player.get('available_evening', False)

            if morning and afternoon and evening:
                return "Any time"
            if not morning and not afternoon and not evening:
                return ""

            times = []
            if morning:
                times.append("Mornings")
            if afternoon:
                times.append("Afternoons")
            if evening:
                times.append("Evenings")
            return ", ".join(times)

        # Build availability text from 6-slot system
        weekday_times = []
        if weekday_early:
            weekday_times.append("before 9am")
        if weekday_day:
            weekday_times.append("9-5")
        if weekday_late:
            weekday_times.append("after 5pm")

        weekend_times = []
        if weekend_early:
            weekend_times.append("before 9am")
        if weekend_day:
            weekend_times.append("9-5")
        if weekend_late:
            weekend_times.append("after 5pm")

        parts = []
        if weekday_times:
            parts.append(f"Weekdays: {', '.join(weekday_times)}")
        if weekend_times:
            parts.append(f"Weekends: {', '.join(weekend_times)}")

        return " | ".join(parts) if parts else ""

    def _send_reminder_emails(self, period_label=None):
        """Send reminders for matches not yet completed"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get pending assignments (not completed)
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(*), player2:players!player2_id(*)')\
            .eq('period_label', period_label)\
            .in_('status', ['pending', 'accepted'])\
            .execute()

        # Calculate days left in month
        now = datetime.now()
        import calendar
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_left = days_in_month - now.day

        sent_count = 0
        errors = []

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']

            # Send reminder to both players
            for player, opponent in [(p1, p2), (p2, p1)]:
                html = get_reminder_email_html(
                    player['name'],
                    opponent['name'],
                    period_label,
                    days_left
                )
                result = send_email(
                    player['email'],
                    f'⏰ {days_left} days left to play your match!',
                    html
                )
                if result['success']:
                    sent_count += 1
                else:
                    errors.append(f"{player['email']}: {result['error']}")

        return {
            'sent': sent_count,
            'pending_matches': len(assignments.data),
            'days_left': days_left,
            'errors': errors if errors else None
        }

    def _send_welcome_email(self, player_email, player_name):
        """Send welcome email to new player"""
        if not player_email or not player_name:
            return {'sent': 0, 'error': 'Missing player_email or player_name'}

        html = get_welcome_email_html(player_name)
        result = send_email(player_email, 'Welcome to NET WORTH Tennis!', html)

        return {
            'sent': 1 if result.get('success') else 0,
            'blocked': result.get('blocked', False),
            'error': result.get('error')
        }

    def _send_score_confirmations(self, match_id, period_label=None):
        """Send score confirmation emails to both players after match reported"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        if not match_id:
            return {'sent': 0, 'error': 'Missing match_id'}

        # Get match details
        match = supabase.table('matches')\
            .select('*, player1:players!player1_id(*), player2:players!player2_id(*)')\
            .eq('id', match_id)\
            .single()\
            .execute()

        if not match.data:
            return {'sent': 0, 'error': 'Match not found'}

        m = match.data
        p1 = m['player1']
        p2 = m['player2']

        # Format scores
        score_for_p1 = f"{m['set1_p1']}-{m['set1_p2']}, {m['set2_p1']}-{m['set2_p2']}"
        score_for_p2 = f"{m['set1_p2']}-{m['set1_p1']}, {m['set2_p2']}-{m['set2_p1']}"

        # Calculate games won
        p1_games = m['set1_p1'] + m['set2_p1']
        p2_games = m['set1_p2'] + m['set2_p2']

        sent_count = 0
        errors = []

        # Send to player 1
        html1 = get_score_confirmation_email_html(p1['name'], p2['name'], score_for_p1, p1_games, period_label)
        result1 = send_email(p1['email'], 'Match Recorded!', html1)
        if result1.get('success'):
            sent_count += 1
        elif result1.get('error'):
            errors.append(f"{p1['email']}: {result1['error']}")

        # Send to player 2
        html2 = get_score_confirmation_email_html(p2['name'], p1['name'], score_for_p2, p2_games, period_label)
        result2 = send_email(p2['email'], 'Match Recorded!', html2)
        if result2.get('success'):
            sent_count += 1
        elif result2.get('error'):
            errors.append(f"{p2['email']}: {result2['error']}")

        return {
            'sent': sent_count,
            'match_id': match_id,
            'errors': errors if errors else None
        }

    def _send_outstanding_match_emails(self):
        """Send reminders for matches from previous months that weren't completed.

        This finds all assignments from past periods (not current month) that are
        still pending/accepted and haven't been completed yet.
        """
        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        current_period = datetime.now().strftime('%B %Y')

        # Get all pending/accepted assignments from PREVIOUS periods (not current month)
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(*), player2:players!player2_id(*)')\
            .in_('status', ['pending', 'accepted'])\
            .neq('period_label', current_period)\
            .execute()

        sent_count = 0
        errors = []
        periods_reminded = set()

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']
            period_label = assignment['period_label']
            periods_reminded.add(period_label)

            # Send to both players
            for player, opponent in [(p1, p2), (p2, p1)]:
                html = get_outstanding_match_email_html(
                    player['name'],
                    opponent['name'],
                    opponent['email'],
                    period_label
                )
                result = send_email(
                    player['email'],
                    f"Did you finish your {period_label} match?",
                    html
                )
                if result.get('success'):
                    sent_count += 1
                elif result.get('error'):
                    errors.append(f"{player['email']}: {result['error']}")

        return {
            'sent': sent_count,
            'outstanding_matches': len(assignments.data),
            'periods': list(periods_reminded),
            'errors': errors if errors else None
        }

    def _send_last_chance_emails(self, period_label=None):
        """Send last chance reminders for matches not yet completed (end of month)"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get pending assignments (not completed)
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(*), player2:players!player2_id(*)')\
            .eq('period_label', period_label)\
            .in_('status', ['pending', 'accepted'])\
            .execute()

        sent_count = 0
        errors = []

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']

            # Send to both players
            for player, opponent in [(p1, p2), (p2, p1)]:
                html = get_last_chance_email_html(
                    player['name'],
                    opponent['name'],
                    opponent['email'],
                    period_label
                )
                result = send_email(
                    player['email'],
                    'Last chance to play your match!',
                    html
                )
                if result.get('success'):
                    sent_count += 1
                elif result.get('error'):
                    errors.append(f"{player['email']}: {result['error']}")

        return {
            'sent': sent_count,
            'pending_matches': len(assignments.data),
            'errors': errors if errors else None
        }

    def _send_monthly_availability_emails(self):
        """Send monthly availability check emails (27th of month) to all active players"""
        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get all active players (both player and social_butterfly tiers)
        players = supabase.table('players')\
            .select('id, name, email')\
            .eq('is_active', True)\
            .execute()

        sent_count = 0
        errors = []

        html = get_monthly_availability_email_html()

        for player in players.data:
            result = send_email(
                player['email'],
                'Quick check: are you playing next month?',
                html
            )
            if result.get('success'):
                sent_count += 1
            elif result.get('error'):
                errors.append(f"{player['email']}: {result['error']}")

        return {
            'sent': sent_count,
            'total_players': len(players.data),
            'errors': errors if errors else None
        }

    def _send_final_availability_emails(self):
        """Send final availability reminder (last day of month) to all active players"""
        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get all active players
        players = supabase.table('players')\
            .select('id, name, email')\
            .eq('is_active', True)\
            .execute()

        sent_count = 0
        errors = []

        html = get_final_availability_email_html()

        for player in players.data:
            result = send_email(
                player['email'],
                'Last call: update your playing status',
                html
            )
            if result.get('success'):
                sent_count += 1
            elif result.get('error'):
                errors.append(f"{player['email']}: {result['error']}")

        return {
            'sent': sent_count,
            'total_players': len(players.data),
            'errors': errors if errors else None
        }

    def _send_mid_month_reminder_emails(self, period_label=None):
        """Send mid-month match reminder to all players with pending matches"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get pending assignments for this period
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(id, name, email), player2:players!player2_id(id, name, email)')\
            .eq('period_label', period_label)\
            .in_('status', ['pending', 'accepted'])\
            .execute()

        sent_count = 0
        errors = []

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']

            # Send to player 1
            html1 = get_mid_month_reminder_email_html(p1['name'], p2['name'], period_label)
            result1 = send_email(
                p1['email'],
                f'Friendly reminder to play your {period_label} match',
                html1
            )
            if result1.get('success'):
                sent_count += 1
            elif result1.get('error'):
                errors.append(f"{p1['email']}: {result1['error']}")

            # Send to player 2
            html2 = get_mid_month_reminder_email_html(p2['name'], p1['name'], period_label)
            result2 = send_email(
                p2['email'],
                f'Friendly reminder to play your {period_label} match',
                html2
            )
            if result2.get('success'):
                sent_count += 1
            elif result2.get('error'):
                errors.append(f"{p2['email']}: {result2['error']}")

        return {
            'sent': sent_count,
            'pending_matches': len(assignments.data),
            'errors': errors if errors else None
        }

    def _send_success(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, **data}).encode())

    def _send_error(self, status, message):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode())
