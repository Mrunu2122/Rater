import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import Response, JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List
from backend.app.storage.db import get_db, AsyncSessionLocal
from backend.app.storage.models import RunModel
from backend.app.storage.object_store import object_store
from backend.app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/runs", tags=["runs"])

async def run_background_analysis(run_id: str):
    async with AsyncSessionLocal() as session:
        await analysis_service.process_run(session, run_id)

@router.post("", status_code=202)
async def upload_policy(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db)
):
    # Validate magic bytes for PDF (%PDF)
    contents = await file.read()
    if not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid file format: must be a valid PDF document (magic bytes %PDF required).")
    if len(contents) > 52428800: # 50 MB
        raise HTTPException(status_code=400, detail="File too large: maximum upload size is 50 MB.")
        
    run = await analysis_service.create_run(session, file.filename, contents)
    
    if run.status != "saved":
        background_tasks.add_task(run_background_analysis, run.id)
        
    return {
        "id": run.id,
        "fileName": run.file_name,
        "status": run.status,
        "isDuplicate": run.is_duplicate,
        "message": "Policy uploaded and queued for analysis." if run.status != "saved" else "Identical policy retrieved from history."
    }

@router.get("")
async def list_runs(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50),
    session: AsyncSession = Depends(get_db)
):
    stmt = select(RunModel).order_by(desc(RunModel.created_at)).limit(limit)
    if status and status != "all":
        stmt = stmt.where(RunModel.status == status)
    if search:
        stmt = stmt.where(RunModel.file_name.ilike(f"%{search}%"))
        
    res = await session.execute(stmt)
    runs = res.scalars().all()
    
    return [
        {
            "id": r.id,
            "fileName": r.file_name,
            "fileSizeBytes": r.file_size_bytes,
            "status": r.status,
            "createdAt": r.created_at.isoformat(),
            "completedAt": r.completed_at.isoformat() if r.completed_at else None,
            "isDuplicate": r.is_duplicate,
            "rates": r.rates,
            "confidence": r.confidence
        }
        for r in runs
    ]

@router.get("/{run_id}")
async def get_run(run_id: str, session: AsyncSession = Depends(get_db)):
    stmt = select(RunModel).where(RunModel.id == run_id)
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
        
    return {
        "id": run.id,
        "fileName": run.file_name,
        "fileSizeBytes": run.file_size_bytes,
        "pdfSha256": run.pdf_sha256,
        "status": run.status,
        "createdAt": run.created_at.isoformat(),
        "completedAt": run.completed_at.isoformat() if run.completed_at else None,
        "gridChecksum": run.grid_checksum_sha256,
        "resolverVersion": run.resolver_version,
        "modelId": run.model_id,
        "facts": run.facts,
        "rates": run.rates,
        "confidence": run.confidence,
        "trace": run.trace,
        "rawExtractionJson": run.raw_extraction_json,
        "errorMessage": run.error_message,
        "isDuplicate": run.is_duplicate
    }

@router.get("/{run_id}/pdf")
async def get_run_pdf(run_id: str, session: AsyncSession = Depends(get_db)):
    stmt = select(RunModel).where(RunModel.id == run_id)
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
        
    pdf_bytes = object_store.get_pdf(run.pdf_storage_path)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={run.file_name}"}
    )

@router.get("/{run_id}/export")
async def export_run_json(run_id: str, session: AsyncSession = Depends(get_db)):
    stmt = select(RunModel).where(RunModel.id == run_id)
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
        
    data = {
        "id": run.id,
        "fileName": run.file_name,
        "pdfSha256": run.pdf_sha256,
        "status": run.status,
        "createdAt": run.created_at.isoformat(),
        "facts": run.facts,
        "rates": run.rates,
        "confidence": run.confidence,
        "trace": run.trace
    }
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename=run_{run.id}.json"}
    )

@router.post("/{run_id}/rerun", status_code=202)
async def rerun_analysis(
    run_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db)
):
    stmt = select(RunModel).where(RunModel.id == run_id)
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
        
    run.status = "queued"
    run.error_message = None
    await session.commit()
    background_tasks.add_task(run_background_analysis, run.id)
    return {"id": run.id, "status": "queued", "message": "Re-run started."}
