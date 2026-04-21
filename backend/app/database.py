from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

if settings.cloud_sql_instance:
    # Cloud Run: connect via Unix socket mounted at /cloudsql/{instance}
    # gcloud run deploy --set-cloudsql-instances adds this mount automatically.
    _socket_dir = f"/cloudsql/{settings.cloud_sql_instance}"
    _url = (
        f"postgresql+asyncpg://{settings.db_user}:{quote_plus(settings.db_password)}"
        f"@/{settings.db_name}"
    )
    engine = create_async_engine(
        _url,
        echo=settings.debug,
        pool_pre_ping=True,
        connect_args={"host": _socket_dir},
    )
else:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
