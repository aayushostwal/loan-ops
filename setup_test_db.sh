#!/bin/bash
# Setup script for test database

set -e

echo "🔧 Setting up test database for Kaaj"
echo "====================================="
echo ""

# Database configuration
DB_USER="test_user"
DB_PASS="test_pass"
DB_NAME="test_kaaj"
POSTGRES_USER="postgres"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   On macOS with Homebrew: brew install postgresql@14"
    echo "   On macOS with Homebrew: brew services start postgresql@14"
    echo "   Or: brew services start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"
echo ""

# Check if test user exists
USER_EXISTS=$(psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" 2>/dev/null || echo "")

if [ "$USER_EXISTS" == "1" ]; then
    echo "ℹ️  User '$DB_USER' already exists"
else
    echo "Creating user '$DB_USER'..."
    psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" || {
        echo "❌ Failed to create user. You might need to run this with different credentials."
        echo "   Try: sudo -u postgres ./setup_test_db.sh"
        exit 1
    }
    echo "✅ User '$DB_USER' created"
fi

echo ""

# Check if test database exists
DB_EXISTS=$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "")

if [ "$DB_EXISTS" == "1" ]; then
    echo "ℹ️  Database '$DB_NAME' already exists"
else
    echo "Creating database '$DB_NAME'..."
    psql postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || {
        echo "❌ Failed to create database"
        exit 1
    }
    echo "✅ Database '$DB_NAME' created"
fi

echo ""

# Grant privileges
echo "Granting privileges..."
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true
echo "✅ Privileges granted"

echo ""
echo "🎉 Test database setup complete!"
echo ""
echo "Test database URL:"
echo "  postgresql+asyncpg://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
echo ""
echo "You can now run tests with:"
echo "  ./run_tests.sh"
echo ""

