from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

if settings.cloud_sql_instance:
    from google.cloud.sql.connector import create_async_connector

    _connector = None

    async def _getconn():
        global _connector
        if _connector is None:
            _connector = await create_async_connector()
        return await _connector.connect(
            settings.cloud_sql_instance,
            "asyncpg",
            user=settings.db_user,
            password=settings.db_password,
            db=settings.db_name,
        )

    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=_getconn,
        echo=settings.debug,
        pool_pre_ping=True,
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
