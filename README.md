# 📚 Kaaj - Loan Management System

Welcome to Kaaj! A comprehensive loan management system with intelligent lender document processing and automated loan application matching using parallel workflows.

## 🎯 What's New: Loan Application Feature

**NEW!** Upload loan applications and automatically match them against all lenders using parallel processing with Hatchet workflows. Get AI-powered match scores and detailed recommendations.

👉 **[Quick Start Guide for Loan Applications](docs/LOAN_APPLICATION_QUICKSTART.md)**

---

## 📖 Documentation Index

**📑 [Complete Documentation Index](docs/INDEX.md)** - Browse all documentation in one place

---

### ⭐ Loan Application Feature (NEW)
| Document | Description | For |
|----------|-------------|-----|
| **[Quick Start](docs/LOAN_APPLICATION_QUICKSTART.md)** | Get started in 5 minutes | New users, developers |
| **[Architecture & Flow](docs/LOAN_APPLICATION_FLOW.md)** | Detailed system design | Developers, architects |
| **[API Examples](docs/LOAN_APPLICATION_EXAMPLES.md)** | Code examples & usage | Developers, integrators |
| **[Implementation Details](docs/IMPLEMENTATION_SUMMARY.md)** | Complete implementation overview | Developers, maintainers |
| **[Change Log](docs/CHANGES.md)** | All files created/modified | DevOps, reviewers |

### 🚀 Getting Started
| Document | Description | For |
|----------|-------------|-----|
| **[Setup Guide](docs/SETUP.md)** | Installation & configuration | New users, DevOps |

### 🏗️ Architecture & API
| Document | Description | For |
|----------|-------------|-----|
| **[Architecture Guide](docs/ARCHITECTURE.md)** | System design & patterns | Developers, architects |
| **[API Examples](docs/API_EXAMPLES.md)** | API usage & examples | Developers, integrators |

### 🧪 Testing
| Document | Description | For |
|----------|-------------|-----|
| **[Test Suite](tests/README.md)** | Running tests | Developers, QA |
| **[Celery Mocking](tests/CELERY_MOCKING.md)** | Mock setup for tests | Developers |

## 🗂️ Quick Navigation

### 🆕 Getting Started with Loan Applications
1. Read [Quick Start Guide](docs/LOAN_APPLICATION_QUICKSTART.md)
2. Run the demo: `python demo_loan_application.py application.pdf`
3. Check [API Examples](docs/LOAN_APPLICATION_EXAMPLES.md) for integration
4. See [Architecture Flow](docs/LOAN_APPLICATION_FLOW.md) for details

### 👤 For New Users
1. [Setup Guide](docs/SETUP.md) - Install and configure
2. [API Examples](docs/API_EXAMPLES.md) - Try the API
3. [Architecture](docs/ARCHITECTURE.md) - Understand the system
4. [Test Suite](tests/README.md) - Validate your setup

### 👨‍💻 For Developers
1. [Architecture Guide](docs/ARCHITECTURE.md) - System design
2. [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) - Code details
3. [API Examples](docs/API_EXAMPLES.md) - Integration examples
4. [Test Suite](tests/README.md) - Run tests

### 🚀 For DevOps
1. [Setup Guide](docs/SETUP.md) - Installation & deployment
2. [Architecture](docs/ARCHITECTURE.md) - Deployment strategies
3. [Change Log](docs/CHANGES.md) - Recent changes

## 🔍 What's Covered

### System Components
- ✅ Lender Model & Database Schema
- ✅ **Loan Application Model & Match Model** ⭐ NEW
- ✅ OCR Service (Tesseract)
- ✅ LLM Service (OpenAI GPT)
- ✅ **Match Service (AI-powered scoring)** ⭐ NEW
- ✅ Celery Async Workers
- ✅ **Hatchet Parallel Workflows** ⭐ NEW
- ✅ FastAPI REST API
- ✅ PostgreSQL Database
- ✅ Redis Task Queue

### Features

#### Lender Management
- ✅ PDF Upload & Processing
- ✅ OCR Text Extraction
- ✅ LLM-based Data Structuring
- ✅ Async Background Processing
- ✅ Status Tracking

#### Loan Applications ⭐ NEW
- ✅ **Loan Application PDF Upload**
- ✅ **Automated Matching Against All Lenders**
- ✅ **Parallel Processing with Hatchet**
- ✅ **AI-Powered Match Scores (0-100)**
- ✅ **Detailed Match Analysis**
- ✅ **Strengths, Weaknesses & Recommendations**
- ✅ **Workflow Tracking**
- ✅ **Match Filtering & Sorting**

#### General
- ✅ Comprehensive Logging
- ✅ Error Handling & Retries
- ✅ Comprehensive Test Suite

### Development
- ✅ Code Organization
- ✅ Testing Strategies
- ✅ Comprehensive Test Suite
- ✅ Deployment Options
- ✅ Scalability Patterns
- ✅ Security Considerations

## 🆘 Need Help?

| Issue | Documentation |
|-------|--------------|
| **Loan Applications** | [Quick Start](docs/LOAN_APPLICATION_QUICKSTART.md) • [Examples](docs/LOAN_APPLICATION_EXAMPLES.md) |
| **Installation Issues** | [Setup Guide - Troubleshooting](docs/SETUP.md#troubleshooting) |
| **API Questions** | [API Examples](docs/API_EXAMPLES.md) • [Loan App Examples](docs/LOAN_APPLICATION_EXAMPLES.md) |
| **Architecture** | [Architecture Guide](docs/ARCHITECTURE.md) • [Loan App Flow](docs/LOAN_APPLICATION_FLOW.md) |
| **Testing** | [Test Suite](tests/README.md) |

## 🔗 Resources

### Internal Documentation
- **[📑 Complete Docs Index](docs/INDEX.md)** - All documentation in one place
- **[🚀 Quick Start - Loan Apps](docs/LOAN_APPLICATION_QUICKSTART.md)** - Get started fast
- **[🏗️ System Architecture](docs/ARCHITECTURE.md)** - Technical design
- **[🔌 API Examples](docs/API_EXAMPLES.md)** - Integration guide

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hatchet Documentation](https://docs.hatchet.run/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)


