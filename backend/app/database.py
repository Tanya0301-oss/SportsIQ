"""
SQLAlchemy async database setup.
Uses SQLite (aiosqlite) locally, PostgreSQL (asyncpg) in production.
"""
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Fix SQLite check_same_thread issue
connect_args = {}
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI dependency for DB session."""
    async with AsyncSessionLocal() as session:
        yield session
