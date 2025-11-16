"""
╔════════════════════════════════════════════════════════╗
║         Alembic Migration Environment                  ║
║          Async Database Migration Support              ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Handles database schema migrations
    - Supports async SQLAlchemy operations
    - Loads models for auto-generation
    - Uses environment variables for connection

Security:
    - Database credentials from environment (never hardcoded)
    - Azure Key Vault integration in production
    - Migration history tracked in version table

ISO 27001 Controls:
    - A.12.4.1: Event logging (migration audit trail)
    - A.14.2.1: Secure development policy
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import app configuration
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.models.base import Base

# Import all models so Alembic can detect them
from app.models.user import User, UserRole
from app.models.session import UserSession
from app.models.department import Department
from app.models.generation import (
    ImageGeneration,
    BatchGenerationJob,
    GenerationStatus,
)

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Set database URL from environment
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though
    an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with given connection.

    Args:
        connection: Database connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
        # Include schemas if needed
        # include_schemas=True,
        # version_table_schema=target_metadata.schema,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    In this scenario we need to create an async Engine and associate a
    connection with the context.
    """
    # Create async engine configuration
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    # Create async engine
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Don't pool connections for migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Runs migrations with async support for our async database setup.
    """
    asyncio.run(run_async_migrations())


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


# ⚠️  MIGRATION BEST PRACTICES:
#
# 📝 Before Creating Migration:
# 1. Ensure all model changes are complete
# 2. Review model relationships and constraints
# 3. Consider data migration needs (not just schema)
# 4. Test migration on development database first
#
# 🔄 Creating Migration:
# ```bash
# # Auto-generate migration from model changes
# alembic revision --autogenerate -m "description"
#
# # Create empty migration for data changes
# alembic revision -m "description"
# ```
#
# ⬆️  Applying Migrations:
# ```bash
# # Upgrade to latest
# alembic upgrade head
#
# # Upgrade by 1 version
# alembic upgrade +1
#
# # Upgrade to specific version
# alembic upgrade <revision>
# ```
#
# ⬇️  Rolling Back:
# ```bash
# # Downgrade by 1 version
# alembic downgrade -1
#
# # Downgrade to base (WARNING: data loss!)
# alembic downgrade base
# ```
#
# 📊 Migration History:
# ```bash
# # Show current version
# alembic current
#
# # Show migration history
# alembic history
#
# # Show pending migrations
# alembic history -r current:head
# ```
#
# ⚠️  SECURITY CONSIDERATIONS:
# - Never include sensitive data in migrations
# - Test downgrade paths before production
# - Backup database before running migrations
# - Use transactions for data migrations
# - Review auto-generated migrations carefully
#
# 📋 ISO 27001 Control Mapping:
# - A.12.4.1: Event logging (migration audit trail)
# - A.14.2.1: Secure development policy (schema version control)
# - A.12.1.2: Change management (controlled database changes)
