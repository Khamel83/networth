#!/bin/bash
# NET WORTH Tennis Ladder - Quick Start Script
# Automatically sets up and runs the platform locally for testing

set -e  # Exit on error

echo "============================================================"
echo "NET WORTH Tennis Ladder - Quick Start"
echo "============================================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi
echo "✓ Python 3 found: $(python3 --version)"

if ! command_exists pip3; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi
echo "✓ pip3 found"

echo

# Install dependencies
echo "Installing Python dependencies..."
echo "(This may take a minute on first run)"
pip3 install -q -r requirements_backend.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo

# Initialize database
echo "Initializing test database..."
python3 init_database.py --force

if [ $? -eq 0 ]; then
    echo "✓ Database initialized with 11 test players"
else
    echo "❌ Failed to initialize database"
    exit 1
fi

echo
echo "============================================================"
echo "✓ Setup Complete! Starting server..."
echo "============================================================"
echo
echo "📋 Test Credentials:"
echo "   Email: admin@networthtennis.com"
echo "   Password: tennis123"
echo
echo "🌐 Opening in your browser..."
echo "   URL: http://localhost:5000"
echo
echo "⌨️  Press Ctrl+C to stop the server"
echo "============================================================"
echo

# Wait a moment for user to read
sleep 2

# Try to open browser (works on macOS, Linux, and WSL)
if command_exists open; then
    open http://localhost:5000 >/dev/null 2>&1 &
elif command_exists xdg-open; then
    xdg-open http://localhost:5000 >/dev/null 2>&1 &
elif command_exists wslview; then
    wslview http://localhost:5000 >/dev/null 2>&1 &
fi

# Start the server
python3 production_server.py
