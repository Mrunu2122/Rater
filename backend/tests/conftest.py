import os
import pytest

# Ensure any module-level imports of db.py during test collection don't touch data/rater.db
os.environ["RATER_SQLITE_PATH"] = ":memory:"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.storage.models import Base
import backend.app.storage.db as db_mod
import backend.app.storage.object_store as store_mod

@pytest.fixture(autouse=True)
def isolate_db_and_storage(tmp_path, monkeypatch):
    """
    Ensure every test runs with an isolated temporary SQLite database
    and temporary storage directory, never touching or depending on data/rater.db.
    """
    tmp_db_path = tmp_path / "test_rater.db"
    tmp_storage_path = tmp_path / "test_storage"
    tmp_storage_path.mkdir(parents=True, exist_ok=True)
    
    # Configure isolated test engines
    async_db_url = f"sqlite+aiosqlite:///{tmp_db_path.as_posix()}"
    sync_db_url = f"sqlite:///{tmp_db_path.as_posix()}"
    
    test_async_engine = create_async_engine(async_db_url, echo=False)
    test_sync_engine = create_engine(sync_db_url, echo=False)
    
    # Create schema in the temp database
    Base.metadata.create_all(bind=test_sync_engine)
    
    TestAsyncSessionLocal = async_sessionmaker(test_async_engine, expire_on_commit=False)
    TestSyncSessionLocal = sessionmaker(test_sync_engine)
    
    # Patch db module attributes
    monkeypatch.setattr(db_mod, "async_engine", test_async_engine)
    monkeypatch.setattr(db_mod, "sync_engine", test_sync_engine)
    monkeypatch.setattr(db_mod, "AsyncSessionLocal", TestAsyncSessionLocal)
    monkeypatch.setattr(db_mod, "SyncSessionLocal", TestSyncSessionLocal)
    
    # Also patch direct imports in other modules
    import backend.app.api.runs as runs_api
    import backend.app.main as main_mod
    monkeypatch.setattr(runs_api, "AsyncSessionLocal", TestAsyncSessionLocal)
    monkeypatch.setattr(main_mod, "AsyncSessionLocal", TestAsyncSessionLocal)
    
    # Override get_db dependency for FastAPI
    async def override_get_db():
        async with TestAsyncSessionLocal() as session:
            yield session
            
    monkeypatch.setattr(db_mod, "get_db", override_get_db)
    
    # Patch object store local path to point to temp storage
    orig_upload_pdf = store_mod.ObjectStore.upload_pdf
    def mocked_upload_pdf(self, storage_key: str, data: bytes) -> str:
        if self.is_s3 and self.client:
            return orig_upload_pdf(self, storage_key, data)
        target_file = tmp_storage_path / storage_key.replace("/", "_")
        target_file.write_bytes(data)
        return str(target_file)
        
    def mocked_get_pdf(self, storage_key: str) -> bytes:
        if self.is_s3 and self.client:
            return self.client.get_object(Bucket=self.bucket, Key=storage_key)["Body"].read()
        target_file = tmp_storage_path / storage_key.replace("/", "_")
        if target_file.exists():
            return target_file.read_bytes()
        # Fallback to direct path if saved as absolute path
        if os.path.exists(storage_key):
            with open(storage_key, "rb") as f:
                return f.read()
        raise FileNotFoundError(f"Mocked storage could not find {storage_key}")
        
    monkeypatch.setattr(store_mod.ObjectStore, "upload_pdf", mocked_upload_pdf)
    monkeypatch.setattr(store_mod.ObjectStore, "get_pdf", mocked_get_pdf)
    
    yield
