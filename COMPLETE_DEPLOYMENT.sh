#!/bin/bash
# COMPLETE TENNIS MATCHING SYSTEM DEPLOYMENT
# Run this after you get Ashley's information

echo "🎾 Starting Tennis Matching System Deployment..."

# 1. Clone the repository
echo "1. Cloning repository..."
git clone https://github.com/Khamel83/networth tennis-system
cd tennis-system

# 2. Set up environment
echo "2. Setting up environment..."
echo "GMAIL_EMAIL=matches@networthtennis.club" > .env
echo "# Add Ashley's Gmail App Password here:" >> .env
echo "GMAIL_PASSWORD=" >> .env

# 3. Test system
echo "3. Testing system..."
python3 simple_final.py --add-player "Test Player" "test@tennis.com" "555-1234" "3.5" "90210"
python3 simple_final.py --list-players
python3 simple_final.py --run-matching

# 4. Schedule daily matching
echo "4. Setting up daily matching..."
echo "0 2 * * * cd $(pwd) && python3 simple_final.py --run-matching" | crontab -

# 5. Instructions
echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "NEXT STEPS:"
echo "1. Get Ashley's Gmail App Password and add to .env file"
echo "2. Import her player data: python3 simple_final.py --ashley-import players.csv"
echo "3. Domain setup: networthtennis.club email forwarding"
echo "4. Upload confirmation pages to GitHub Pages"
echo ""
echo "System will run matching every day at 2 AM automatically!"
echo "All player replies go to Ashley's Gmail inbox."
echo ""
echo "🎾 Tennis matching is ready!"