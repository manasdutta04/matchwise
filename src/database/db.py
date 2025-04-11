"""
Database initialization and connection management.
Modified to support serverless environments like Vercel.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import Session

# Environment check
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
IS_VERCEL = os.environ.get("VERCEL", "0") == "1"

# Database URLs - with dynamic paths for serverless environments
if IS_VERCEL:
    # For Vercel, use /tmp directory which is writable
    DB_PATH = "/tmp/matchwise.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
else:
    # For normal environments, use project directory
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///matchwise.db")
    ASYNC_DATABASE_URL = os.environ.get("DATABASE_ASYNC_URL", "sqlite+aiosqlite:///matchwise.db")

# Create engine for synchronous operations
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    # Add connection pooling for better performance in production
    pool_size=5 if ENVIRONMENT == "production" else None,
    max_overflow=10 if ENVIRONMENT == "production" else None
)

# Create engine for asynchronous operations - comment this out if aiosqlite is not installed
try:
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    # Session factories
    AsyncSessionLocal = sessionmaker(
        class_=AsyncSession, autocommit=False, autoflush=False, bind=async_engine
    )
except ImportError:
    # If aiosqlite is not available, set these to None
    async_engine = None
    AsyncSessionLocal = None
    print("Warning: aiosqlite not available, async database operations will not work")

# Session factories for synchronous operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Get an async database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database not available - aiosqlite is required")
        
    async with AsyncSessionLocal() as session:
        yield session


def init_db():
    """Initialize the database."""
    create_tables()
    print(f"Database initialized successfully at {DATABASE_URL}")


if __name__ == "__main__":
    init_db() 