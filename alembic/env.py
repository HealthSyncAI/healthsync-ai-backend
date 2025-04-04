
import os
import sys
from logging.config import fileConfig
import asyncio

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import create_async_engine


project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_dir)


from app.core.config import settings
from app.db.database import Base



config = context.config



if config.config_file_name is not None:
    fileConfig(config.config_file_name)



target_metadata = Base.metadata







def get_sync_database_url():
    """Gets the synchronous database URL from settings."""
    async_db_url = settings.database_uri
    if not async_db_url:
        raise ValueError("DATABASE_URI is not set in the configuration.")


    if '+asyncpg' in async_db_url:

        sync_db_url = async_db_url.replace('+asyncpg', '')

    elif async_db_url.startswith('postgresql://'):

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
    url = get_sync_database_url()
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
    sync_db_url = get_sync_database_url()

    connectable = create_engine(
        sync_db_url,
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,

        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    print("Running migrations offline...")
    run_migrations_offline()
else:
    print("Running migrations online...")
    run_migrations_online()