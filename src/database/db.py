"""
Database initialization and connection management.
This module handles SQLite database setup and connection management.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import Session

# Database file path
DATABASE_URL = "sqlite:///matchwise.db"
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///matchwise.db"

# Create engine for synchronous operations
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
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
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_db() 