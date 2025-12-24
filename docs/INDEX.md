# 📚 Kaaj Documentation Index

Complete documentation for the Kaaj Loan Management System.

## 📖 Table of Contents

- [Quick Reference](#quick-reference)
- [Getting Started](#getting-started)
- [Loan Application Feature](#loan-application-feature)
- [Core Features](#core-features)
- [Architecture & Design](#architecture--design)
- [API Reference](#api-reference)
- [Testing](#testing)
- [For Developers](#for-developers)

---

## Quick Reference

| What do you want to do? | Go here |
|-------------------------|---------|
| 🚀 Get started quickly | [Setup Guide](SETUP.md) |
| 💼 Upload loan applications | [Loan App Quick Start](LOAN_APPLICATION_QUICKSTART.md) |
| 📄 Upload lender documents | [API Examples](API_EXAMPLES.md#lender-upload) |
| 🔌 Use the API | [API Examples](API_EXAMPLES.md) |
| 🏗️ Understand the system | [Architecture Guide](ARCHITECTURE.md) |
| 🧪 Run tests | [Test Suite](../tests/README.md) |
| 🐛 Troubleshoot issues | [Setup - Troubleshooting](SETUP.md#troubleshooting) |

---

## Getting Started

### 1. Setup Guide
**File:** [SETUP.md](SETUP.md)  
**For:** New users, DevOps, System administrators

**Contents:**
- System prerequisites (PostgreSQL, Redis, Tesseract)
- Installation steps
- Environment configuration
- Running the application
- Troubleshooting common issues

**Start here if:** You're setting up Kaaj for the first time.

---

## Loan Application Feature

### 1. Quick Start Guide
**File:** [LOAN_APPLICATION_QUICKSTART.md](LOAN_APPLICATION_QUICKSTART.md)  
**For:** Users, Developers, Product managers

**Contents:**
- Feature overview
- Quick start (5 minutes)
- Basic usage examples
- Match score breakdown
- Testing instructions
- Troubleshooting

**Start here if:** You want to upload loan applications and get matches.

### 2. Architecture & Flow
**File:** [LOAN_APPLICATION_FLOW.md](LOAN_APPLICATION_FLOW.md)  
**For:** Developers, Architects, Technical leads

**Contents:**
- Complete architecture
- Flow diagrams
- API endpoints (detailed)
- Match score calculation
- Hatchet workflow steps
- Setup instructions
- Performance considerations

**Start here if:** You need to understand how loan matching works internally.

### 3. API Examples
**File:** [LOAN_APPLICATION_EXAMPLES.md](LOAN_APPLICATION_EXAMPLES.md)  
**For:** Developers, Integrators, QA engineers

**Contents:**
- Upload examples (curl, Python)
- Status checking
- Match retrieval
- Filtering examples
- Error handling
- Complete workflow example
- Best practices

**Start here if:** You're integrating with the loan application API.

### 4. Implementation Details
**File:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)  
**For:** Developers, Code reviewers, Maintainers

**Contents:**
- All files created/modified
- Code statistics
- Feature list
- Testing strategy
- Integration points
- Future enhancements

**Start here if:** You need a technical overview of the implementation.

### 5. Change Log
**File:** [CHANGES.md](CHANGES.md)  
**For:** Developers, DevOps, Code reviewers

**Contents:**
- Files created
- Files modified
- Statistics
- Features added
- Integration points

**Start here if:** You need to know what changed in the loan application feature.

---

## Core Features

### 1. Architecture Guide
**File:** [ARCHITECTURE.md](ARCHITECTURE.md)  
**For:** Developers, Architects, Technical leads

**Contents:**
- System architecture
- Project structure
- Data flow
- Technology stack
- Design patterns
- Security practices
- Deployment strategies
- Scalability considerations

**Start here if:** You need to understand the overall system design.

### 2. API Examples (Lender Management)
**File:** [API_EXAMPLES.md](API_EXAMPLES.md)  
**For:** Developers, Integrators, QA engineers

**Contents:**
- Lender upload examples
- PDF processing
- Status tracking
- Data retrieval
- Error handling
- Testing workflows

**Start here if:** You're working with lender document management.

---

## API Reference

### REST API Endpoints

#### Lender Management
- `POST /api/lenders/upload` - Upload lender policy PDF
- `GET /api/lenders/{id}` - Get lender details
- `GET /api/lenders/` - List all lenders
- `DELETE /api/lenders/{id}` - Delete lender

**Documentation:** [API_EXAMPLES.md](API_EXAMPLES.md)

#### Loan Applications
- `POST /api/loan-applications/upload` - Upload loan application
- `GET /api/loan-applications/{id}` - Get application details
- `GET /api/loan-applications/` - List applications
- `GET /api/loan-applications/{id}/matches` - Get match results
- `DELETE /api/loan-applications/{id}` - Delete application

**Documentation:** [LOAN_APPLICATION_EXAMPLES.md](LOAN_APPLICATION_EXAMPLES.md)

#### System
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)

---

## Testing

### Test Suite
**File:** [../tests/README.md](../tests/README.md)  
**For:** Developers, QA engineers, CI/CD

**Contents:**
- Running tests
- Test structure
- Setup instructions
- Mocking strategies
- Troubleshooting test failures

**Also see:**
- [Celery Mocking](../tests/CELERY_MOCKING.md) - Mock setup details
- Test files in `tests/` directory

---

## For Developers

### Development Workflow

1. **Setup Development Environment**
   - Follow [SETUP.md](SETUP.md)
   - Run tests: `./run_tests.sh`

2. **Understanding the Codebase**
   - Read [ARCHITECTURE.md](ARCHITECTURE.md)
   - Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

3. **Working on Features**
   - Check [CHANGES.md](CHANGES.md) for recent updates
   - Follow patterns in existing code
   - Write tests for new features
   - Update documentation

4. **Testing Your Changes**
   - Run full test suite: `./run_tests.sh`
   - Test specific files: `pytest tests/test_file.py -v`
   - Check [../tests/README.md](../tests/README.md)

5. **API Development**
   - Reference [API_EXAMPLES.md](API_EXAMPLES.md)
   - Use interactive docs at `/docs`
   - Test with demo scripts

### Code Organization

```
kaaj/
├── app/
│   ├── models/          # Database models
│   ├── routers/         # API routes
│   ├── services/        # Business logic
│   ├── tasks/           # Celery tasks
│   └── workflows/       # Hatchet workflows
├── docs/                # This directory
├── tests/               # Test suite
└── alembic/            # Database migrations
```

### Key Modules

| Module | Purpose | Documentation |
|--------|---------|---------------|
| `app.models.lender` | Lender data model | [ARCHITECTURE.md](ARCHITECTURE.md) |
| `app.models.loan_application` | Loan app models | [LOAN_APPLICATION_FLOW.md](LOAN_APPLICATION_FLOW.md) |
| `app.services.llm_service` | LLM processing | [ARCHITECTURE.md](ARCHITECTURE.md) |
| `app.services.match_service` | Match scoring | [LOAN_APPLICATION_FLOW.md](LOAN_APPLICATION_FLOW.md) |
| `app.workflows.loan_matching_workflow` | Parallel matching | [LOAN_APPLICATION_FLOW.md](LOAN_APPLICATION_FLOW.md) |

---

## External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Hatchet Documentation](https://docs.hatchet.run/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

---

## Document Maintenance

### When to Update Documentation

- **Adding features**: Update [ARCHITECTURE.md](ARCHITECTURE.md) and create examples
- **Changing APIs**: Update [API_EXAMPLES.md](API_EXAMPLES.md) or [LOAN_APPLICATION_EXAMPLES.md](LOAN_APPLICATION_EXAMPLES.md)
- **Setup changes**: Update [SETUP.md](SETUP.md)
- **Bug fixes**: Update troubleshooting sections
- **New tests**: Update [../tests/README.md](../tests/README.md)

### Documentation Standards

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Keep table of contents updated
- Link related documents

---

## Quick Links

- [📖 Main README](../README.md)
- [🚀 Setup Guide](SETUP.md)
- [💼 Loan App Quick Start](LOAN_APPLICATION_QUICKSTART.md)
- [🏗️ Architecture](ARCHITECTURE.md)
- [🔌 API Examples](API_EXAMPLES.md)
- [🧪 Test Suite](../tests/README.md)

---

**Last Updated:** December 24, 2025  
**Kaaj Version:** 2.0.0

