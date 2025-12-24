#!/bin/bash

# Start Hatchet Worker Script
# This script starts the Hatchet worker for processing loan matching workflows

set -e

echo "🚀 Starting Hatchet Worker for Loan Matching"
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
    echo "   The worker will run in mock mode without Hatchet server"
    echo ""
fi

if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "⚠️  OPENAI_API_KEY not set in .env"
    echo "   Match score calculation will fail without OpenAI API"
    echo ""
fi

if [[ -z "$DATABASE_URL" ]]; then
    echo "⚠️  DATABASE_URL not set in .env"
    echo "   Using default: postgresql+asyncpg://user:pass@localhost:5432/kaaj"
    export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/kaaj"
fi

echo "📊 Configuration:"
echo "   Database: ${DATABASE_URL}"
echo "   Hatchet: ${HATCHET_CLIENT_TOKEN:+Configured}${HATCHET_CLIENT_TOKEN:-Not configured (mock mode)}"
echo "   OpenAI: ${OPENAI_API_KEY:+Configured}${OPENAI_API_KEY:-Not configured}"
echo ""

# Check if Hatchet is configured
if [[ -z "$HATCHET_CLIENT_TOKEN" ]]; then
    echo "ℹ️  Running in MOCK MODE"
    echo "   Workflows will not be processed by Hatchet"
    echo "   To enable Hatchet:"
    echo "   1. Sign up at https://cloud.onhatchet.run/"
    echo "   2. Create a project and get your client token"
    echo "   3. Add HATCHET_CLIENT_TOKEN to .env"
    echo ""
    echo "❌ Cannot start worker without HATCHET_CLIENT_TOKEN"
    exit 1
fi

echo "🔧 Starting Hatchet worker..."
echo ""

# Start the Hatchet worker
# This will register and run the loan matching workflow
python -c "
import asyncio
import logging
from app.workflows.loan_matching_workflow import get_hatchet_client, LoanMatchingWorkflow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info('Initializing Hatchet worker...')
    
    # Get Hatchet client
    hatchet = get_hatchet_client()
    
    if not hatchet:
        logger.error('Failed to initialize Hatchet client')
        return
    
    # Create workflow instance
    workflow = LoanMatchingWorkflow(hatchet)
    
    # Register workflow
    workflow.register_workflow()
    
    logger.info('Loan matching workflow registered')
    logger.info('Worker is ready to process workflows')
    logger.info('Press Ctrl+C to stop')
    
    # Start worker (this blocks)
    hatchet.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Worker stopped by user')
    except Exception as e:
        logger.error(f'Worker failed: {str(e)}', exc_info=True)
        exit(1)
"

echo ""
echo "✅ Hatchet worker stopped"

