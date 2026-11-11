import pytest
import os
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.storage.db import init_db_sync

@pytest.fixture(autouse=True)
def setup_db():
    init_db_sync()

@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["gridsLoaded"] == 4

@pytest.mark.anyio
async def test_get_grids():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/grids")
        assert resp.status_code == 200
        grids = resp.json()
        assert len(grids) == 4
        assert any(g["insurerId"] == "godigit" for g in grids)
        assert any(g["insurerId"] == "reliance" for g in grids)
        assert any(g["insurerId"] == "tata_aig" for g in grids)
        assert any(g["insurerId"] == "hdfc_ergo" for g in grids)

@pytest.mark.anyio
async def test_get_bench():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/bench")
        assert resp.status_code == 200
        bench = resp.json()
        assert len(bench) == 4

@pytest.mark.anyio
async def test_upload_invalid_file():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}
        resp = await client.post("/api/runs", files=files)
        assert resp.status_code == 400
        assert "magic bytes" in resp.json()["detail"]

@pytest.mark.anyio
async def test_upload_valid_pdf_queued():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        fake_pdf = b"%PDF-1.5 test content"
        files = {"file": ("dummy.pdf", fake_pdf, "application/pdf")}
        resp = await client.post("/api/runs", files=files)
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] in ["queued", "saved"]
        run_id = data["id"]
        
        # Query detail
        detail_resp = await client.get(f"/api/runs/{run_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == run_id
