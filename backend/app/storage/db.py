import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings
from backend.app.storage.models import Base

# Support SQLite fallback for local test execution if postgres is offline
db_url = settings.DATABASE_URL
sync_db_url = settings.DATABASE_URL_SYNC

if "sqlite" in db_url:
    async_engine = create_async_engine(db_url, echo=False)
    sync_engine = create_engine(sync_db_url, echo=False)
else:
    try:
        async_engine = create_async_engine(db_url, echo=False)
        sync_engine = create_engine(sync_db_url, echo=False)
    except Exception:
        # Fallback to local SQLite for isolated testing
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
