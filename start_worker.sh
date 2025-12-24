#!/bin/bash

# Start Hatchet Worker Script
# This script starts a Hatchet worker for processing workflows (lenders and loan applications)

set -e

echo "🔧 Starting Hatchet Worker"
echo "=========================="

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated"
    if [[ -d ".venv" ]]; then
        echo "📦 Activating virtual environment..."
        source .venv/bin/activate
    else
        echo "❌ No virtual environment found. Please create one first."
        exit 1
    fi
fi

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    echo "⚠️  .env file not found"
    if [[ -f "env.example" ]]; then
        echo "📝 Please copy env.example to .env and configure it"
        echo "   cp env.example .env"
    fi
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check required environment variables
if [[ -z "$HATCHET_CLIENT_TOKEN" ]]; then
    echo "⚠️  HATCHET_CLIENT_TOKEN not set in .env"
    echo "   The worker will run in mock mode without Hatchet server"
    echo "   To enable Hatchet:"
    echo "   1. Sign up at https://cloud.onhatchet.run/"
    echo "   2. Create a project and get your client token"
    echo "   3. Add HATCHET_CLIENT_TOKEN to .env"
    echo ""
    echo "❌ Cannot start worker without HATCHET_CLIENT_TOKEN"
    exit 1
fi

if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "⚠️  OPENAI_API_KEY not set in .env"
    echo "   Processing will fail without OpenAI API"
fi

if [[ -z "$DATABASE_URL" ]]; then
    echo "⚠️  DATABASE_URL not set in .env"
    echo "   Using default: postgresql+asyncpg://postgres:postgres@localhost:5432/kaaj"
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/kaaj"
fi

echo "📊 Configuration:"
echo "   Hatchet: ${HATCHET_CLIENT_TOKEN:+Configured}${HATCHET_CLIENT_TOKEN:-Not configured}"
echo "   OpenAI: ${OPENAI_API_KEY:+Configured}${OPENAI_API_KEY:-Not configured}"
echo "   Database: ${DATABASE_URL}"
echo ""

echo "🚀 Starting single Hatchet worker..."
echo "   This worker handles both:"
echo "   - Lender document processing"
echo "   - Loan application matching"
echo ""
echo "💡 For multiple workers, use: ./start_workers.sh [num_workers]"
echo ""

# Start the unified Hatchet worker
python app/workflows/worker.py

echo ""
echo "✅ Hatchet worker stopped"
