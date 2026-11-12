import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.anyio
async def test_api_runs_endpoints_and_history():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create an initial run in this isolated test database
        dummy_pdf = b"%PDF-1.4\n%isolated test pdf\n%%EOF"
        upload_resp = await client.post("/api/runs", files={"file": ("history_test.pdf", dummy_pdf, "application/pdf")})
        assert upload_resp.status_code == 202
        created_id = upload_resp.json()["id"]

        # 1. Health check
        res_health = await client.get("/api/health")
        assert res_health.status_code == 200
        health_data = res_health.json()
        assert health_data["status"] == "healthy"
        assert "database" in health_data
        assert "storage" in health_data

        # 2. List runs with pagination and search
        res_list = await client.get("/api/runs?page=1&limit=5")
        assert res_list.status_code == 200
        runs_data = res_list.json()
        assert isinstance(runs_data, list)
        assert len(runs_data) > 0

        first_run = runs_data[0]
        run_id = first_run["id"]

        # 3. GET /api/runs/:id
        res_detail = await client.get(f"/api/runs/{run_id}")
        assert res_detail.status_code == 200
        assert res_detail.json()["id"] == run_id

        # 4. GET /api/runs/:id/export
        res_export = await client.get(f"/api/runs/{run_id}/export")
        assert res_export.status_code == 200
        assert "application/json" in res_export.headers.get("content-type", "")

        # 5. GET /api/runs/:id/pdf
        res_pdf = await client.get(f"/api/runs/{run_id}/pdf")
        assert res_pdf.status_code == 200
        assert "application/pdf" in res_pdf.headers.get("content-type", "")

        # 6. POST /api/runs/:id/rerun
        res_rerun = await client.post(f"/api/runs/{run_id}/rerun")
        assert res_rerun.status_code == 202
        assert res_rerun.json()["status"] == "queued"
