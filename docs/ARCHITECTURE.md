# Architecture

Low-Level Design (LLD) documentation for the Kaaj Loan Management System.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              KAAJ SYSTEM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐        ┌─────────────────────────────────────────────┐     │
│  │   React     │◄──────▶│              FastAPI Server                 │     │
│  │  Frontend   │  REST  │                                             │     │
│  │  :5173      │        │  ┌─────────────┐  ┌─────────────┐           │     │
│  └─────────────┘        │  │   Lender    │  │    Loan     │           │     │
│                         │  │   Routes    │  │   Routes    │           │     │
│                         │  └──────┬──────┘  └──────┬──────┘           │     │
│                         │         │                │                  │     │
│                         │         ▼                ▼                  │     │
│                         │  ┌─────────────────────────────────┐        │     │
│                         │  │           Services              │        │     │
│                         │  │  ┌─────┐  ┌─────┐  ┌─────────┐  │        │     │
│                         │  │  │ OCR │  │ LLM │  │  Match  │  │        │     │
│                         │  └──┴─────┴──┴─────┴──┴─────────┴──┘        │     │
│                         └──────────────────┬──────────────────────────┘     │
│                                            │                                │
│  ┌─────────────────────────────────────────┼─────────────────────────┐      │
│  │                    Hatchet Workflow     │                         │      │
│  │  ┌─────────────────────┐    ┌──────────▼──────────┐               │      │
│  │  │ Lender Processing   │    │  Loan Matching      │               │      │
│  │  │     Workflow        │    │    Workflow         │               │      │
│  │  └─────────────────────┘    └─────────────────────┘               │      │
│  └───────────────────────────────────────────────────────────────────┘      │
│                                            │                                │
│                         ┌──────────────────▼──────────────────┐             │
│                         │          PostgreSQL                 │             │
│                         │   ┌─────────┐  ┌─────────────────┐  │             │
│                         │   │ lenders │  │loan_applications│  │             │
│                         │   └─────────┘  ├─────────────────┤  │             │
│                         │                │  loan_matches   │  │             │
│                         │                └─────────────────┘  │             │
│                         └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Lender Service

The Lender Service handles the ingestion and processing of lender policy documents.

### 1.1 Data Model

```
┌────────────────────────────────────────────────────────────────┐
│                          LENDERS                               │
├────────────────────────────────────────────────────────────────┤
│  id               │ INTEGER      │ PK, Auto-increment          │
│  lender_name      │ VARCHAR(255) │ NOT NULL, Indexed           │
│  policy_details   │ JSON         │ User-provided policy info   │
│  raw_data         │ TEXT         │ OCR-extracted text          │
│  processed_data   │ JSON         │ LLM-structured data         │
│  status           │ ENUM         │ uploaded/processing/        │
│                   │              │ completed/failed            │
│  original_filename│ VARCHAR(500) │ Original PDF filename       │
│  created_by       │ VARCHAR(255) │ User identifier             │
│  created_at       │ TIMESTAMP    │ Auto-set on creation        │
│  updated_at       │ TIMESTAMP    │ Auto-updated on change      │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Status State Machine

```
                    ┌───────────┐
                    │           │
      PDF Upload    │ UPLOADED  │
      ─────────────▶│           │
                    └─────┬─────┘
                          │
                          │ Workflow triggered
                          ▼
                    ┌───────────┐
                    │           │
                    │PROCESSING │
                    │           │
                    └─────┬─────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
        ┌───────────┐           ┌───────────┐
        │           │           │           │
        │ COMPLETED │           │  FAILED   │
        │           │           │           │
        └───────────┘           └───────────┘
```

### 1.3 Upload Flow

```
┌────────┐     ┌────────────┐     ┌─────────────┐     ┌──────────┐
│ Client │────▶│ POST       │────▶│ OCR Service │────▶│ Extract  │
│        │     │ /upload    │     │             │     │ Text     │
└────────┘     └────────────┘     └─────────────┘     └────┬─────┘
                                                           │
     ┌─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│ Create      │────▶│ Trigger     │────▶│ Return Response │
│ DB Record   │     │ Workflow    │     │ (lender_id)     │
│ status=     │     │ (async)     │     │                 │
│ UPLOADED    │     │             │     │                 │
└─────────────┘     └─────────────┘     └─────────────────┘
```

### 1.4 Processing Workflow

```
Hatchet Workflow: lender-processing
Event: lender:document:uploaded

┌─────────────────────────────────────────────────────────────────┐
│  Task: process_lender_document                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Fetch Lender Record                                         │
│     └── Set status = PROCESSING                                 │
│                                                                 │
│  2. Call LLM Service                                            │
│     ├── Build extraction prompt                                 │
│     ├── Send to OpenAI GPT-4o-mini                              │
│     └── Parse JSON response                                     │
│                                                                 │
│  3. Validate & Enrich Data                                      │
│     ├── Check required fields                                   │
│     └── Calculate completeness score                            │
│                                                                 │
│  4. Update Database                                             │
│     ├── Save processed_data                                     │
│     └── Set status = COMPLETED                                  │
│                                                                 │
│  On Error:                                                      │
│     └── Set status = FAILED                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.5 LLM Extraction Schema

The LLM extracts and structures the following from lender policy PDFs:

```json
{
  "loan_types": ["personal", "home", "auto"],
  "interest_rates": { "min": "10.5%", "max": "15.0%" },
  "eligibility_criteria": ["Age 21-65", "Min income Rs. 25,000"],
  "loan_amount_range": { "min": "Rs. 50,000", "max": "Rs. 20,00,000" },
  "tenure": { "min": "12 months", "max": "60 months" },
  "processing_fees": "2% of loan amount",
  "documents_required": ["PAN Card", "Aadhaar Card", "Bank Statements"],
  "key_terms": ["Prepayment allowed after 6 months"],
  "contact_information": { "phone": "...", "email": "...", "website": "..." },
  "special_offers": ["0.5% discount for salaried employees"],
  "_metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 1234,
    "processing_successful": true
  },
  "_validation": {
    "field_completeness": { "loan_types": true, ... },
    "completeness_score": 0.85
  }
}
```

---

## 2. Loan Application Service

The Loan Application Service handles loan applications and matches them against lender policies.

### 2.1 Data Models

```
┌────────────────────────────────────────────────────────────────┐
│                     LOAN_APPLICATIONS                          │
├────────────────────────────────────────────────────────────────┤
│  id                │ INTEGER      │ PK, Auto-increment         │
│  applicant_name    │ VARCHAR(255) │ NOT NULL, Indexed          │
│  applicant_email   │ VARCHAR(255) │ Contact email              │
│  applicant_phone   │ VARCHAR(50)  │ Contact phone              │
│  application_details│ JSON        │ User-provided details      │
│  raw_data          │ TEXT         │ OCR-extracted text         │
│  processed_data    │ JSON         │ LLM-structured data        │
│  status            │ ENUM         │ uploaded/processing/       │
│                    │              │ completed/failed           │
│  workflow_run_id   │ VARCHAR(255) │ Hatchet tracking ID        │
│  original_filename │ VARCHAR(500) │ Original PDF filename      │
│  created_by        │ VARCHAR(255) │ User identifier            │
│  created_at        │ TIMESTAMP    │ Auto-set on creation       │
│  updated_at        │ TIMESTAMP    │ Auto-updated on change     │
└────────────────────────────────────────────────────────────────┘
                            │
                            │ 1:N
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                       LOAN_MATCHES                             │
├────────────────────────────────────────────────────────────────┤
│  id                │ INTEGER      │ PK, Auto-increment         │
│  loan_application_id│ INTEGER     │ FK → loan_applications.id  │
│  lender_id         │ INTEGER      │ FK → lenders.id            │
│  match_score       │ FLOAT        │ Score 0-100                │
│  match_analysis    │ JSON         │ Detailed breakdown         │
│  status            │ ENUM         │ pending/processing/        │
│                    │              │ completed/failed           │
│  error_message     │ TEXT         │ Error details if failed    │
│  created_at        │ TIMESTAMP    │ Auto-set on creation       │
│  updated_at        │ TIMESTAMP    │ Auto-updated on change     │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Entity Relationship Diagram

```
┌───────────────┐         ┌───────────────────┐         ┌───────────────┐
│    LENDERS    │         │   LOAN_MATCHES    │         │    LOAN_      │
│               │         │                   │         │ APPLICATIONS  │
├───────────────┤         ├───────────────────┤         ├───────────────┤
│ id (PK)       │◄────────┤ lender_id (FK)    │         │ id (PK)       │
│ lender_name   │    N    │ loan_app_id (FK)  │────────▶│ applicant_name│
│ processed_data│         │ match_score       │    N    │ processed_data│
│ status        │         │ match_analysis    │         │ status        │
└───────────────┘         │ status            │         └───────────────┘
                          └───────────────────┘
```

### 2.3 Upload Flow

```
┌────────┐     ┌────────────┐     ┌─────────────┐     ┌──────────┐
│ Client │────▶│ POST       │────▶│ OCR Service │────▶│ Extract  │
│        │     │ /upload    │     │             │     │ Text     │
└────────┘     └────────────┘     └─────────────┘     └────┬─────┘
                                                           │
     ┌─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│ Create      │────▶│ Trigger     │────▶│ Return Response │
│ DB Record   │     │ Loan Match  │     │ (application_id)│
│ status=     │     │ Workflow    │     │                 │
│ UPLOADED    │     │ (async)     │     │                 │
└─────────────┘     └─────────────┘     └─────────────────┘
```

### 2.4 Matching Workflow (4-Step DAG)

```
Hatchet Workflow: loan-matching
Event: loan:application:uploaded

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   Step 1: process_application_data                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  • Call LLM to extract structured data from raw OCR text            │   │
│   │  • Extract: loan_type, amount, employment, income, credit score     │   │
│   │  • Save processed_data to database                                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│   Step 2: prepare_matching                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  • Fetch all lenders with status = COMPLETED                        │   │
│   │  • Create LoanMatch records for each lender (status = PENDING)      │   │
│   │  • Update application status = PROCESSING                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│   Step 3: calculate_matches (PARALLEL)                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                                                                     │   │
│   │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐         │   │
│   │   │ Lender 1 │   │ Lender 2 │   │ Lender 3 │   │ Lender N │         │   │
│   │   │  Match   │   │  Match   │   │  Match   │   │  Match   │         │   │
│   │   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘         │   │
│   │        │              │              │              │               │   │
│   │        └──────────────┴──────────────┴──────────────┘               │   │
│   │                              │                                      │   │
│   │                    asyncio.gather()                                 │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│   Step 4: finalize_matching                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  • Aggregate results                                                │   │
│   │  • Update application status = COMPLETED                            │   │
│   │  • Log success/failure counts                                       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.5 Match Calculation

For each lender, the LLM evaluates 10 criteria:

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATCH SCORING CRITERIA                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Criteria              │ Weight  │ Description                 │
│   ──────────────────────┼─────────┼─────────────────────────────│
│   loan_amount           │  10%    │ Amount within range?        │
│   loan_type             │  10%    │ Type offered by lender?     │
│   interest_rate         │  10%    │ Rates align with needs?     │
│   eligibility           │  10%    │ Meets basic criteria?       │
│   tenure                │  10%    │ Tenure options match?       │
│   credit_profile        │  10%    │ Credit score acceptable?    │
│   income                │  10%    │ Income requirements met?    │
│   documentation         │  10%    │ Can provide documents?      │
│   special_conditions    │  10%    │ Any special requirements?   │
│   overall_fit           │  10%    │ General compatibility       │
│   ──────────────────────┼─────────┼─────────────────────────────│
│   TOTAL                 │  100%   │ Final match score           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.6 Match Score Categories

| Score Range | Category | Recommendation |
|-------------|----------|----------------|
| 90-100 | Excellent | Highly recommended |
| 75-89 | Very Good | Recommended |
| 60-74 | Good | Suitable |
| 40-59 | Fair | Possible with conditions |
| 20-39 | Poor | Significant gaps |
| 0-19 | Very Poor | Not recommended |

### 2.7 Match Analysis Schema

```json
{
  "match_score": 78,
  "match_category": "very_good",
  "strengths": [
    "Income exceeds minimum requirements",
    "Loan amount within lender's range"
  ],
  "weaknesses": [
    "Credit score slightly below preferred threshold"
  ],
  "recommendations": [
    "Consider providing additional income documentation",
    "May qualify for better rates after 6 months"
  ],
  "criteria_scores": {
    "loan_amount": 9,
    "loan_type": 10,
    "interest_rate": 7,
    "eligibility": 8,
    "tenure": 8,
    "credit_profile": 6,
    "income": 9,
    "documentation": 8,
    "special_conditions": 7,
    "overall_fit": 8
  },
  "summary": "Strong application with good income and appropriate loan size. Minor concerns about credit history that may affect interest rates.",
  "_metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 856,
    "application_id": 1,
    "lender_id": 3,
    "calculation_successful": true
  }
}
```

---

## 3. Service Layer

### 3.1 OCR Service

```
┌─────────────────────────────────────────────────────────────────┐
│                        OCR SERVICE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: PDF bytes                                               │
│                                                                 │
│  Processing Pipeline:                                           │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐      │
│  │ PyMuPDF │──▶│ Render  │──▶│  PIL    │──▶│  Tesseract  │      │
│  │  Open   │   │ @ 300   │   │  Image  │   │    OCR      │      │
│  │   PDF   │   │   DPI   │   │         │   │             │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────────┘      │
│                                                   │             │
│  Output: Concatenated text from all pages         │             │
│  ◄────────────────────────────────────────────────┘             │
│                                                                 │
│  Format:                                                        │
│  --- Page 1 ---                                                 │
│  [OCR text...]                                                  │
│                                                                 │
│  --- Page 2 ---                                                 │
│  [OCR text...]                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 LLM Service

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLM SERVICE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Model: gpt-4o-mini                                             │
│  Temperature: 0.2 (deterministic)                               │
│  Response Format: JSON object                                   │
│                                                                 │
│  Methods:                                                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  process_raw_text(raw_text, lender_name)                │    │
│  │  └── Extract lender policy information                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  process_loan_application(raw_text, applicant_name)     │    │
│  │  └── Extract loan application information               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  validate_and_enrich_data(processed_data, raw_text)     │    │
│  │  └── Add completeness scores and validation flags       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Match Service

```
┌─────────────────────────────────────────────────────────────────┐
│                       MATCH SERVICE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input:                                                         │
│  • application_data (JSON)                                      │
│  • lender_data (JSON)                                           │
│  • lender_name                                                  │
│                                                                 │
│  Process:                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  1. Build comparison prompt with both datasets          │    │
│  │  2. Send to OpenAI with JSON response format            │    │
│  │  3. Parse match analysis response                       │    │
│  │  4. Return score (0-100) and detailed breakdown         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Output:                                                        │
│  • match_score: float (0-100)                                   │
│  • match_analysis: dict (strengths, weaknesses, etc.)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Configuration

### 4.1 Connection Pools

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE ENGINES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  engine (Async)          - FastAPI routes                       │
│  ├── Pool Size: 10                                              │
│  └── Max Overflow: 20                                           │
│                                                                 │
│  task_engine (Async)     - Background tasks                     │
│  ├── Pool Size: 5                                               │
│  └── Max Overflow: 10                                           │
│                                                                 │
│  workflow_engine (Async) - Hatchet workers                      │
│  ├── Pool Size: 5                                               │
│  └── Max Overflow: 10                                           │
│                                                                 │
│  sync_engine             - Alembic migrations                   │
│  └── Standard sync connection                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Connection Strings

```
Async (FastAPI/Workers):  postgresql+asyncpg://user:pass@host:5432/kaaj
Sync (Alembic):           postgresql+psycopg://user:pass@host:5432/kaaj
```

---

## 5. API Layer

### 5.1 Lender Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| `POST` | `/api/lenders/upload` | `upload_pdf_document` | Upload & OCR PDF |
| `GET` | `/api/lenders/` | `list_lenders` | List with filtering |
| `GET` | `/api/lenders/{id}` | `get_lender` | Get single lender |
| `DELETE` | `/api/lenders/{id}` | `delete_lender` | Delete lender |

### 5.2 Loan Application Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| `POST` | `/api/loan-applications/upload` | `upload_loan_application` | Upload & process |
| `GET` | `/api/loan-applications/` | `list_loan_applications` | List with filtering |
| `GET` | `/api/loan-applications/{id}` | `get_loan_application` | Get with matches |
| `GET` | `/api/loan-applications/{id}/matches` | `get_application_matches` | Get match list |
| `DELETE` | `/api/loan-applications/{id}` | `delete_loan_application` | Delete cascade |

---

## 6. Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     REACT FRONTEND                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐        │
│  │    Pages    │────▶│   Hooks     │────▶│     API     │        │
│  │             │     │ (TanStack   │     │   Service   │        │
│  │ - Lenders   │     │   Query)    │     │             │        │
│  │ - LoanApps  │     │             │     │ - lenderApi │        │
│  └─────────────┘     └─────────────┘     │ - loanApi   │        │
│        │                                  └──────┬──────┘       │
│        ▼                                         │              │
│  ┌─────────────┐                                 │              │
│  │ Components  │                                 ▼              │
│  │             │                          ┌─────────────┐       │
│  │ - FileUpload│                          │   Axios     │       │
│  │ - StatusBadge                          │             │       │
│  │ - Layout    │                          │ baseURL:    │       │
│  │ - Spinner   │                          │ :8000       │       │
│  └─────────────┘                          └─────────────┘       │
│                                                                 │
│  Auto-refresh: 5 seconds polling                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Hatchet Workflow Orchestration

### 7.1 Worker Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│                     HATCHET WORKER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Worker Name: kaaj-worker                                       │
│                                                                 │
│  Registered Workflows:                                          │
│  ├── lender-processing                                          │
│  │   └── Event: lender:document:uploaded                        │
│  │                                                              │
│  └── loan-matching                                              │
│      └── Event: loan:application:uploaded                       │
│                                                                 │
│  Execution:                                                     │
│  $ python app/workflows/worker.py                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Workflow Triggers

```python
# Lender processing (from lender_routes.py)
lender_processing_workflow.run_no_wait(
    LenderProcessingInput(lender_id=lender.id)
)

# Loan matching (from loan_application_routes.py)
loan_matching_workflow.run_no_wait(
    ProcessApplicationDataInput(
        application_id=application.id,
        raw_text=raw_text,
        applicant_name=applicant_name
    )
)
```

---

## 8. Error Handling

### 8.1 API Error Responses

| Status | Condition |
|--------|-----------|
| 400 | Invalid file type, empty PDF, invalid status filter |
| 404 | Lender/Application not found |
| 500 | OCR failure, database error, workflow trigger failure |

### 8.2 Workflow Failure Handling

- Status updated to `FAILED` on any exception
- Error messages stored in `error_message` column (for matches)
- Workflow continues for other lenders on individual match failures
- Results aggregated with success/failure counts

