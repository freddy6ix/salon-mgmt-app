import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Support two layouts:
#   Local dev:  migrations/ is at repo root, app code is at backend/app/
#   Docker:     migrations/ is at /app/migrations/, app code is at /app/app/
_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_base, "backend"))  # local dev
sys.path.insert(0, _base)                            # Docker container

from app.config import settings
from app.database import Base
import app.models  # noqa: F401 — registers all models for autogenerate

alembic_cfg = context.config
alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = alembic_cfg.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    if settings.cloud_sql_instance:
        from google.cloud.sql.connector import AsyncConnector

        connector = AsyncConnector()

        async def getconn():
            return await connector.connect(
                settings.cloud_sql_instance,
                "asyncpg",
                user=settings.db_user,
                password=settings.db_password,
                db=settings.db_name,
            )

        connectable = create_async_engine("postgresql+asyncpg://", async_creator=getconn)
    else:
        connectable = create_async_engine(settings.database_url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

    if settings.cloud_sql_instance:
        await connector.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
