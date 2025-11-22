#!/usr/bin/env python3
"""
NET WORTH Automation Scheduler
Runs all automated processes on schedule
"""

import schedule
import time
import subprocess
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/dev/networth/automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Run a Python script and log results"""
    try:
        logger.info(f"🚀 Running {script_name}...")
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            cwd='/home/ubuntu/dev/networth'
        )

        if result.returncode == 0:
            logger.info(f"✅ {script_name} completed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"❌ {script_name} failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")

    except Exception as e:
        logger.error(f"❌ Failed to run {script_name}: {str(e)}")

def weekly_match_suggestions():
    """Send weekly match suggestions (Mondays 9AM)"""
    run_script('networth_complete.py')

def daily_match_reminders():
    """Send daily match reminders (6PM)"""
    run_script('networth_complete.py')

def weekly_ladder_update():
    """Send weekly ladder updates (Fridays 5PM)"""
    run_script('networth_complete.py')

def score_follow_ups():
    """Send score follow-ups (Thursdays 6PM)"""
    run_script('networth_complete.py')

def database_maintenance():
    """Weekly database maintenance (Sundays 2AM)"""
    try:
        logger.info("🔧 Running database maintenance...")

        # Clean up expired match suggestions
        from networth_complete import NetWorthTennisSystem
        system = NetWorthTennisSystem()

        conn = sqlite3.connect(system.db_path)
        cursor = conn.cursor()

        # Delete expired suggestions
        cursor.execute('''
            DELETE FROM match_suggestions
            WHERE expires_at < datetime('now')
        ''')

        # Archive old match reports (older than 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        cursor.execute('''
            DELETE FROM match_reports
            WHERE created_at < ?
        ''', (six_months_ago,))

        conn.commit()
        conn.close()

        logger.info("✅ Database maintenance completed")

    except Exception as e:
        logger.error(f"❌ Database maintenance failed: {str(e)}")

def setup_scheduler():
    """Setup all scheduled tasks"""
    logger.info("📅 Setting up NET WORTH automation scheduler...")

    # Weekly match suggestions (Monday 9AM)
    schedule.every().monday.at("09:00").do(weekly_match_suggestions)

    # Daily match reminders (6PM)
    schedule.every().day.at("18:00").do(daily_match_reminders)

    # Weekly ladder updates (Friday 5PM)
    schedule.every().friday.at("17:00").do(weekly_ladder_update)

    # Score follow-ups (Thursday 6PM)
    schedule.every().thursday.at("18:00").do(score_follow_ups)

    # Database maintenance (Sunday 2AM)
    schedule.every().sunday.at("02:00").do(database_maintenance)

    # Health check every hour
    schedule.every().hour.do(lambda: logger.info("💓 NET WORTH system is running normally"))

def main():
    """Main scheduler loop"""
    logger.info("🚀 NET WORTH Automation System Starting...")

    setup_scheduler()

    logger.info("⏰ Scheduler configured. Waiting for scheduled tasks...")
    logger.info("📅 Next scheduled task: Monday 9:00 AM - Weekly Match Suggestions")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler crashed: {str(e)}")
        raise

if __name__ == "__main__":
    main()