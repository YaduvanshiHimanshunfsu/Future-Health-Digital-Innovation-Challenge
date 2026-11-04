import asyncio
import logging.config
import os

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401 - registers every table on Base.metadata
from app.db.base import Base

if context.config.config_file_name:
    logging.config.fileConfig(context.config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _migration_url() -> str:
    # Separate from DATABASE_URL on purpose: the API's role has no rights to change the schema.
    url = os.environ.get("MIGRATION_DATABASE_URL")
    if not url:
        raise RuntimeError("MIGRATION_DATABASE_URL is not set")
    return url


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def _run_online() -> None:
    engine = create_async_engine(_migration_url())
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    context.configure(url=_migration_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(_run_online())
