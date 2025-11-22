#!/bin/bash

# Tennis Match LA - Demo Setup Script
# Run this to see the beautiful mockup site with sample data

echo "🎾 Tennis Match LA - Starting Demo..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -q -r requirements.txt

# Remove old demo database if exists
if [ -f "tennis_match.db" ]; then
    echo "Cleaning old demo database..."
    rm tennis_match.db
fi

# Start the server (will auto-create sample data)
echo ""
echo "✅ Demo ready! Starting server..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎾 DEMO LOGIN CREDENTIALS (with fake sample data):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "👤 John Doe       → john@tennis.com   | password123"
echo "👤 Jane Smith     → jane@tennis.com   | password123"
echo "👤 Mike Johnson   → mike@tennis.com   | password123"
echo "👤 Sarah Wilson   → sarah@tennis.com  | password123"
echo "👤 Tom Brown      → tom@tennis.com    | password123"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Open your browser to: http://localhost:8000"
echo "🎨 Professional design, mobile-friendly interface"
echo "📊 Sample matches and data pre-populated"
echo ""
echo "Press Ctrl+C to stop the demo server"
echo ""

# Run the FastAPI server
python3 main.py
