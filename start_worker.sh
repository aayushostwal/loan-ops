#!/bin/bash

# Start Celery Worker for Lender Processing
# This script starts the Celery worker for async document processing

echo "🚀 Starting Celery Worker..."
echo "============================================"
echo ""

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "❌ Error: Redis is not running!"
    echo "Please start Redis first:"
    echo "  macOS: brew services start redis"
    echo "  Linux: sudo systemctl start redis"
    exit 1
fi

echo "✅ Redis is running"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please copy env.example to .env and configure it:"
    echo "  cp env.example .env"
    echo ""
fi

# Start Celery worker
echo "Starting Celery worker..."
uv run celery -A app.celery_app worker --loglevel=info

# Note: Use Ctrl+C to stop the worker

