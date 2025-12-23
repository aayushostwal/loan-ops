#!/bin/bash

# Start FastAPI Development Server
# This script starts the API server for lender document processing

echo "🚀 Starting Kaaj API Server..."
echo "============================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please copy env.example to .env and configure it:"
    echo "  cp env.example .env"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if PostgreSQL is accessible
if ! psql -U postgres -d kaaj -c "SELECT 1" &> /dev/null; then
    echo "⚠️  Warning: Cannot connect to PostgreSQL database 'kaaj'"
    echo "Make sure PostgreSQL is running and database 'kaaj' exists"
    echo ""
fi

# Start FastAPI dev server
echo "Starting API server..."
echo ""
echo "📝 API Documentation will be available at:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc:      http://localhost:8000/redoc"
echo ""

uv run fastapi dev app/main.py

# Note: Use Ctrl+C to stop the server

