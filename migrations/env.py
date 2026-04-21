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
        from urllib.parse import quote_plus

        socket_dir = f"/cloudsql/{settings.cloud_sql_instance}"
        url = (
            f"postgresql+asyncpg://{settings.db_user}:{quote_plus(settings.db_password)}"
            f"@/{settings.db_name}"
        )
        print(f"[migration] Connecting via socket {socket_dir}", flush=True)
        connectable = create_async_engine(
            url,
            connect_args={"host": socket_dir},
        )
    else:
        connectable = create_async_engine(settings.database_url)

    print("[migration] Acquiring DB connection...", flush=True)
    async with connectable.connect() as connection:
        print("[migration] Connected — running migrations", flush=True)
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()
    print("[migration] Done", flush=True)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
