#!/bin/bash

# Start Multiple Hatchet Workers Script
# This script starts multiple Hatchet worker processes for parallel processing

set -e

# Configuration
NUM_WORKERS=${1:-2}  # Default to 2 workers, can be overridden via argument
WORKER_SCRIPT="app/workflows/worker.py"

echo "🔧 Starting ${NUM_WORKERS} Hatchet Workers"
echo "=============================================="

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
    echo "   To enable Hatchet:"
    echo "   1. Sign up at https://cloud.onhatchet.run/"
    echo "   2. Create a project and get your client token"
    echo "   3. Add HATCHET_CLIENT_TOKEN to .env"
    echo ""
    echo "❌ Cannot start workers without HATCHET_CLIENT_TOKEN"
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
echo "   Workers: ${NUM_WORKERS}"
echo "   Hatchet: ${HATCHET_CLIENT_TOKEN:+Configured}${HATCHET_CLIENT_TOKEN:-Not configured}"
echo "   OpenAI: ${OPENAI_API_KEY:+Configured}${OPENAI_API_KEY:-Not configured}"
echo "   Database: ${DATABASE_URL}"
echo ""

# Create PID directory to track worker processes
WORKER_PID_DIR=".worker_pids"
mkdir -p "$WORKER_PID_DIR"

# Cleanup function to kill all workers on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all workers..."
    for pid_file in "$WORKER_PID_DIR"/*.pid; do
        if [[ -f "$pid_file" ]]; then
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                echo "   Stopping worker with PID $pid"
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done
    rmdir "$WORKER_PID_DIR" 2>/dev/null || true
    echo "✅ All workers stopped"
}

# Register cleanup function
trap cleanup EXIT INT TERM

# Start workers
echo "🚀 Starting workers..."
echo ""

for i in $(seq 1 $NUM_WORKERS); do
    echo "Starting worker #${i}..."
    python "$WORKER_SCRIPT" > "logs/worker_${i}.log" 2>&1 &
    worker_pid=$!
    echo "$worker_pid" > "$WORKER_PID_DIR/worker_${i}.pid"
    echo "   Worker #${i} started with PID $worker_pid (logs: logs/worker_${i}.log)"
done

echo ""
echo "✅ All ${NUM_WORKERS} workers started successfully"
echo ""
echo "📝 Worker logs:"
for i in $(seq 1 $NUM_WORKERS); do
    echo "   Worker #${i}: logs/worker_${i}.log"
done
echo ""
echo "💡 Tips:"
echo "   - Monitor all logs: tail -f logs/worker_*.log"
echo "   - Monitor specific worker: tail -f logs/worker_1.log"
echo "   - Press Ctrl+C to stop all workers"
echo ""
echo "🎯 Workers are ready to process workflows"
echo "   - Lender document processing"
echo "   - Loan application matching"
echo ""

# Wait for all workers to finish (or until interrupted)
wait

