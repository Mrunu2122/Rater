import io
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.anyio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "storage" in data
        assert "gemini" in data

@pytest.mark.anyio
async def test_get_grids():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/grids")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 4
        slugs = [g["insurer_slug"] for g in data["grids"]]
        assert "hdfc_ergo" in slugs
        assert "reliance" in slugs
        assert "godigit" in slugs
        assert "tata_aig" in slugs

@pytest.mark.anyio
async def test_upload_invalid_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("test.txt", b"plain text is not a pdf", "text/plain")}
        resp = await ac.post("/api/runs", files=files)
        assert resp.status_code == 400
        assert "magic bytes %PDF" in resp.json()["detail"]

@pytest.mark.anyio
async def test_upload_valid_pdf_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        dummy_pdf = b"%PDF-1.4\n%dummy pdf content for api endpoint testing\n%%EOF"
        files = {"file": ("dummy.pdf", dummy_pdf, "application/pdf")}
        resp = await ac.post("/api/runs", files=files)
        assert resp.status_code == 202
        data = resp.json()
        assert "id" in data
        run_id = data["id"]
        
        # Test pagination and list endpoint
        list_resp = await ac.get("/api/runs?page=1&limit=10")
        assert list_resp.status_code == 200
        runs_list = list_resp.json()
        assert any(r["id"] == run_id for r in runs_list)
        
        # Test get run detail
        detail_resp = await ac.get(f"/api/runs/{run_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["id"] == run_id
        assert detail_data["fileName"] == "dummy.pdf"
        assert "pdfSha256" in detail_data
        
        # Test get run PDF
        pdf_resp = await ac.get(f"/api/runs/{run_id}/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert pdf_resp.content.startswith(b"%PDF")
        
        # Test export run json
        export_resp = await ac.get(f"/api/runs/{run_id}/export")
        assert export_resp.status_code == 200
        export_data = export_resp.json()
        assert export_data["id"] == run_id
        
        # Test duplicate upload
        dup_resp = await ac.post("/api/runs", files={"file": ("dummy_dup.pdf", dummy_pdf, "application/pdf")})
        assert dup_resp.status_code == 202
        dup_data = dup_resp.json()
        assert dup_data["isDuplicate"] is True
        
        # Test rerun
        rerun_resp = await ac.post(f"/api/runs/{run_id}/rerun")
        assert rerun_resp.status_code == 202
        assert rerun_resp.json()["status"] == "queued"
