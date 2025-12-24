# 🚀 Kaaj Quick Start Guide

Get up and running with Kaaj in minutes!

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ PostgreSQL 13+
- ✅ Tesseract OCR
- ✅ OpenAI API key

## Step 1: Clone and Setup Backend

```bash
# Clone the repository
git clone <your-repo-url>
cd kaaj

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment file
cp env.example .env

# Edit .env and add your credentials:
# - DATABASE_URL
# - OPENAI_API_KEY
# - HATCHET_CLIENT_TOKEN (optional)
```

## Step 2: Setup Database

```bash
# Create database
createdb kaaj

# Run migrations
alembic upgrade head
```

## Step 3: Start Backend Services

### Terminal 1: Start API Server

```bash
./start_api.sh
```

API will be available at: `http://localhost:8000`

### Terminal 2: Start Hatchet Worker(s) (Optional)

**Single Worker (Development)**:
```bash
./start_worker.sh
```

**Multiple Workers (Production/High Load)**:
```bash
# Start 2 workers (default)
./start_workers.sh

# Start custom number (e.g., 4 workers)
./start_workers.sh 4
```

> 💡 See `WORKERS_GUIDE.md` for detailed worker management and scaling

## Step 4: Start Frontend

### Terminal 3: Start Frontend

```bash
./start_frontend.sh
```

Frontend will be available at: `http://localhost:5173`

## Step 5: Use the Application

### Upload a Lender Policy

1. Open `http://localhost:5173/lenders`
2. Enter lender name (e.g., "ABC Bank")
3. Drag & drop or select a PDF file
4. Click "Upload Document"
5. Watch the status change: Uploaded → Processing → Completed
6. Click the eye icon to view processed data

### Upload a Loan Application

1. Navigate to `http://localhost:5173/loan-applications`
2. Enter applicant details:
   - Name (required)
   - Email (optional)
   - Phone (optional)
3. Upload PDF document
4. Click "Upload Application"
5. View match results with lenders
6. See match scores and analysis

## Quick Test

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# List lenders
curl http://localhost:8000/api/lenders/

# List loan applications
curl http://localhost:8000/api/loan-applications/
```

### Test Frontend

1. Open browser to `http://localhost:5173`
2. You should see the Kaaj interface
3. Navigate between Lenders and Loan Applications pages

## Run Tests

```bash
# Setup test database
./setup_test_db.sh

# Run all tests
./run_tests.sh

# Or run specific tests
pytest tests/test_lender_upload.py -v
pytest tests/test_loan_application_upload.py -v
```

## Common Issues

### Backend won't start

**Issue:** Database connection error

**Solution:**
```bash
# Check PostgreSQL is running
pg_isready

# Verify DATABASE_URL in .env
# Example: postgresql+asyncpg://user:pass@localhost:5432/kaaj
```

**Issue:** OpenAI API error

**Solution:**
```bash
# Verify OPENAI_API_KEY in .env
# Get key from: https://platform.openai.com/api-keys
```

### Frontend won't start

**Issue:** Port 5173 already in use

**Solution:**
```bash
# Kill existing process
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

**Issue:** API connection failed

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify VITE_API_BASE_URL in frontend/.env
```

### File upload fails

**Issue:** PDF processing error

**Solution:**
```bash
# Check Tesseract is installed
tesseract --version

# Install if missing:
# macOS: brew install tesseract
# Ubuntu: sudo apt-get install tesseract-ocr
# Windows: Download from GitHub
```

## Next Steps

### Learn More

- 📖 [Frontend Documentation](docs/FRONTEND.md) - UI guide
- 🏗️ [Architecture Guide](docs/ARCHITECTURE.md) - System design
- 🔌 [API Examples](docs/API_EXAMPLES.md) - Integration examples
- 💼 [Loan Application Flow](docs/LOAN_APPLICATION_FLOW.md) - Matching system

### Explore Features

1. **Upload Multiple Lenders**
   - Try uploading different lender policies
   - View processing results
   - Compare lender criteria

2. **Test Loan Matching**
   - Upload a loan application
   - See how it matches against lenders
   - Review match scores and analysis

3. **Monitor Processing**
   - Watch real-time status updates
   - View processing times
   - Check error messages

### Customize

1. **Adjust LLM Prompts**
   - Edit `app/services/llm_service.py`
   - Customize extraction logic
   - Fine-tune match scoring

2. **Modify UI**
   - Edit components in `frontend/src/components/`
   - Update styles in `frontend/src/index.css`
   - Customize colors in `frontend/tailwind.config.js`

3. **Add Features**
   - Create new API endpoints
   - Add frontend pages
   - Implement custom workflows

## Production Deployment

### Backend

```bash
# Use production ASGI server
pip install gunicorn uvicorn[standard]

# Run with Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Frontend

```bash
cd frontend

# Build for production
npm run build

# Deploy dist/ folder to:
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
# - Your preferred hosting
```

### Database

- Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
- Enable connection pooling
- Set up backups
- Configure SSL

### Environment

- Use environment-specific `.env` files
- Store secrets securely (AWS Secrets Manager, etc.)
- Enable HTTPS
- Configure CORS properly

## Support

Need help?

- 📖 Check [Documentation](docs/INDEX.md)
- 🐛 Review error logs
- 💬 Contact development team

## What's Next?

You're all set! 🎉

Start uploading documents and exploring the features. Check out the documentation for advanced usage and customization options.

Happy coding! 🚀

