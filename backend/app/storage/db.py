import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings
from backend.app.storage.models import Base

db_url = settings.DATABASE_URL
sync_db_url = settings.DATABASE_URL_SYNC

if settings.APP_ENV == "production":
    if not db_url or "sqlite" in db_url:
        raise RuntimeError("Production requires a valid PostgreSQL database URL.")
    async_engine = create_async_engine(db_url, echo=False)
    sync_engine = create_engine(sync_db_url or db_url.replace("+asyncpg", ""), echo=False)
else:
    # Dev / Test environment: Use Postgres if provided, else use persistent SQLite
    if db_url and "postgres" in db_url:
        async_engine = create_async_engine(db_url, echo=False)
        sync_engine = create_engine(sync_db_url or db_url.replace("+asyncpg", ""), echo=False)
    elif db_url and "sqlite" in db_url:
        async_engine = create_async_engine(db_url, echo=False)
        sync_engine = create_engine(sync_db_url or db_url.replace("+aiosqlite", ""), echo=False)
    else:
        sqlite_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "rater.db")
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        async_engine = create_async_engine(f"sqlite+aiosqlite:///{sqlite_path}")
        sync_engine = create_engine(f"sqlite:///{sqlite_path}")

AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)
SyncSessionLocal = sessionmaker(sync_engine)

def init_db_sync():
    Base.metadata.create_all(bind=sync_engine)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
