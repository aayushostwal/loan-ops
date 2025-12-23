# 🚀 Lender Document Processing System - Setup Guide

## Prerequisites

### 1. System Dependencies

#### macOS
```bash
# Install Tesseract OCR
brew install tesseract

# Install Poppler (for PDF processing)
brew install poppler

# Install Redis
brew install redis
brew services start redis

# Install PostgreSQL (if not already installed)
brew install postgresql@15
brew services start postgresql@15
```

#### Ubuntu/Debian
```bash
# Install Tesseract OCR
sudo apt-get update
sudo apt-get install tesseract-ocr

# Install Poppler
sudo apt-get install poppler-utils

# Install Redis
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Verify Installations
```bash
# Check Tesseract
tesseract --version

# Check Poppler (pdfinfo)
pdfinfo -v

# Check Redis
redis-cli ping
# Should return: PONG

# Check PostgreSQL
psql --version
```

## Installation

### 1. Clone Repository
```bash
cd /path/to/your/workspace
git clone <repository-url>
cd kaaj
```

### 2. Install UV (if not already installed)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### 3. Install Python Dependencies
```bash
# Sync all dependencies
uv sync
```

### 4. Setup Database
```bash
# Create database (if not exists)
createdb kaaj

# Or using psql
psql -U postgres
CREATE DATABASE kaaj;
\q
```

### 5. Configure Environment
```bash
# Copy example env file
cp env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Important:** Make sure to set your `OPENAI_API_KEY` in the `.env` file.

### 6. Run Migrations
```bash
# Apply all migrations
uv run alembic upgrade head

# Verify current revision
uv run alembic current
```

## Running the Application

### Option 1: Development Mode (Recommended)

#### Terminal 1: Start API Server
```bash
uv run fastapi dev app/main.py
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs` (Swagger UI)

#### Terminal 2: Start Celery Worker
```bash
uv run celery -A app.celery_app worker --loglevel=info
```

### Option 2: Production Mode

#### Start API Server
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Start Celery Worker
```bash
uv run celery -A app.celery_app worker --loglevel=info --concurrency=4
```

## Testing the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok"}
```

### 2. Upload a PDF Document
```bash
curl -X POST "http://localhost:8000/api/lenders/upload" \
  -F "file=@/path/to/your/document.pdf" \
  -F "lender_name=Test Bank" \
  -F "created_by=admin@example.com"
```

Expected response:
```json
{
  "message": "PDF uploaded successfully. Processing started.",
  "lender_id": 1,
  "status": "uploaded",
  "task_id": "abc123-def456-..."
}
```

### 3. Check Processing Status
```bash
# Get lender details
curl http://localhost:8000/api/lenders/1
```

### 4. List All Lenders
```bash
curl "http://localhost:8000/api/lenders/?limit=10"
```

## Monitoring

### Check Celery Worker Status
```bash
# View active tasks
uv run celery -A app.celery_app inspect active

# View registered tasks
uv run celery -A app.celery_app inspect registered

# View worker stats
uv run celery -A app.celery_app inspect stats
```

### Check Redis
```bash
# Connect to Redis CLI
redis-cli

# Check queue length
LLEN celery

# Monitor in real-time
MONITOR
```

### Check Database
```bash
# Connect to database
psql -U postgres -d kaaj

# View lenders
SELECT id, lender_name, status, created_at FROM lenders;

# Check processing status distribution
SELECT status, COUNT(*) FROM lenders GROUP BY status;
```

## Troubleshooting

### Issue: Tesseract not found
```bash
# Set custom path in .env
TESSERACT_CMD=/usr/local/bin/tesseract

# Or find tesseract location
which tesseract
```

### Issue: Redis connection failed
```bash
# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux

# Check if running
redis-cli ping
```

### Issue: Database connection failed
```bash
# Check PostgreSQL is running
brew services list | grep postgres  # macOS
sudo systemctl status postgresql  # Linux

# Verify credentials in .env match your database setup
```

### Issue: Import errors
```bash
# Reinstall dependencies
rm -rf .venv
uv sync
```

### Issue: Migration errors
```bash
# Reset migrations (CAUTION: This will drop all data)
uv run alembic downgrade base
uv run alembic upgrade head
```

## Development

### Adding Dependencies
```bash
# Add package
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update all
uv sync --upgrade
```

### Creating New Migrations
```bash
# Auto-generate migration
uv run alembic revision --autogenerate -m "description"

# Apply migration
uv run alembic upgrade head
```

### Code Formatting
```bash
# Format code
uv run black .

# Check types
uv run mypy .

# Run tests
uv run pytest
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support

For issues or questions, please refer to the main README.md or open an issue in the repository.

