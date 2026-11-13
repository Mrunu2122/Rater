import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings
from backend.app.storage.models import Base

logger = logging.getLogger("rater.db")

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
        # In serverless environments (like Vercel AWS Lambda), the only writable directory is /tmp
        default_db = "/tmp/rater.db" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "rater.db")
        sqlite_path = os.environ.get("RATER_SQLITE_PATH", default_db)
        dir_name = os.path.dirname(sqlite_path)
        if dir_name and not os.environ.get("PYTEST_CURRENT_TEST"):
            os.makedirs(dir_name, exist_ok=True)
        async_engine = create_async_engine(f"sqlite+aiosqlite:///{sqlite_path}")
        sync_engine = create_engine(f"sqlite:///{sqlite_path}")

AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)
SyncSessionLocal = sessionmaker(sync_engine)

def init_db_sync():
    # If using postgresql+asyncpg without a separate sync driver, or sqlite
    try:
        Base.metadata.create_all(bind=sync_engine)
    except Exception as e:
        logger.warning(f"Sync create_all failed: {e}. Falling back to async engine run_sync.")

async def init_db_async():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
