# alembic/env.py
import os
import sys
from logging.config import fileConfig
import asyncio # Needed for async engine inspection if used directly (not here)

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import create_async_engine # Keep if needed elsewhere, but Alembic needs sync

# Add project root to Python path to allow importing 'app'
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_dir)

# --- Import your project's settings and Base ---
from app.core.config import settings # Your project's configuration
from app.db.database import Base     # Your project's declarative base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_sync_database_url():
    """Gets the synchronous database URL from settings."""
    async_db_url = settings.database_uri
    if not async_db_url:
        raise ValueError("DATABASE_URI is not set in the configuration.")

    # Convert async URL to sync URL for Alembic
    if '+asyncpg' in async_db_url:
        # Replace asyncpg driver with psycopg2 (or just remove driver for default)
        sync_db_url = async_db_url.replace('+asyncpg', '') # Or '+psycopg2' if preferred
        # Alternative: sync_db_url = async_db_url.replace('postgresql+asyncpg', 'postgresql')
    elif async_db_url.startswith('postgresql://'):
        # Assume it's already usable or doesn't specify an async driver
        sync_db_url = async_db_url
    else:
        print(
            f"Warning: Unrecognized DATABASE_URL scheme for sync conversion: {async_db_url}. Attempting direct use."
        )
        sync_db_url = async_db_url

    print(f"Alembic using SYNC URL: {sync_db_url}")
    return sync_db_url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_sync_database_url() # Use our function to get the URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    sync_db_url = get_sync_database_url() # Use our function to get the URL

    connectable = create_engine(
        sync_db_url,
        poolclass=pool.NullPool # Use NullPool for migration engine
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # compare_type=True, # Uncomment if you need subtle type comparisons
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    print("Running migrations offline...")
    run_migrations_offline()
else:
    print("Running migrations online...")
    run_migrations_online()