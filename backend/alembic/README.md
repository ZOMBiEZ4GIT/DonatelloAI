# Database Migrations

This directory contains Alembic database migrations for the Enterprise Image Generation Platform.

## Quick Start

### Prerequisites

1. **Database Setup**: Ensure PostgreSQL or Azure SQL is running
2. **Environment Variables**: Configure `.env` with `DATABASE_URL`
3. **Dependencies**: Run `pip install -r requirements.txt`

### Common Commands

```bash
# Create a new migration (auto-generate from model changes)
alembic revision --autogenerate -m "add user preferences column"

# Create empty migration (for data migrations)
alembic revision -m "migrate legacy user data"

# Apply all pending migrations
alembic upgrade head

# Apply one migration forward
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Show current database version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history -r current:head
```

## Migration Workflow

### 1. Create Migration

After modifying models in `app/models/`:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "descriptive message"
```

**⚠️ IMPORTANT:** Always review auto-generated migrations before applying!

### 2. Review Migration

Check the generated file in `alembic/versions/`:

- Verify upgrade() logic is correct
- Verify downgrade() logic can safely reverse changes
- Add data migrations if needed (e.g., populating new columns)
- Test both upgrade and downgrade paths

### 3. Test Locally

```bash
# Apply migration
alembic upgrade head

# Verify database schema
# Run application and test functionality

# Test rollback
alembic downgrade -1
alembic upgrade head
```

### 4. Commit to Git

```bash
git add alembic/versions/<new_migration>.py
git commit -m "Migration: <description>"
```

## Production Deployment

### Pre-Production Checklist

- [ ] Migration tested on local development database
- [ ] Migration tested on staging database
- [ ] Downgrade path tested and verified
- [ ] Data migration scripts validated (if applicable)
- [ ] Database backup created
- [ ] Maintenance window scheduled (if needed)
- [ ] Rollback plan documented

### Applying in Production

```bash
# 1. Backup database
az sql db export --resource-group <rg> --server <server> --name <db> ...

# 2. Apply migration
alembic upgrade head

# 3. Verify application health
curl https://api.example.com/health

# 4. Monitor logs for errors
tail -f /var/log/app.log
```

### Rollback (if needed)

```bash
# Rollback to previous version
alembic downgrade -1

# Or rollback to specific version
alembic downgrade <revision_id>

# Restore from backup (worst case)
az sql db import --resource-group <rg> --server <server> --name <db> ...
```

## Migration Best Practices

### DO:

✅ **Review auto-generated migrations** - They're not always perfect
✅ **Test both upgrade and downgrade** - Ensure rollback works
✅ **Use transactions** - Wrap data migrations in transactions
✅ **Backup before production** - Always have a restore point
✅ **Small, focused migrations** - One logical change per migration
✅ **Descriptive commit messages** - Explain why, not just what

### DON'T:

❌ **Don't modify old migrations** - Create new ones instead
❌ **Don't skip testing rollback** - You might need it in production
❌ **Don't include sensitive data** - Use data seeds for test data
❌ **Don't run in production without backup** - Murphy's Law applies
❌ **Don't combine schema + data changes** - Separate for safety

## Common Scenarios

### Adding a Column

```python
# Auto-generated migration
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
```

### Changing Column Type

```python
def upgrade():
    # For PostgreSQL
    op.alter_column('users', 'age',
                   existing_type=sa.String(),
                   type_=sa.Integer(),
                   postgresql_using='age::integer')

def downgrade():
    op.alter_column('users', 'age',
                   existing_type=sa.Integer(),
                   type_=sa.String())
```

### Data Migration

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Create table reference
    users_table = table('users',
        column('id', sa.UUID),
        column('old_status', sa.String),
        column('new_status', sa.String),
    )

    # Migrate data
    op.execute(
        users_table.update()
        .where(users_table.c.old_status == 'active')
        .values(new_status='ACTIVE')
    )

    # Drop old column
    op.drop_column('users', 'old_status')

def downgrade():
    # Add old column back
    op.add_column('users', sa.Column('old_status', sa.String(20)))

    # Reverse data migration
    users_table = table('users',
        column('id', sa.UUID),
        column('old_status', sa.String),
        column('new_status', sa.String),
    )

    op.execute(
        users_table.update()
        .where(users_table.c.new_status == 'ACTIVE')
        .values(old_status='active')
    )
```

### Creating Enum

```python
def upgrade():
    # PostgreSQL enum
    op.execute("CREATE TYPE user_role_enum AS ENUM ('admin', 'user', 'guest')")

    op.add_column('users',
        sa.Column('role', sa.Enum('admin', 'user', 'guest', name='user_role_enum'))
    )

def downgrade():
    op.drop_column('users', 'role')
    op.execute("DROP TYPE user_role_enum")
```

## Troubleshooting

### "Target database is not up to date"

Your database is behind. Apply pending migrations:

```bash
alembic upgrade head
```

### "Can't locate revision"

Your migration history is out of sync. Check:

```bash
# What's in the database?
alembic current

# What's in the codebase?
alembic heads

# Fix: Stamp database to match codebase (dangerous!)
alembic stamp head
```

### "Revision not found"

You have migrations in your database that aren't in your codebase. This usually happens when:

- Working on different branches
- Missing migration files
- Database from different environment

Solution: Ensure you have all migration files or stamp to correct version.

### Migration Conflicts

Two developers created migrations simultaneously:

```bash
# Create merge migration
alembic merge -m "merge heads" <rev1> <rev2>

# Or resolve manually by editing migration files
```

## ISO 27001 Compliance

This migration system supports the following controls:

- **A.12.4.1**: Event logging (migration audit trail in version table)
- **A.14.2.1**: Secure development policy (version-controlled schema)
- **A.12.1.2**: Change management (controlled, auditable database changes)

All migrations are tracked, versioned, and reversible to support audit requirements.

## Support

For issues or questions:

1. Check this README
2. Review [Alembic Documentation](https://alembic.sqlalchemy.org/)
3. Check application logs for database errors
4. Contact platform team

---

**Last Updated**: 2025-11-16
**Alembic Version**: 1.12.1
**SQLAlchemy Version**: 2.0.23
