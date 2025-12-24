# Kaaj - Loan Management System

A modern loan management platform that automates lender policy processing and loan application matching using OCR, LLM, and parallel workflow orchestration.

## Overview

Kaaj streamlines the loan matching process by:
- **Extracting** policy data from lender PDF documents using OCR
- **Processing** extracted text with LLMs to create structured policy profiles
- **Matching** loan applications against lender policies in parallel
- **Scoring** applications with detailed match analysis

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Lender     │────▶│     OCR      │────▶│     LLM      │
│   PDF        │     │   Extract    │     │   Process    │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Loan      │────▶│   Parallel   │◀────│   Lender     │
│ Application  │     │   Matching   │     │   Profiles   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Match     │
                     │   Scores     │
                     └──────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | FastAPI (async Python) |
| **Database** | PostgreSQL + SQLAlchemy |
| **Workflows** | Hatchet (parallel task orchestration) |
| **OCR** | Tesseract + PyMuPDF |
| **LLM** | OpenAI GPT-4o-mini |
| **Frontend** | React + TypeScript + TailwindCSS |
| **Package Manager** | uv (Python) / npm (Frontend) |

## Quick Start

```bash
# 1. Clone and setup environment
cp env.example .env
# Edit .env with your API keys

# 2. Setup database
createdb kaaj
uv run alembic upgrade head

# 3. Start services (in separate terminals)
./start_api.sh      # API Server → http://localhost:8000
./start_worker.sh   # Hatchet Worker
./start_frontend.sh # Frontend → http://localhost:5173
```

## Documentation

| Document | Description |
|----------|-------------|
| [**Architecture**](./docs/ARCHITECTURE.md) | System design, data models, workflow diagrams |
| [**Setup Guide**](./docs/SETUP.md) | Detailed installation and configuration |

## API Endpoints

### Lenders
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/lenders/upload` | Upload lender policy PDF |
| `GET` | `/api/lenders/` | List all lenders |
| `GET` | `/api/lenders/{id}` | Get lender details |
| `DELETE` | `/api/lenders/{id}` | Delete lender |

### Loan Applications
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/loan-applications/upload` | Upload loan application PDF |
| `GET` | `/api/loan-applications/` | List all applications |
| `GET` | `/api/loan-applications/{id}` | Get application with matches |
| `GET` | `/api/loan-applications/{id}/matches` | Get match scores |
| `DELETE` | `/api/loan-applications/{id}` | Delete application |

## Project Structure

```
kaaj/
├── app/
│   ├── main.py              # FastAPI application
│   ├── db.py                # Database configuration
│   ├── models/              # SQLAlchemy models
│   │   ├── lender.py        # Lender model
│   │   └── loan_application.py  # LoanApplication & LoanMatch models
│   ├── routers/             # API route handlers
│   │   ├── lender_routes.py
│   │   └── loan_application_routes.py
│   ├── services/            # Business logic
│   │   ├── ocr_service.py   # PDF text extraction
│   │   ├── llm_service.py   # LLM text processing
│   │   └── match_service.py # Match score calculation
│   └── workflows/           # Hatchet workflows
│       ├── lender_processing_workflow.py
│       ├── loan_matching_workflow.py
│       └── worker.py
├── frontend/                # React frontend
├── alembic/                 # Database migrations
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async connection string |
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM processing |
| `HATCHET_CLIENT_TOKEN` | Yes* | Hatchet workflow token |

*Required for workflow processing. Without it, uploads work but async processing is disabled.

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app
```

## License

MIT

