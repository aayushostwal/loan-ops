# Setup Guide

Complete setup instructions for running the Kaaj Loan Management System.

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Backend API & workers |
| Node.js | 18+ | Frontend |
| PostgreSQL | 14+ | Database |
| Tesseract OCR | 4.0+ | PDF text extraction |
| uv | Latest | Python package manager |

---

## 1. Install System Dependencies

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install postgresql@14 tesseract python@3.11 node uv

# Start PostgreSQL
brew services start postgresql@14
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install -y postgresql postgresql-contrib tesseract-ocr \
    python3.11 python3.11-venv nodejs npm

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Windows (WSL2 recommended)

```powershell
# Use WSL2 with Ubuntu, then follow Ubuntu instructions
wsl --install -d Ubuntu
```

### Verify Installations

```bash
python3 --version    # Should be 3.10+
node --version       # Should be 18+
psql --version       # Should be 14+
tesseract --version  # Should be 4.0+
uv --version         # Latest
```

---

## 2. Database Setup

### Create Database & User

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE kaaj;
CREATE USER kaaj_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE kaaj TO kaaj_user;
\q
```

### Verify Connection

```bash
psql -U kaaj_user -d kaaj -c "SELECT 1;"
```

---

## 3. Project Setup

### Clone Repository

```bash
git clone <repository-url> kaaj
cd kaaj
```

### Create Virtual Environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### Install Python Dependencies

```bash
# Install all dependencies including dev
uv pip install -e ".[dev]"

# Or using uv sync
uv sync
```

---

## 4. Environment Configuration

### Create Environment File

```bash
cp env.example .env
```

### Configure Variables

Edit `.env` with your settings:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://kaaj_user:your_password@localhost:5432/kaaj
SYNC_DATABASE_URL=postgresql+psycopg://kaaj_user:your_password@localhost:5432/kaaj

# OpenAI API (Required for LLM processing)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Hatchet Configuration (Required for workflow processing)
# Get your token from https://cloud.onhatchet.run/
HATCHET_CLIENT_TOKEN=your-hatchet-token-here

# Optional: Custom Tesseract path
# TESSERACT_CMD=/usr/local/bin/tesseract

# Logging
LOG_LEVEL=INFO
```

### Get API Keys

#### OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com)
2. Navigate to API Keys
3. Create new secret key
4. Copy to `OPENAI_API_KEY`

#### Hatchet Token
1. Go to [cloud.onhatchet.run](https://cloud.onhatchet.run)
2. Create an account or sign in
3. Create a new project
4. Go to Settings → API Tokens
5. Generate a client token
6. Copy to `HATCHET_CLIENT_TOKEN`

---

## 5. Database Migrations

### Run Migrations

```bash
# Apply all migrations
uv run alembic upgrade head
```

### Verify Tables

```bash
psql -U kaaj_user -d kaaj -c "\dt"
```

Expected tables:
- `lenders`
- `loan_applications`
- `loan_matches`
- `alembic_version`

### Migration Commands Reference

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Upgrade to latest
uv run alembic upgrade head

# Downgrade one version
uv run alembic downgrade -1

# Show current version
uv run alembic current

# Show migration history
uv run alembic history
```

---

## 6. Running the Application

### Option A: Using Startup Scripts

Open 3 terminal windows:

**Terminal 1: API Server**
```bash
./start_api.sh
```

**Terminal 2: Hatchet Worker**
```bash
./start_worker.sh
```

**Terminal 3: Frontend**
```bash
./start_frontend.sh
```

### Option B: Manual Commands

**Terminal 1: API Server**
```bash
source .venv/bin/activate
uv run fastapi dev app/main.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Terminal 2: Hatchet Worker**
```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
python app/workflows/worker.py
```

**Terminal 3: Frontend**
```bash
cd frontend
npm install
npm run dev
# Frontend available at http://localhost:5173
```

---

## 7. Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React web app |
| API | http://localhost:8000 | FastAPI server |
| Swagger Docs | http://localhost:8000/docs | Interactive API docs |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Health Check | http://localhost:8000/health | API health status |

---

## 8. Running Tests

### Install Test Dependencies

```bash
uv pip install -e ".[dev]"
```

### Run All Tests

```bash
uv run pytest
```

### Run with Verbose Output

```bash
uv run pytest -v
```

### Run Specific Test File

```bash
uv run pytest tests/test_lender_upload.py
uv run pytest tests/test_loan_flow.py
```

### Run with Coverage

```bash
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html for report
```

### Test Categories

```bash
# Run only async tests
uv run pytest -m asyncio

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

### Test Database

Tests use SQLite in-memory database by default. For PostgreSQL testing:

```bash
# Create test database
createdb kaaj_test

# Set test database URL
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kaaj_test

# Run tests
uv run pytest
```

---

## 9. Development Workflow

### Code Formatting

```bash
# Format code
uv run black app/ tests/

# Sort imports
uv run isort app/ tests/
```

### Type Checking

```bash
uv run mypy app/
```

### Linting

```bash
# Python
uv run black --check app/

# Frontend
cd frontend && npm run lint
```

---

## 10. Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Check connection
psql -U postgres -d kaaj -c "SELECT 1;"

# Reset database
dropdb kaaj && createdb kaaj
uv run alembic upgrade head
```

### Tesseract Not Found

```bash
# Check installation
which tesseract
tesseract --version

# macOS: Add to PATH if installed via Homebrew
export PATH="/opt/homebrew/bin:$PATH"

# Or set in .env
TESSERACT_CMD=/opt/homebrew/bin/tesseract
```

### Worker Not Processing

1. Check `HATCHET_CLIENT_TOKEN` is set correctly
2. Verify worker is running: `python app/workflows/worker.py`
3. Check Hatchet dashboard at [cloud.onhatchet.run](https://cloud.onhatchet.run)
4. Review worker logs for errors

### OpenAI API Errors

1. Verify `OPENAI_API_KEY` is valid
2. Check API usage limits at [platform.openai.com](https://platform.openai.com)
3. Ensure sufficient credits/quota

### Frontend Not Connecting

1. Check API is running on port 8000
2. Verify CORS settings in `app/main.py`
3. Check browser console for errors
4. Ensure `.env` in frontend has correct API URL

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # API
lsof -i :5173  # Frontend

# Kill process
kill -9 <PID>
```

---

## 11. Production Deployment

### Environment Variables

Set these in your production environment:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/kaaj
SYNC_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/kaaj
OPENAI_API_KEY=sk-prod-key
HATCHET_CLIENT_TOKEN=prod-token

# Recommended
LOG_LEVEL=WARNING
```

### Running with Gunicorn

```bash
pip install gunicorn uvicorn

gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Building Frontend for Production

```bash
cd frontend
npm run build
# Output in dist/ folder
```

### Docker (Optional)

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv pip install -e .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Quick Reference

### Common Commands

```bash
# Start everything
./start_api.sh & ./start_worker.sh & ./start_frontend.sh

# Run tests
uv run pytest

# Apply migrations
uv run alembic upgrade head

# Format code
uv run black app/ tests/

# Check health
curl http://localhost:8000/health
```

### File Locations

| Item | Path |
|------|------|
| API Entry | `app/main.py` |
| Database Config | `app/db.py` |
| Models | `app/models/` |
| Routes | `app/routers/` |
| Services | `app/services/` |
| Workflows | `app/workflows/` |
| Migrations | `alembic/versions/` |
| Tests | `tests/` |
| Frontend | `frontend/` |

