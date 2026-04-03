"""Async database engine, session factory, and base model class."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import DeclarativeBase

from backend.settings import settings

# Async engine — connection pool to PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Session factory — creates new sessions for each request
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Synchronous engine for Celery workers
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DB_ECHO,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
)

# Synchronous session factory for Celery workers
sync_session_factory = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass
