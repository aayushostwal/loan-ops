"""
Test Configuration and Fixtures

This module provides pytest fixtures for testing the Kaaj API.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

# Set test environment variables before importing app modules
# This prevents Celery from trying to connect to Redis during import
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import app
from app.models import Base
from app.routers.lender_routes import get_db

# Test database URL - use a separate database for testing
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_kaaj"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Disable connection pooling for tests
)

# Create test session maker
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def mock_celery_app():
    """
    Mock the Celery app at session level to prevent any Redis connection attempts.
    
    This fixture is autouse=True, so it runs automatically for all tests.
    """
    # Mock the celery_app to prevent connection attempts
    with patch('app.celery_app.celery_app.connection') as mock_conn:
        mock_conn.return_value = MagicMock()
        yield


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def mock_celery():
    """
    Mock Celery tasks to avoid Redis dependency in tests.
    
    This fixture mocks the Celery task so that .delay() and .apply_async()
    return a mock AsyncResult without actually connecting to Redis.
    """
    # Create a mock AsyncResult that Celery tasks return
    mock_async_result = MagicMock()
    mock_async_result.id = "test-task-id-12345"
    mock_async_result.state = "PENDING"
    mock_async_result.ready.return_value = False
    mock_async_result.successful.return_value = False
    mock_async_result.failed.return_value = False
    
    # Patch the Celery task methods
    with patch('app.tasks.lender_tasks.process_lender_document.delay', return_value=mock_async_result) as mock_delay, \
         patch('app.tasks.lender_tasks.process_lender_document.apply_async', return_value=mock_async_result) as mock_apply_async:
        yield {
            'delay': mock_delay,
            'apply_async': mock_apply_async,
            'async_result': mock_async_result
        }


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    
    This fixture:
    - Creates all tables before the test
    - Provides a clean database session
    - Rolls back all changes and drops tables after the test
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession, mock_celery) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the FastAPI app.
    
    This fixture:
    - Overrides the database dependency to use the test database session
    - Mocks the OCR service to avoid dependency on Tesseract
    - Mocks the LLM service to avoid OpenAI API calls
    - Mocks the Match service to avoid OpenAI API calls
    - Mocks the TaskAsyncSession to use the test session (prevents concurrency issues)
    - Mocks Celery tasks to avoid Redis dependency
    - Mocks Hatchet client to avoid Hatchet server dependency
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create a mock session context manager that returns the test db_session
    class MockAsyncSessionContext:
        async def __aenter__(self):
            return db_session
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            # Don't close the session, let the fixture handle it
            pass
    
    # Mock the task session maker to use the test session
    mock_task_session = lambda: MockAsyncSessionContext()
    
    # Mock Hatchet client
    mock_hatchet_client = MagicMock()
    mock_workflow_run = MagicMock()
    mock_workflow_run.workflow_run_id = "test-workflow-run-id-12345"
    mock_hatchet_client.admin.run_workflow.return_value = mock_workflow_run
    
    # Mock the OCR service to return sample text
    with patch('app.services.ocr_service.OCRService.extract_text_from_pdf') as mock_ocr, \
         patch('app.services.llm_service.LLMService.process_raw_text', new_callable=AsyncMock) as mock_llm_process, \
         patch('app.services.llm_service.LLMService.process_loan_application', new_callable=AsyncMock) as mock_llm_loan_app, \
         patch('app.services.llm_service.LLMService.validate_and_enrich_data', new_callable=AsyncMock) as mock_llm_validate, \
         patch('app.services.match_service.MatchService.calculate_match_score', new_callable=AsyncMock) as mock_match_score, \
         patch('app.workflows.loan_matching_workflow.get_hatchet_client', return_value=None) as mock_hatchet, \
         patch('app.tasks.lender_tasks.TaskAsyncSession', mock_task_session):
        
        # Configure OCR mock to return sample extracted text
        mock_ocr.return_value = """
        ADVANTAGE BROKER 2025
        Sample Lender Document
        
        Loan Products:
        - Fixed Rate: 3.5% - 4.5%
        - Variable Rate: 2.5% - 3.5%
        - Interest Only: Available
        
        LVR: Up to 95%
        Minimum Loan: $50,000
        Maximum Loan: $5,000,000
        
        Contact: info@samplelender.com
        Phone: 1800 123 456
        """
        
        # Configure LLM mock to return structured data for lender processing
        mock_llm_response = {
            "loan_types": ["Fixed Rate", "Variable Rate", "Interest Only"],
            "interest_rates": {
                "fixed_rate": {"min": "3.5%", "max": "4.5%"},
                "variable_rate": {"min": "2.5%", "max": "3.5%"}
            },
            "eligibility_criteria": [
                "Minimum credit score: 650",
                "Stable employment history",
                "Valid identification"
            ],
            "loan_amount_range": {
                "min": "$50,000",
                "max": "$5,000,000"
            },
            "tenure": {
                "min": "1 year",
                "max": "30 years"
            },
            "processing_fees": "Application fee applies",
            "documents_required": [
                "Proof of identity",
                "Proof of income",
                "Bank statements",
                "Property documents"
            ],
            "key_terms": [
                "LVR up to 95%",
                "Interest only option available",
                "Fixed and variable rate options"
            ],
            "contact_information": {
                "email": "info@samplelender.com",
                "phone": "1800 123 456",
                "website": "www.advantagebroker.com"
            },
            "special_offers": [
                "Competitive rates for 2025",
                "Flexible repayment options"
            ],
            "_metadata": {
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "tokens_used": 850,
                "processing_successful": True
            }
        }
        
        # Configure LLM mock for loan application processing
        mock_loan_app_response = {
            "loan_type": "home",
            "loan_amount": {"amount": 450000, "currency": "USD"},
            "loan_purpose": "Purchase primary residence",
            "tenure_requested": {"years": 30},
            "employment_details": {
                "status": "employed",
                "employer": "Tech Corp",
                "job_title": "Software Engineer",
                "years_employed": 5
            },
            "income_details": {
                "monthly_income": 8500,
                "annual_income": 102000,
                "other_income": None
            },
            "credit_score": 720,
            "existing_loans": [],
            "assets": {
                "property": [],
                "vehicles": [{"type": "car", "value": 30000}],
                "investments": {"stocks": 75000}
            },
            "personal_information": {
                "age": 32,
                "marital_status": "single",
                "dependents": 0,
                "education": "Bachelor's Degree"
            },
            "contact_information": {
                "phone": "+1-555-0100",
                "email": "applicant@example.com",
                "address": "123 Main St, City, State 12345"
            },
            "documents_provided": ["Pay stubs", "Tax returns", "Bank statements"],
            "special_requirements": None,
            "_metadata": {
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "tokens_used": 920,
                "processing_successful": True
            }
        }
        
        # Configure match score mock
        mock_match_response = {
            "match_score": 82.5,
            "match_analysis": {
                "match_score": 82.5,
                "match_category": "very_good",
                "strengths": [
                    "Excellent credit score",
                    "Strong income profile",
                    "Stable employment history"
                ],
                "weaknesses": [
                    "Limited down payment",
                    "No existing property ownership"
                ],
                "recommendations": [
                    "Consider mortgage insurance",
                    "Explore first-time buyer programs"
                ],
                "criteria_scores": {
                    "loan_amount": 9,
                    "loan_type": 10,
                    "interest_rate": 8,
                    "eligibility": 9,
                    "tenure": 8,
                    "credit_profile": 9,
                    "income": 9,
                    "documentation": 8,
                    "special_conditions": 7,
                    "overall_fit": 8
                },
                "summary": "Very good match with strong fundamentals and minor areas for improvement",
                "_metadata": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.2,
                    "tokens_used": 1200,
                    "application_id": 1,
                    "lender_id": 1,
                    "lender_name": "Test Lender",
                    "calculation_successful": True
                }
            }
        }
        
        # Configure async mocks to return the structured responses
        mock_llm_process.return_value = mock_llm_response
        mock_llm_loan_app.return_value = mock_loan_app_response
        mock_match_score.return_value = mock_match_response
        
        # Configure validate_and_enrich_data async mock
        async def mock_validate_enrich(processed_data, raw_text):
            enriched = processed_data.copy()
            enriched["_validation"] = {
                "field_completeness": {
                    "loan_types": True,
                    "interest_rates": True,
                    "eligibility_criteria": True
                },
                "completeness_score": 1.0
            }
            return enriched
        
        mock_llm_validate.side_effect = mock_validate_enrich
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def assets_dir() -> str:
    """Return the path to the test assets directory."""
    return os.path.join(os.path.dirname(__file__), "assets")


@pytest.fixture(scope="session")
def pdf_files(assets_dir: str) -> list[str]:
    """
    Get list of PDF files in the assets directory.
    
    Returns:
        List of absolute paths to PDF files
    """
    if not os.path.exists(assets_dir):
        raise FileNotFoundError(
            f"Assets directory not found: {assets_dir}. "
            "Please create tests/assets/ and add your PDF files there."
        )
    
    pdf_files = [
        os.path.join(assets_dir, f)
        for f in os.listdir(assets_dir)
        if f.lower().endswith('.pdf')
    ]
    
    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {assets_dir}. "
            "Please add at least one PDF file for testing."
        )
    
    return sorted(pdf_files)


@pytest.fixture
def sample_pdf_file(pdf_files: list[str]) -> str:
    """Return the first PDF file from the assets directory."""
    print("Using PDF FIle: ", pdf_files[0])
    return pdf_files[0]


@pytest.fixture
def all_pdf_files(pdf_files: list[str]) -> list[str]:
    """Return all PDF files from the assets directory."""
    return pdf_files


@pytest.fixture
def expected_llm_response() -> dict:
    """
    Return the expected mocked LLM response structure.
    
    This fixture provides the exact structure that the mocked LLM service returns,
    allowing tests to verify against this expected response.
    """
    return {
        "loan_types": ["Fixed Rate", "Variable Rate", "Interest Only"],
        "interest_rates": {
            "fixed_rate": {"min": "3.5%", "max": "4.5%"},
            "variable_rate": {"min": "2.5%", "max": "3.5%"}
        },
        "eligibility_criteria": [
            "Minimum credit score: 650",
            "Stable employment history",
            "Valid identification"
        ],
        "loan_amount_range": {
            "min": "$50,000",
            "max": "$5,000,000"
        },
        "tenure": {
            "min": "1 year",
            "max": "30 years"
        },
        "processing_fees": "Application fee applies",
        "documents_required": [
            "Proof of identity",
            "Proof of income",
            "Bank statements",
            "Property documents"
        ],
        "key_terms": [
            "LVR up to 95%",
            "Interest only option available",
            "Fixed and variable rate options"
        ],
        "contact_information": {
            "email": "info@samplelender.com",
            "phone": "1800 123 456",
            "website": "www.advantagebroker.com"
        },
        "special_offers": [
            "Competitive rates for 2025",
            "Flexible repayment options"
        ],
        "_metadata": {
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "tokens_used": 850,
            "processing_successful": True
        }
    }

