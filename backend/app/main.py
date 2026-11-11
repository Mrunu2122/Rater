import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select, update
from backend.app.config import settings
from backend.app.storage.db import init_db_sync, AsyncSessionLocal
from backend.app.storage.models import RunModel
from backend.app.api.runs import router as runs_router, run_background_analysis
from backend.app.api.meta import router as meta_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rater")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize schema
    init_db_sync()
    logger.info("Database initialized.")
    
    # 2. Startup recovery: Find any stuck runs in transient state and recover or re-queue them
    async with AsyncSessionLocal() as session:
        stmt = (
            update(RunModel)
            .where(RunModel.status.in_(["extracting", "resolving"]))
            .values(
                status="failed",
                error_message="Analysis was interrupted by server restart. Please click Re-run."
            )
        )
        await session.execute(stmt)
        await session.commit()
        logger.info("Startup recovery complete: recovered interrupted runs.")
        
    yield

app = FastAPI(title="Insurance Rater Agent API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router)
app.include_router(meta_router)

# Mount frontend static files if built
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
