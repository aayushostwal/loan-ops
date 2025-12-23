# 🏗️ Architecture & Implementation Guide

Complete technical documentation for the Kaaj Lender Document Processing System, covering system architecture, implementation details, and deployment strategies.

---

## Table of Contents

1. [Implementation Overview](#implementation-overview)
2. [Project Structure](#project-structure)
3. [Component Architecture](#component-architecture)
4. [Data Flow & Processing](#data-flow--processing)
5. [Technology Stack](#technology-stack)
6. [Design Patterns](#design-patterns)
7. [Implemented Features](#implemented-features)
8. [Scalability & Performance](#scalability--performance)
9. [Security Considerations](#security-considerations)
10. [Monitoring & Logging](#monitoring--logging)
11. [Testing Strategy](#testing-strategy)
12. [Deployment](#deployment)
13. [Future Enhancements](#future-enhancements)

---

## Implementation Overview

Successfully implemented a production-ready **Lender Document Processing System** with:

- 📄 **PDF Upload & OCR** - Extract text from documents using Tesseract
- 🤖 **LLM Processing** - Convert raw text to structured data using OpenAI GPT
- ⚡ **Async Workers** - Background processing with Celery + Redis
- 🔌 **RESTful API** - Complete CRUD operations with FastAPI
- 📊 **Status Tracking** - Real-time processing status updates
- 📝 **Comprehensive Logging** - Debug and monitor easily
- 🗄️ **PostgreSQL** - Robust data storage with async support

---

## Project Structure

```
kaaj/
├── app/
│   ├── models/
│   │   ├── __init__.py           # Models package exports
│   │   └── lender.py             # Lender model with LenderStatus enum
│   ├── services/
│   │   ├── __init__.py           # Services package exports
│   │   ├── ocr_service.py        # OCR text extraction service
│   │   └── llm_service.py        # LLM processing service
│   ├── routers/
│   │   ├── __init__.py           # Routers package exports
│   │   └── lender_routes.py      # Lender API endpoints
│   ├── tasks/
│   │   ├── __init__.py           # Tasks package exports
│   │   └── lender_tasks.py       # Celery async tasks
│   ├── db.py                     # Database configuration
│   ├── main.py                   # FastAPI application entry point
│   ├── celery_app.py             # Celery configuration
│   └── models.py                 # SQLAlchemy base
├── alembic/
│   ├── versions/
│   │   ├── 2118a2715dde_init.py           # Initial migration
│   │   └── 3a4b5c6d7e8f_add_lender_model.py  # Lender model migration
│   ├── env.py                    # Alembic environment config
│   └── script.py.mako            # Migration template
├── docs/
│   ├── SETUP.md                  # Setup instructions
│   ├── ARCHITECTURE.md           # This file
│   └── API_EXAMPLES.md           # API usage examples
├── alembic.ini                   # Alembic configuration
├── pyproject.toml                # Project dependencies (UV)
├── env.example                   # Environment variables template
├── start_api.sh                  # API server startup script
├── start_worker.sh               # Celery worker startup script
└── README.md                     # Main documentation
```

---

## Component Architecture

### 1. Models Layer (`app/models/`)

**Purpose:** Database models using SQLAlchemy ORM

#### Lender Model (`lender.py`)

**Database Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key (auto-increment) |
| `lender_name` | String(255) | Name of the lender organization |
| `policy_details` | JSON | Structured policy information |
| `raw_data` | Text | Raw OCR-extracted text from PDF |
| `processed_data` | JSON | LLM-processed structured data |
| `status` | Enum | Processing status |
| `created_by` | String(255) | User who uploaded the document |
| `created_at` | DateTime | Record creation timestamp (auto) |
| `updated_at` | DateTime | Last update timestamp (auto) |
| `original_filename` | String(500) | Original PDF filename |

**Status Enum Values:**
- `UPLOADED`: Initial state after PDF upload
- `PROCESSING`: Being processed by async worker
- `COMPLETED`: Processing successful
- `FAILED`: Processing failed

**Features:**
- ✅ Database indexes on `id`, `lender_name`, and `status`
- ✅ Comprehensive field comments
- ✅ Timezone-aware timestamps
- ✅ SQLAlchemy ORM with async support
- ✅ Type hints throughout

### 2. Services Layer (`app/services/`)

**Purpose:** Business logic and external service integrations

#### OCR Service (`ocr_service.py`)

Handles PDF to text conversion using Tesseract OCR.

**Key Methods:**
- `extract_text_from_pdf(pdf_bytes, dpi=300, language='eng')`: Main PDF processing
  - Converts PDF to images (one per page)
  - Applies OCR to each image
  - Returns formatted text with page markers
- `extract_text_from_image(image_bytes, language='eng')`: Single image processing
- `validate_tesseract_installation()`: Check Tesseract availability

**Dependencies:**
- `pytesseract`: Tesseract OCR wrapper
- `pdf2image`: PDF to image conversion
- `Pillow (PIL)`: Image processing

**Features:**
- ✅ Multi-page PDF support
- ✅ Configurable DPI and language settings
- ✅ Page-by-page text extraction with markers
- ✅ Comprehensive error handling
- ✅ Detailed logging at every step

#### LLM Service (`llm_service.py`)

Processes raw OCR text into structured data using OpenAI GPT.

**Key Methods:**
- `process_raw_text(raw_text, lender_name, policy_details)`: Main processing
- `validate_and_enrich_data(processed_data, raw_text)`: Data validation
- `_build_processing_prompt(raw_text, lender_name)`: Prompt engineering

**Extraction Targets:**
- Loan types offered
- Interest rates and ranges
- Eligibility criteria
- Loan amount ranges
- Tenure options
- Processing fees
- Required documents
- Key terms and conditions
- Contact information
- Special offers and promotions

**Configuration:**
- Model: `gpt-4o-mini` (configurable)
- Temperature: `0.2` (low for deterministic output)
- Response format: JSON
- Token usage tracking

**Features:**
- ✅ Structured data extraction from raw text
- ✅ JSON response format
- ✅ Comprehensive prompt engineering
- ✅ Token usage tracking and metadata
- ✅ Data validation and enrichment
- ✅ Completeness scoring

### 3. Routers Layer (`app/routers/`)

**Purpose:** API endpoint definitions using FastAPI

#### Lender Routes (`lender_routes.py`)

FastAPI router for lender document management.

**API Endpoints:**

| Method | Path | Description | Status Codes |
|--------|------|-------------|--------------|
| POST | `/api/lenders/upload` | Upload PDF and trigger processing | 201, 400, 500 |
| GET | `/api/lenders/{id}` | Get specific lender by ID | 200, 404, 500 |
| GET | `/api/lenders/` | List all lenders (with filters) | 200, 500 |
| DELETE | `/api/lenders/{id}` | Delete lender record | 204, 404, 500 |

**Request/Response Models:**
- `LenderResponse`: Single lender data with all fields
- `LenderListResponse`: Paginated lender list with total count
- `UploadResponse`: Upload confirmation with lender_id and task_id

**Features:**
- ✅ Multipart form-data support for file uploads
- ✅ PDF file validation
- ✅ Pydantic models for request/response validation
- ✅ Async database sessions
- ✅ Comprehensive error handling
- ✅ Proper HTTP status codes
- ✅ Pagination support (limit, offset)
- ✅ Status filtering
- ✅ Detailed logging

### 4. Tasks Layer (`app/tasks/`)

**Purpose:** Async background task processing using Celery

#### Lender Tasks (`lender_tasks.py`)

**Main Task:** `process_lender_document(lender_id)`

**Processing Workflow:**
1. Fetch lender record from database
2. Update status to `PROCESSING`
3. Call LLM service to process raw text
4. Validate and enrich processed data
5. Update database with structured results
6. Set final status (`COMPLETED` or `FAILED`)

**Error Handling:**
- Automatic retry (up to 3 attempts)
- 60-second retry delay between attempts
- Status update on failure
- Comprehensive error logging
- Task time limits (5 minutes hard, 4 minutes soft)

**Features:**
- ✅ Celery integration with Redis backend
- ✅ Automatic task retry mechanism
- ✅ Status tracking throughout workflow
- ✅ Comprehensive error handling
- ✅ Detailed logging of all operations

### 5. Configuration Files

#### Database Configuration (`db.py`)

Dual-engine setup for different use cases:
- **Async engine**: For FastAPI using `asyncpg`
- **Sync engine**: For Alembic migrations using `psycopg`

#### Celery Configuration (`celery_app.py`)

**Settings:**
- Broker: Redis
- Result backend: Redis
- Task time limit: 5 minutes (hard)
- Soft time limit: 4 minutes
- Serializer: JSON
- Timezone: UTC
- Task tracking: Enabled

#### FastAPI Application (`main.py`)

- Router inclusion
- API metadata configuration
- Health check endpoint
- Comprehensive logging setup

---

## Data Flow & Processing

### Upload and Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT UPLOADS PDF                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  POST /api/lenders/upload                                    │
│  - Validate PDF file (type, size)                           │
│  - Extract text using OCR (Tesseract)                        │
│  - Save raw data to database (status: UPLOADED)             │
│  - Trigger Celery task                                       │
│  - Return lender_id + task_id                                │
└───────────────────────────┬─────────────────────────────────┘
                            │ (API returns immediately)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CELERY WORKER (Background Processing)                       │
│  - Fetch lender record                                       │
│  - Update status: PROCESSING                                 │
│  - Call LLM service with raw text                            │
│  - Extract structured data (JSON)                            │
│  - Validate and enrich data                                  │
│  - Save processed_data to database                           │
│  - Update status: COMPLETED                                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CLIENT QUERIES RESULT                                       │
│  GET /api/lenders/{id}                                       │
│  - Returns full data including processed_data                │
│  - Status indicates completion state                         │
└─────────────────────────────────────────────────────────────┘
```

### Error Flow

```
┌─────────────────────────┐
│   Error in OCR          │
│   (During Upload)       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Return HTTP 500        │
│  No DB record created   │
└─────────────────────────┘

┌─────────────────────────┐
│  Error in LLM           │
│  (During Processing)    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Update status: FAILED  │
│  Log error details      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Retry task             │
│  (up to 3 attempts)     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  If retries exhausted:  │
│  Status remains FAILED  │
└─────────────────────────┘
```

---

## Technology Stack

### Core Framework
- **FastAPI** - Modern async web framework with automatic API docs
- **SQLAlchemy 2.0** - ORM with comprehensive async support
- **Alembic** - Database migrations and version control
- **Pydantic** - Data validation and serialization
- **Python 3.9+** - Modern Python with type hints

### Processing & AI
- **Tesseract OCR** - Open-source text extraction from images
- **pdf2image** - PDF to image conversion using Poppler
- **OpenAI GPT-4** - Natural language processing and structuring
- **Pillow (PIL)** - Image processing and manipulation

### Task Queue & Caching
- **Celery** - Distributed task queue for async processing
- **Redis** - Message broker and result backend

### Database
- **PostgreSQL** - Primary relational database
- **asyncpg** - Async PostgreSQL driver for FastAPI
- **psycopg** - Sync PostgreSQL driver for Alembic

### Development Tools
- **UV** - Fast Python package manager
- **Black** - Code formatter
- **MyPy** - Static type checker
- **Pytest** - Testing framework

---

## Design Patterns

### 1. Service Layer Pattern

Business logic is encapsulated in service classes (`OCRService`, `LLMService`) separate from API routes.

**Benefits:**
- Reusability across different endpoints
- Easier unit testing
- Clear separation of concerns
- Simplified maintenance

**Example:**
```python
# Service can be used from anywhere
ocr_service = OCRService()
text = await ocr_service.extract_text_from_pdf(pdf_bytes)
```

### 2. Repository Pattern

Database operations are abstracted through SQLAlchemy models, providing a clean interface for data access.

**Benefits:**
- Database-agnostic code
- Easier testing with mocks
- Consistent data access patterns

### 3. Async/Await Pattern

Used throughout for non-blocking I/O operations, maximizing throughput.

**Benefits:**
- High concurrency
- Efficient resource utilization
- Better scalability

### 4. Task Queue Pattern

Long-running operations are offloaded to Celery workers, keeping the API responsive.

**Benefits:**
- API remains fast and responsive
- Scalable processing with multiple workers
- Automatic retries and error handling
- Task prioritization and scheduling

---

## Implemented Features

### ✅ Complete Feature List

#### 1. Lender Model
- Primary key with auto-increment
- Lender name with indexing
- JSON fields for policy and processed data
- Text field for raw OCR data
- Status enum with 4 states
- Audit fields (created_by, created_at, updated_at)
- Original filename tracking
- Comprehensive field comments

#### 2. OCR Service
- PDF to image conversion
- Multi-page PDF support
- Tesseract OCR integration
- Configurable DPI (default: 300)
- Multi-language support
- Page markers in output
- Error handling and validation
- Installation verification

#### 3. LLM Service
- OpenAI GPT-4 integration
- Structured prompt engineering
- JSON response parsing
- Token usage tracking
- Data validation and enrichment
- Completeness scoring
- Configurable model and temperature
- Comprehensive error handling

#### 4. Async Worker System
- Celery task queue
- Redis backend
- Automatic retries (3 attempts)
- 60-second retry delay
- Status tracking
- Time limits (5 min hard, 4 min soft)
- Comprehensive logging

#### 5. RESTful API
- PDF upload endpoint
- Get lender by ID
- List lenders with pagination
- Status filtering
- Delete lender
- Pydantic validation
- Async database operations
- Proper HTTP status codes

#### 6. Database Integration
- PostgreSQL with async support
- Alembic migrations
- Dual-engine setup
- JSON field support
- Enum types
- Timezone-aware timestamps
- Connection pooling

#### 7. Documentation
- Setup guide (SETUP.md)
- Architecture documentation (this file)
- API examples (API_EXAMPLES.md)
- Environment template (env.example)
- Helper scripts (start_api.sh, start_worker.sh)

---

## Scalability & Performance

### Horizontal Scaling

#### API Servers
```bash
# Run multiple API instances behind a load balancer
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Gunicorn with Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### Celery Workers
```bash
# Run multiple workers on different machines
celery -A app.celery_app worker --loglevel=info --concurrency=4

# Run specialized workers for different queues
celery -A app.celery_app worker -Q high_priority --concurrency=2
```

### Vertical Scaling

#### Database Optimization
- Add read replicas for query load distribution
- Connection pooling (already configured in SQLAlchemy)
- Query optimization with indexes
- Partitioning for large tables

#### Redis Optimization
- Redis Cluster for high availability
- Sentinel for automatic failover
- Separate instances for different purposes

### Performance Optimization

#### OCR Processing
- **DPI Adjustment**: Lower DPI = faster, higher DPI = more accurate
- **Parallel Page Processing**: Process multiple pages simultaneously
- **Document Caching**: Cache results for duplicate documents
- **Image Pre-processing**: Enhance image quality before OCR

#### LLM Processing
- **Response Caching**: Cache results for similar documents
- **Batch Processing**: Process multiple documents in one API call
- **Streaming**: Use streaming for large documents
- **Prompt Optimization**: Refine prompts for faster processing

#### Database Performance
- **Index Optimization**: Indexes on frequently queried fields
- **Query Batching**: Fetch related data in single queries
- **Connection Pooling**: Reuse database connections
- **Materialized Views**: Pre-compute complex queries

---

## Security Considerations

### API Security

#### Authentication & Authorization
- **Implement JWT/OAuth2**: Add authentication middleware
- **API Keys**: For service-to-service communication
- **Rate Limiting**: Prevent abuse and DDoS attacks
- **CORS Configuration**: Restrict cross-origin requests

#### Input Validation
- **File Type Validation**: Already implemented (PDF only)
- **File Size Limits**: Prevent resource exhaustion
- **JSON Schema Validation**: Validate all JSON inputs
- **SQL Injection Prevention**: Using ORM (protected by default)

### Data Security

#### At Rest
- **Database Encryption**: Encrypt sensitive fields
- **File Storage**: Store PDFs in encrypted storage (S3/MinIO)
- **Backup Encryption**: Encrypt database backups

#### In Transit
- **HTTPS/TLS**: Use SSL certificates in production
- **Redis TLS**: Secure Redis connections
- **Database SSL**: Encrypt database connections

#### Application Security
- **Environment Variables**: Store secrets in `.env` (not in code)
- **Secret Management**: Use services like AWS Secrets Manager
- **Input Sanitization**: Sanitize all user inputs
- **Dependency Scanning**: Regularly update and scan dependencies

### Infrastructure Security

#### Network Security
- **Firewall Rules**: Restrict access to services
- **VPC/Network Isolation**: Isolate workers and databases
- **Bastion Hosts**: Secure access to production servers

#### Monitoring & Auditing
- **Access Logs**: Log all API access
- **Audit Trail**: Track all database changes
- **Anomaly Detection**: Monitor for unusual patterns
- **Security Alerts**: Set up alerts for security events

---

## Monitoring & Logging

### Logging Implementation

All components use Python's `logging` module with structured logs.

**Log Format:**
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**Log Levels:**
- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems

**What's Logged:**
- ✅ Request/response details
- ✅ OCR processing duration and character count
- ✅ LLM API calls and token usage
- ✅ Task start/completion/failure
- ✅ Database operations
- ✅ Error stack traces

### Recommended Log Aggregation

#### ELK Stack (Elasticsearch, Logstash, Kibana)
```yaml
# Centralized logging with powerful search
- Elasticsearch: Store and search logs
- Logstash: Collect and process logs
- Kibana: Visualize and analyze logs
```

#### Grafana Loki
```yaml
# Lightweight log aggregation
- Efficient storage
- Integration with Grafana
- Label-based indexing
```

#### Cloud Solutions
- **AWS CloudWatch**: For AWS deployments
- **Google Cloud Logging**: For GCP deployments
- **Datadog**: Multi-cloud monitoring

### Metrics to Monitor

#### Application Metrics
- API response times (p50, p95, p99)
- Request rate and error rate
- OCR processing duration
- LLM API latency and token usage
- Celery queue length
- Task success/failure rates
- Worker utilization

#### Infrastructure Metrics
- CPU and memory usage
- Database connections and query performance
- Redis memory usage and command rate
- Disk I/O and network bandwidth
- Error rates by endpoint

### Health Checks

#### API Health
```bash
# Basic health check
GET /health

# Detailed health check (custom endpoint)
GET /health/detailed
```

#### Celery Workers
```bash
# Check active tasks
celery -A app.celery_app inspect active

# Check registered tasks
celery -A app.celery_app inspect registered

# Check worker stats
celery -A app.celery_app inspect stats
```

#### Dependencies
- Database connectivity
- Redis availability
- Tesseract installation
- OpenAI API access

---

## Testing Strategy

### Unit Tests

Test individual components in isolation.

**What to Test:**
- Service layer methods (OCR, LLM)
- Model validation and business logic
- Utility functions
- Data transformation functions

**Example:**
```python
# tests/unit/test_ocr_service.py
async def test_extract_text_from_pdf():
    ocr_service = OCRService()
    text = await ocr_service.extract_text_from_pdf(sample_pdf_bytes)
    assert len(text) > 0
    assert "Page 1" in text
```

### Integration Tests

Test how components work together.

**What to Test:**
- API endpoints with database
- Celery tasks with services
- Database operations
- External service integrations

**Example:**
```python
# tests/integration/test_lender_routes.py
async def test_upload_pdf(client):
    response = await client.post(
        "/api/lenders/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"lender_name": "Test Bank"}
    )
    assert response.status_code == 201
    assert "lender_id" in response.json()
```

### End-to-End Tests

Test complete user workflows.

**What to Test:**
- Full upload to processing flow
- Error scenarios and retries
- Status transitions
- Data consistency

**Example Test Structure:**
```
tests/
├── unit/
│   ├── test_ocr_service.py
│   ├── test_llm_service.py
│   └── test_models.py
├── integration/
│   ├── test_lender_routes.py
│   ├── test_lender_tasks.py
│   └── test_database.py
├── e2e/
│   └── test_full_workflow.py
└── conftest.py  # Shared fixtures
```

---

## Deployment

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install uv && uv sync

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/kaaj
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./app:/app/app

  worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/kaaj
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=kaaj
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Cloud Deployment

#### AWS Deployment
- **Compute**: ECS/Fargate for containers
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis
- **Storage**: S3 for PDF storage
- **Load Balancer**: ALB for API servers

#### Google Cloud Deployment
- **Compute**: Cloud Run or GKE
- **Database**: Cloud SQL PostgreSQL
- **Cache**: Memorystore Redis
- **Storage**: Cloud Storage

#### Kubernetes Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kaaj-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kaaj-api
  template:
    metadata:
      labels:
        app: kaaj-api
    spec:
      containers:
      - name: api
        image: kaaj:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: kaaj-secrets
              key: database-url
```

---

## Future Enhancements

### Potential Features

1. **Multi-language OCR Support**
   - Support for Hindi, Tamil, Bengali, etc.
   - Automatic language detection
   - Multi-lingual document processing

2. **Batch Processing**
   - Upload multiple PDFs at once
   - Bulk import from cloud storage
   - Parallel processing of batches

3. **Document Comparison**
   - Compare policies across lenders
   - Highlight differences
   - Generate comparison reports

4. **Webhooks**
   - Notify clients when processing completes
   - Custom callback URLs
   - Retry mechanism for failed webhooks

5. **File Storage**
   - Store original PDFs in S3/MinIO
   - Generate presigned URLs
   - Automatic file cleanup

6. **Advanced Search**
   - Full-text search on processed data
   - Elasticsearch integration
   - Faceted search and filters

7. **Analytics Dashboard**
   - Visualize lender data trends
   - Processing statistics
   - Performance metrics

8. **Export Functionality**
   - Export to Excel/CSV
   - PDF report generation
   - Custom export templates

9. **Version Control**
   - Track changes to lender policies
   - Document history
   - Diff viewing

10. **API Rate Limiting**
    - Prevent abuse
    - Tiered access levels
    - Usage quotas

### Technical Improvements

1. **Caching Layer**
   - Redis for frequently accessed data
   - Response caching for GET requests
   - Distributed cache invalidation

2. **GraphQL API**
   - Alternative to REST
   - Flexible queries
   - Real-time subscriptions

3. **WebSocket Support**
   - Real-time processing updates
   - Live status notifications
   - Bidirectional communication

4. **Microservices Architecture**
   - Split OCR service
   - Separate LLM service
   - Independent scaling

5. **Container Orchestration**
   - Kubernetes deployment
   - Auto-scaling
   - Self-healing

6. **CI/CD Pipeline**
   - Automated testing
   - Continuous deployment
   - Rollback capabilities

---

## Contributing Guidelines

1. **Follow PEP 8** style guide for Python code
2. **Add type hints** to all function signatures
3. **Write docstrings** for all public methods and classes
4. **Add logging statements** for important operations
5. **Create tests** for new features
6. **Update documentation** when adding features
7. **Run linters** before committing:
   ```bash
   uv run black .
   uv run mypy .
   ```

---

## Quick Reference

### Key Highlights

✅ **Type hints** throughout all modules  
✅ **Docstrings** for all classes and methods  
✅ **Comprehensive comments** explaining complex logic  
✅ **No linter errors** - clean code  
✅ **Modular design** - easy to extend  
✅ **Async/await** throughout  
✅ **Background processing** for long tasks  
✅ **Comprehensive logging** - debug easily  
✅ **Production-ready** - deploy with confidence  

### Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Setup environment
cp env.example .env

# 3. Run migrations
uv run alembic upgrade head

# 4. Start services
uv run fastapi dev app/main.py  # Terminal 1
uv run celery -A app.celery_app worker --loglevel=info  # Terminal 2
```

---

For setup instructions, see [SETUP.md](./SETUP.md)  
For API examples, see [API_EXAMPLES.md](./API_EXAMPLES.md)  
For the main overview, see [README.md](../README.md)
