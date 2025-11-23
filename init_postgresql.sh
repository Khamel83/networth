#!/bin/bash
# Initialize PostgreSQL database on Railway
# Run this ONCE after adding PostgreSQL service to Railway

echo "=================================================="
echo "NET WORTH Tennis Ladder - PostgreSQL Setup"
echo "=================================================="
echo

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    echo "Make sure you've added PostgreSQL service to your Railway project"
    exit 1
fi

echo "✓ DATABASE_URL found"
echo

# Install psql if not available (Railway should have it)
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL client..."
    apt-get update && apt-get install -y postgresql-client
fi

echo "Creating database schema..."
echo

# Run the schema file
psql "$DATABASE_URL" -f schema_postgresql.sql

if [ $? -eq 0 ]; then
    echo
    echo "=================================================="
    echo "✓ PostgreSQL database initialized successfully!"
    echo "=================================================="
    echo
    echo "Next steps:"
    echo "1. Run the migration script to transfer data from SQLite"
    echo "   python3 migrate_sqlite_to_postgresql.py"
    echo
    echo "2. Update environment variables:"
    echo "   Remove: DATABASE_PATH"
    echo "   Keep: DATABASE_URL (already set by Railway)"
    echo
    echo "3. Restart your Railway service"
    echo "4. Test the application"
else
    echo
    echo "✗ ERROR: Failed to initialize database"
    echo "Check the error messages above"
    exit 1
fi
