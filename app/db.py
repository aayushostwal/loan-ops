from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import create_engine

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/kaaj"
SYNC_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/kaaj"

# Async engine for FastAPI
engine = create_async_engine(DATABASE_URL, echo=True)

# Sync engine for Alembic migrations
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)
