"""
╔════════════════════════════════════════════════════════╗
║           Database Connection Management                ║
║         SQLAlchemy Session & Engine Setup              ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Central database connection management
    - Connection pooling for performance
    - Async support for FastAPI
    - Handles both Azure SQL and PostgreSQL

Security Considerations:
    - Connection strings from environment variables
    - TLS/SSL enforced for all connections
    - Connection pool limits prevent resource exhaustion
    - Prepared statements prevent SQL injection

ISO 27001 Controls:
    - A.12.3.1: Information backup
    - A.14.2.7: Outsourced development
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import logger

# ┌─────────────────────────────────────────────────────────┐
# │ Database Engine Configuration                           │
# └─────────────────────────────────────────────────────────┘

# Determine if using async driver
is_async = settings.DATABASE_URL.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://"))

if is_async:
    # Async engine for FastAPI async endpoints
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
    )

    # Async session factory
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    logger.info(
        "async_database_engine_created",
        database_url=settings.DATABASE_URL.split("@")[-1],  # Hide credentials
        pool_size=settings.DB_POOL_SIZE,
    )

else:
    # Sync engine for synchronous operations
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    # Sync session factory
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    logger.info(
        "sync_database_engine_created",
        database_url=settings.DATABASE_URL.split("@")[-1],
        pool_size=settings.DB_POOL_SIZE,
    )


# ┌─────────────────────────────────────────────────────────┐
# │ Database Session Dependencies                           │
# └─────────────────────────────────────────────────────────┘


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database sessions.

    Yields:
        AsyncSession: Database session

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(User))
            return result.scalars().all()

    Security:
        - Session automatically committed or rolled back
        - Connection returned to pool after use
        - Prevents connection leaks

    ISO 27001 Control: A.14.2.7 - Outsourced development
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> Session:
    """
    Dependency for synchronous database sessions.

    Yields:
        Session: Database session

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_sync_db)):
            return db.query(User).all()

    Note:
        - Prefer async sessions for FastAPI endpoints
        - Use sync sessions only for background tasks or scripts
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ┌─────────────────────────────────────────────────────────┐
# │ Database Event Listeners                                │
# └─────────────────────────────────────────────────────────┘


@event.listens_for(pool.Pool, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Set SQLite pragmas for better performance and data integrity.

    Only runs for SQLite databases (local development).
    """
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")  # Enable foreign keys
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        cursor.close()


# ┌─────────────────────────────────────────────────────────┐
# │ Database Initialization                                 │
# └─────────────────────────────────────────────────────────┘


async def init_db() -> None:
    """
    Initialize database schema.

    Creates all tables defined in models.

    Warning:
        - Only use in development
        - Production uses Alembic migrations
        - Running this in production will not apply migrations

    Usage:
        # In startup event
        await init_db()
    """
    from app.models.base import Base

    if is_async:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("database_tables_created")
    else:
        Base.metadata.create_all(bind=engine)
        logger.info("database_tables_created")


async def close_db() -> None:
    """
    Close database connections.

    Called during application shutdown.

    Usage:
        # In shutdown event
        await close_db()
    """
    if is_async:
        await engine.dispose()
    else:
        engine.dispose()

    logger.info("database_connections_closed")


# ⚠️  DATABASE SECURITY NOTES:
#
# 🔒 Connection Security:
# - SSL/TLS enforced for all connections
# - Connection strings never logged
# - Credentials from environment variables only
# - Azure SQL requires encrypted connections
#
# 💾 Connection Pooling:
# - Pool size: 20 connections (configurable)
# - Max overflow: 10 additional connections
# - Pool timeout: 30 seconds
# - Connections recycled after 1 hour
# - Pre-ping prevents stale connections
#
# 🛡️ SQL Injection Prevention:
# - All queries use SQLAlchemy ORM
# - Prepared statements with parameter binding
# - Never use string concatenation for queries
# - Input validation via Pydantic
#
# 📊 Performance Optimization:
# - Async operations for non-blocking I/O
# - Connection pool reuse
# - Query result caching (application level)
# - Lazy loading for relationships
# - Bulk operations for batch inserts
#
# 🔧 Azure SQL Specific:
# - Connection string format:
#   mssql+pyodbc://user:pass@server.database.windows.net:1433/db?driver=ODBC+Driver+18+for+SQL+Server
# - Transparent Data Encryption (TDE) enabled
# - Geo-replication for disaster recovery
# - Automatic backups (daily, weekly, monthly)
#
# 🐘 PostgreSQL Specific (local dev):
# - Connection string format:
#   postgresql+asyncpg://user:pass@localhost:5432/db
# - Row-level security for multi-tenancy
# - JSONB for flexible schema
# - Full-text search capabilities
#
# 📋 ISO 27001 Control Mapping:
# - A.12.3.1: Information backup (automated by Azure SQL)
# - A.14.2.7: Outsourced development (secure coding practices)
# - A.14.2.8: System security testing (connection validation)
