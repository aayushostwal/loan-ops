# Test Suite for Kaaj

This directory contains comprehensive API tests for the Kaaj lender management system.

## Overview

The test suite is designed to work **without external dependencies** like Redis or OpenAI:
- ✅ **Celery/Redis**: Automatically mocked (no Redis required)
- ✅ **OpenAI LLM**: Mocked with predefined responses
- ✅ **OCR Service**: Mocked to return sample text
- ✅ **Database**: Uses separate test database

This makes tests fast, reliable, and easy to run locally or in CI/CD.

## Setup

### 1. Install Test Dependencies

```bash
# Using uv
uv pip install pytest pytest-asyncio httpx

# Or with pip
pip install pytest pytest-asyncio httpx
```

### 2. Add Test PDF Files

Place your 5 PDF files in the `tests/assets/` directory:

```
tests/
  assets/
    sample1.pdf
    sample2.pdf
    sample3.pdf
    sample4.pdf
    sample5.pdf
```

### 3. Configure Test Database

Set up a separate test database to avoid affecting your development data.

**Option A: Using environment variable**

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_kaaj"
```

**Option B: Create `.env.test` file**

```
TEST_DATABASE_URL=postgresql+asyncpg://test_user:test_pass@localhost:5432/test_kaaj
```

**Create the test database:**

```bash
# Connect to PostgreSQL
psql -U postgres

# Create test database and user
CREATE DATABASE test_kaaj;
CREATE USER test_user WITH PASSWORD 'test_pass';
GRANT ALL PRIVILEGES ON DATABASE test_kaaj TO test_user;
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_lender_upload.py
```

### Run Specific Test Class

```bash
pytest tests/test_lender_upload.py::TestLenderUpload
```

### Run Specific Test Function

```bash
pytest tests/test_lender_upload.py::TestLenderUpload::test_upload_single_pdf_success
```

### Run with Verbose Output

```bash
pytest tests/ -v
```

### Run with Print Statements

```bash
pytest tests/ -s
```

### Run with Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

## Test Structure

### Test Files

- `conftest.py` - Test configuration and fixtures
- `test_lender_upload.py` - Main test suite for lender uploads
- `assets/` - Directory containing test PDF files

### Test Classes

#### `TestLenderUpload`
- Basic upload functionality
- File validation
- Error handling
- Multiple file uploads

#### `TestLenderRetrievalAfterUpload`
- GET endpoint after upload
- List all lenders
- Filtering by status

#### `TestProcessingWorkflow`
- Complete upload and processing workflow
- Batch processing
- Status transitions

#### `TestDataValidation`
- OCR text extraction
- Data integrity
- Timestamp validation

## Key Features

### 1. Database Isolation
Each test gets a fresh database session with automatic cleanup.

### 2. Direct Processing
Tests call `_process_lender_document_async()` directly instead of using Celery workers.

### 3. Comprehensive Assertions
Tests verify:
- HTTP response codes and content
- Database state (models, fields, relationships)
- Data transformations
- Status transitions

### 4. Multiple PDF Support
Fixtures automatically discover all PDF files in `assets/` directory.

## Example Test Run

```bash
$ pytest tests/test_lender_upload.py -v

tests/test_lender_upload.py::TestLenderUpload::test_upload_single_pdf_success PASSED
tests/test_lender_upload.py::TestLenderUpload::test_upload_with_policy_details PASSED
tests/test_lender_upload.py::TestLenderUpload::test_upload_multiple_pdfs PASSED
tests/test_lender_upload.py::TestLenderUpload::test_upload_and_process PASSED
tests/test_lender_upload.py::TestLenderUpload::test_upload_invalid_file_type PASSED
...

==================== 15 passed in 12.34s ====================
```

## Mocking Strategy

### Celery/Redis Mocking

**No Redis required!** Celery tasks are automatically mocked in all tests:

- **Session-level mock**: Prevents Redis connection attempts at import time
- **Function-level mock**: Returns mock AsyncResult for `.delay()` and `.apply_async()` calls
- **Environment variables**: Set to use in-memory backends

See [CELERY_MOCKING.md](./CELERY_MOCKING.md) for detailed information.

**Key Points:**
- Tests run without Redis or Celery workers
- Tasks appear to be queued but don't actually execute
- You can verify task calls using `mock_celery` fixture
- Task logic can be tested directly by calling the async function

**Example:**

```python
async def test_upload_triggers_task(client, mock_celery, sample_pdf_file):
    with open(sample_pdf_file, "rb") as f:
        response = await client.post(
            "/api/lenders/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"lender_name": "Test"}
        )
    
    # Verify task was called (mocked)
    mock_celery['delay'].assert_called_once()
```

### LLM/OpenAI Mocking

OpenAI API calls are mocked with predefined responses:
- Returns structured lender data
- No API keys required
- Fast and deterministic

### OCR Mocking

Tesseract OCR is mocked to return sample text:
- No Tesseract installation required
- Returns predictable test data

## Troubleshooting

### No PDF files found

```
FileNotFoundError: No PDF files found in tests/assets/
```

**Solution:** Add at least one PDF file to `tests/assets/` directory.

### Database connection error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:** 
1. Ensure PostgreSQL is running
2. Check TEST_DATABASE_URL is correct
3. Verify test database exists

### OCR/Tesseract errors

```
TesseractNotFoundError: tesseract is not installed
```

**Solution:** Tests mock OCR by default. This error shouldn't occur unless testing OCR directly. If needed, install Tesseract:

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Fedora
sudo dnf install tesseract
```

### Redis/Celery connection errors

```
Retry limit exceeded while trying to reconnect to the Celery redis result store backend
```

**Solution:** 
1. Celery is automatically mocked in tests - this error shouldn't occur
2. Make sure you're running tests with pytest (not starting the app)
3. Check that `conftest.py` is being loaded properly
4. Verify you're not importing Celery before mocks are set up

The mocks are configured in `tests/conftest.py`. See [CELERY_MOCKING.md](./CELERY_MOCKING.md) for details.

### Import errors

```
ModuleNotFoundError: No module named 'app'
```

**Solution:** Run pytest from project root directory:

```bash
cd /Users/aayushostwal/Desktop/aayush/kaaj
pytest tests/
```

## Writing New Tests

### Template for New Test

```python
@pytest.mark.asyncio
async def test_your_feature(
    self,
    client: AsyncClient,
    db_session: AsyncSession,
    sample_pdf_file: str
):
    """Test description."""
    # 1. Setup
    with open(sample_pdf_file, "rb") as f:
        files = {"file": (os.path.basename(sample_pdf_file), f, "application/pdf")}
        data = {"lender_name": "Test", "created_by": "user"}
        
        # 2. Execute
        response = await client.post("/api/lenders/upload", files=files, data=data)
    
    # 3. Assert
    assert response.status_code == 201
    lender_id = response.json()["lender_id"]
    
    # 4. Verify database
    result = await db_session.execute(select(Lender).where(Lender.id == lender_id))
    lender = result.scalar_one()
    assert lender.lender_name == "Test"
```

## Notes

- Tests use a separate test database to avoid affecting development data
- Each test creates and tears down its own tables
- The `_process_lender_document_async()` function is called directly to bypass Celery
- All tests are async and use `pytest-asyncio`

