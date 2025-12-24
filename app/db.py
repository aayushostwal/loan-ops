"""
Central Database Configuration

This module provides centralized database engine configuration for the entire application.
All database connections should use engines from this module.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine

# Get database URLs from environment or use defaults
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/kaaj"
)
SYNC_DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/kaaj"
)

# Main async engine for FastAPI routes
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Connection pool size
    max_overflow=20  # Max overflow connections
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

# Async engine for background tasks (Celery workers)
# Uses separate pool to avoid conflicts with main engine
task_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Async engine for workflow processing (Hatchet workers)
# Uses separate pool for workflow operations
workflow_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Session makers for different contexts
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

TaskAsyncSession = async_sessionmaker(
    task_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

WorkflowAsyncSession = async_sessionmaker(
    workflow_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def get_engine(context: str = "default"):
    """
    Get the appropriate engine for the given context.
    
    Args:
        context: One of 'default', 'task', 'workflow', 'sync'
    
    Returns:
        SQLAlchemy engine for the specified context
    """
    engines = {
        "default": engine,
        "task": task_engine,
        "workflow": workflow_engine,
        "sync": sync_engine
    }
    return engines.get(context, engine)
