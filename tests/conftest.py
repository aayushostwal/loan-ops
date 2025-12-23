"""
Test Configuration and Fixtures

This module provides pytest fixtures for testing the Kaaj API.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

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


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the FastAPI app.
    
    This fixture overrides the database dependency to use the test database.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
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
    return pdf_files[0]


@pytest.fixture
def all_pdf_files(pdf_files: list[str]) -> list[str]:
    """Return all PDF files from the assets directory."""
    return pdf_files

