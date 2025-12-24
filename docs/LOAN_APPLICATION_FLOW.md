# Loan Application Flow Documentation

## Overview

The Loan Application Flow allows users to upload loan application PDFs which are automatically processed and matched against all available lenders using parallel processing with Hatchet workflows.

## Architecture

### Components

1. **LoanApplication Model** - Stores loan application data
2. **LoanMatch Model** - Stores match results between applications and lenders
3. **Match Service** - Calculates match scores using LLM
4. **Hatchet Workflow** - Orchestrates parallel processing
5. **API Routes** - RESTful endpoints for managing applications

### Flow Diagram

```
┌─────────────────┐
│  Upload PDF     │
│  Application    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OCR Extract    │
│  Text from PDF  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Process    │
│  Application    │
│  Data           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Save to DB     │
│  (UPLOADED)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Trigger        │
│  Hatchet        │
│  Workflow       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Parallel Processing (Hatchet)     │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │ Lender 1 │  │ Lender 2 │  ...  │
│  │ Match    │  │ Match    │       │
│  └──────────┘  └──────────┘       │
│       │              │             │
│       ▼              ▼             │
│  ┌──────────┐  ┌──────────┐       │
│  │ LLM      │  │ LLM      │       │
│  │ Score    │  │ Score    │       │
│  └──────────┘  └──────────┘       │
│       │              │             │
│       ▼              ▼             │
│  ┌──────────┐  ┌──────────┐       │
│  │ Save     │  │ Save     │       │
│  │ Match    │  │ Match    │       │
│  └──────────┘  └──────────┘       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Update App     │
│  Status         │
│  (COMPLETED)    │
└─────────────────┘
```

## API Endpoints

### 1. Upload Loan Application

**POST** `/api/loan-applications/upload`

Upload a loan application PDF for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `file`: PDF file (required)
  - `applicant_name`: Name of applicant (required)
  - `applicant_email`: Email address (optional)
  - `applicant_phone`: Phone number (optional)
  - `application_details`: JSON string with additional details (optional)
  - `created_by`: User creating the record (optional)

**Response:**
```json
{
  "message": "Loan application uploaded successfully. Matching process started.",
  "application_id": 123,
  "status": "uploaded",
  "workflow_run_id": "wf-abc123"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/loan-applications/upload" \
  -F "file=@loan_application.pdf" \
  -F "applicant_name=John Doe" \
  -F "applicant_email=john@example.com" \
  -F "applicant_phone=+1-555-0100"
```

### 2. Get Loan Application

**GET** `/api/loan-applications/{application_id}`

Retrieve a specific loan application with its matches.

**Parameters:**
- `application_id`: ID of the application (path parameter)
- `include_matches`: Include match results (query parameter, default: true)

**Response:**
```json
{
  "id": 123,
  "applicant_name": "John Doe",
  "applicant_email": "john@example.com",
  "applicant_phone": "+1-555-0100",
  "application_details": {...},
  "processed_data": {...},
  "status": "completed",
  "workflow_run_id": "wf-abc123",
  "created_at": "2025-12-24T10:00:00Z",
  "updated_at": "2025-12-24T10:05:00Z",
  "original_filename": "loan_application.pdf",
  "matches": [
    {
      "id": 1,
      "lender_id": 10,
      "match_score": 85.5,
      "status": "completed",
      "match_analysis": {...}
    }
  ]
}
```

### 3. List Loan Applications

**GET** `/api/loan-applications/`

List all loan applications with optional filtering.

**Parameters:**
- `status_filter`: Filter by status (uploaded, processing, completed, failed)
- `limit`: Maximum number of results (default: 100)
- `offset`: Number of records to skip (default: 0)

**Response:**
```json
{
  "total": 50,
  "applications": [...]
}
```

### 4. Get Application Matches

**GET** `/api/loan-applications/{application_id}/matches`

Get all match results for a specific application.

**Parameters:**
- `application_id`: ID of the application (path parameter)
- `status_filter`: Filter by match status (pending, processing, completed, failed)
- `min_score`: Minimum match score to filter by

**Response:**
```json
[
  {
    "id": 1,
    "lender_id": 10,
    "match_score": 85.5,
    "match_analysis": {
      "match_category": "very_good",
      "strengths": ["Good credit", "Stable income"],
      "weaknesses": ["Limited history"],
      "recommendations": ["Consider co-signer"],
      "criteria_scores": {...},
      "summary": "Very good match overall"
    },
    "status": "completed",
    "created_at": "2025-12-24T10:05:00Z"
  }
]
```

### 5. Delete Loan Application

**DELETE** `/api/loan-applications/{application_id}`

Delete a loan application and all its matches.

**Response:** 204 No Content

## Match Score Calculation

The match score is calculated by the LLM based on multiple criteria:

### Criteria (0-10 points each)

1. **Loan Amount** - Does the requested amount fit the lender's range?
2. **Loan Type** - Does the lender offer this type of loan?
3. **Interest Rate** - Are expectations aligned?
4. **Eligibility** - Does applicant meet requirements?
5. **Tenure** - Is the requested term available?
6. **Credit Profile** - Does credit score match criteria?
7. **Income** - Does income meet requirements?
8. **Documentation** - Can applicant provide required docs?
9. **Special Conditions** - Any special factors?
10. **Overall Fit** - General compatibility

### Score Ranges

- **90-100**: Excellent match (highly recommended)
- **75-89**: Very good match (recommended)
- **60-74**: Good match (suitable)
- **40-59**: Fair match (possible with conditions)
- **20-39**: Poor match (significant gaps)
- **0-19**: Very poor match (not recommended)

## Hatchet Workflow

The Hatchet workflow consists of three steps:

### Step 1: Prepare Matching
- Fetch all active lenders (status = COMPLETED)
- Create pending match records for each lender
- Update application status to PROCESSING

### Step 2: Calculate Matches (Parallel)
- For each lender, calculate match score in parallel
- Use LLM to analyze application against lender policy
- Update match records with scores and analysis
- Handle failures gracefully

### Step 3: Finalize Matching
- Update application status to COMPLETED
- Log success/failure counts

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Hatchet SDK
uv pip install hatchet-sdk>=0.30.0
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Hatchet Configuration
HATCHET_CLIENT_TOKEN=your_hatchet_token_here

# OpenAI for LLM (required for match scoring)
OPENAI_API_KEY=your_openai_key_here

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/kaaj
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start Services

```bash
# Terminal 1: Start API server
./start_api.sh

# Terminal 2: Start Hatchet worker (if using Hatchet)
python -m app.workflows.loan_matching_workflow

# Terminal 3: Start Celery worker (for lender processing)
./start_worker.sh
```

## Testing

### Run All Tests

```bash
./run_tests.sh
```

### Run Specific Test Suite

```bash
pytest tests/test_loan_application_upload.py -v
```

### Test Coverage

The test suite includes:
- ✅ Upload functionality
- ✅ OCR extraction (mocked)
- ✅ LLM processing (mocked)
- ✅ Match score calculation (mocked)
- ✅ Parallel processing simulation
- ✅ Error handling
- ✅ Data validation
- ✅ Filtering and retrieval

## Mock Mode

For development and testing without external services:

- **OCR**: Mocked to return sample text
- **LLM**: Mocked to return structured data
- **Hatchet**: Returns None (workflow not triggered)
- **Match Scores**: Mocked with realistic values

## Production Considerations

### Performance

- Parallel processing scales with number of lenders
- Each match calculation is independent
- Hatchet handles retries and failures

### Monitoring

- Track workflow run IDs for debugging
- Monitor match completion rates
- Alert on high failure rates

### Security

- Validate PDF files before processing
- Sanitize user inputs
- Implement rate limiting
- Use authentication/authorization

### Cost Optimization

- Cache lender data to reduce DB queries
- Batch similar applications
- Monitor OpenAI token usage
- Set reasonable timeouts

## Troubleshooting

### Issue: Workflow not triggering

**Solution:** Check HATCHET_CLIENT_TOKEN is set and Hatchet server is running

### Issue: Low match scores

**Solution:** Review lender policies and application data quality

### Issue: Slow processing

**Solution:** 
- Check OpenAI API response times
- Verify Hatchet worker is running
- Scale workers horizontally

### Issue: Failed matches

**Solution:**
- Check error_message in match records
- Verify lender has processed_data
- Ensure OpenAI API key is valid

## Future Enhancements

1. **Real-time Updates** - WebSocket notifications for match completion
2. **Batch Processing** - Process multiple applications at once
3. **Smart Matching** - Pre-filter lenders based on basic criteria
4. **Caching** - Cache match results for similar applications
5. **Analytics** - Dashboard for match statistics and trends
6. **Recommendations** - Suggest application improvements
7. **Document Verification** - Automated document validation
8. **Integration** - Connect with external credit bureaus

## API Examples

See `docs/API_EXAMPLES.md` for more detailed examples and use cases.

## Support

For issues or questions:
1. Check the logs in the API server and Hatchet worker
2. Review the test suite for examples
3. Consult the architecture documentation

