#!/bin/bash

# NET WORTH Tennis Ladder - Automation Setup Script
# This script sets up all cron jobs for automated tennis management

echo "🚀 Setting up NET WORTH Tennis Automation..."

# Get the current directory
NETWORTH_DIR="/home/ubuntu/dev/networth"
PYTHON_PATH=$(which python3)

echo "📍 Working directory: $NETWORTH_DIR"
echo "🐍 Python path: $PYTHON_PATH"

# Create log directory
mkdir -p "$NETWORTH_DIR/logs"

# Create crontab entries
CRON_FILE="/tmp/networth_cron"

cat > "$CRON_FILE" << EOF
# NET WORTH Tennis Ladder Automation
# Set environment variables
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
PYTHONPATH=$NETWORTH_DIR
NETWORTH_DIR=$NETWORTH_DIR

# Monday 9AM - Weekly Match Suggestions
0 9 * * 1 cd $NETWORTH_DIR && $PYTHON_PATH networth_complete.py >> $NETWORTH_DIR/logs/weekly_suggestions.log 2>&1

# Daily 6PM - Match Reminders
0 18 * * * cd $NETWORTH_DIR && $PYTHON_PATH networth_complete.py >> $NETWORTH_DIR/logs/match_reminders.log 2>&1

# Thursday 6PM - Score Follow-ups
0 18 * * 4 cd $NETWORTH_DIR && $PYTHON_PATH networth_complete.py >> $NETWORTH_DIR/logs/score_followups.log 2>&1

# Friday 5PM - Weekly Ladder Updates
0 17 * * 5 cd $NETWORTH_DIR && $PYTHON_PATH networth_complete.py >> $NETWORTH_DIR/logs/ladder_updates.log 2>&1

# Sunday 2AM - Database Maintenance
0 2 * * 0 cd $NETWORTH_DIR && $PYTHON_PATH automation_scheduler.py >> $NETWORTH_DIR/logs/database_maintenance.log 2>&1

# Hourly health check
0 * * * * echo "NET WORTH system check - \$(date)" >> $NETWORTH_DIR/logs/health.log 2>&1

EOF

# Install crontab
echo "📅 Installing crontab entries..."
crontab "$CRON_FILE"

# Verify installation
echo "✅ Crontab installed successfully!"
echo ""
echo "📋 Active NET WORTH Cron Jobs:"
crontab -l | grep "networth" | cat -n

# Create log rotation configuration
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/networth-tennis > /dev/null << EOF
$NETWORTH_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        # Restart any services that might be affected
        killall -HUP cron 2>/dev/null || true
    endscript
}
EOF

# Set up systemd service for continuous running
echo "🔧 Setting up systemd service for continuous automation..."

sudo tee /etc/systemd/system/networth-automation.service > /dev/null << EOF
[Unit]
Description=NET WORTH Tennis Automation Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$NETWORTH_DIR
Environment=PYTHONPATH=$NETWORTH_DIR
ExecStart=$PYTHON_PATH automation_scheduler.py
Restart=always
RestartSec=30
StandardOutput=append:$NETWORTH_DIR/logs/automation.log
StandardError=append:$NETWORTH_DIR/logs/automation.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable networth-automation.service
sudo systemctl start networth-automation.service

echo ""
echo "✅ NET WORTH Automation Setup Complete!"
echo ""
echo "🎯 What's been set up:"
echo "   • Weekly match suggestions (Monday 9AM)"
echo "   • Daily match reminders (6PM)"
echo "   • Score follow-ups (Thursday 6PM)"
echo "   • Weekly ladder updates (Friday 5PM)"
echo "   • Database maintenance (Sunday 2AM)"
echo "   • Continuous automation service"
echo "   • Log rotation (30-day retention)"
echo ""
echo "📊 Monitoring:"
echo "   • Logs: $NETWORTH_DIR/logs/"
echo "   • Service: sudo systemctl status networth-automation"
echo "   • Cron jobs: crontab -l"
echo ""
echo "🚀 Your NET WORTH system is now fully automated!"