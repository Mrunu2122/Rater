import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.storage.models import RunModel
from backend.app.storage.db import AsyncSessionLocal
from sqlalchemy import select

@pytest.mark.anyio
async def test_health_reports_backends():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "database" in data
        assert "storage" in data
        assert data["database"]["backend"] in ["sqlite", "postgresql"]
        assert data["storage"]["backend"] in ["local_disk", "s3"]

@pytest.mark.anyio
async def test_persistence_across_restart():
    # Insert a record, simulate restart by querying via fresh session
    async with AsyncSessionLocal() as session:
        run = RunModel(
            id="test-restart-run-123",
            pdf_sha256="dummy-sha256",
            file_name="test_restart.pdf",
            file_size_bytes=100,
            pdf_storage_path="local/test_restart.pdf",
            status="queued"
        )
        session.add(run)
        await session.commit()

    # Reconnect in a brand new async session
    async with AsyncSessionLocal() as new_session:
        stmt = select(RunModel).where(RunModel.id == "test-restart-run-123")
        result = await new_session.execute(stmt)
        persisted = result.scalar_one_or_none()
        assert persisted is not None
        assert persisted.id == "test-restart-run-123"
        assert persisted.status == "queued"
        
        # Cleanup
        await new_session.delete(persisted)
        await new_session.commit()
