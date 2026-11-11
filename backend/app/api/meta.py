from fastapi import APIRouter
from backend.app.config import settings
from backend.app.storage.object_store import object_store
from backend.app.grids.registry import registry

router = APIRouter(prefix="/api", tags=["meta"])

@router.get("/health")
async def health_check():
    db_backend = "sqlite" if ("sqlite" in (settings.DATABASE_URL or "") or not settings.DATABASE_URL) else "postgresql"
    storage_backend = "s3" if object_store.is_s3 else "local_disk"
    
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "database": {
            "backend": db_backend,
            "url_configured": bool(settings.DATABASE_URL)
        },
        "storage": {
            "backend": storage_backend,
            "bucket": settings.S3_BUCKET_NAME if object_store.is_s3 else None
        },
        "gemini": {
            "model": settings.GEMINI_MODEL,
            "api_key_configured": bool(settings.GEMINI_API_KEY)
        }
    }

@router.get("/grids")
async def get_grids_metadata():
    return {
        "count": len(registry.grids),
        "grids": [
            {
                "insurer_slug": g.insurerId,
                "insurer_name": g.insurerName,
                "version_name": g.fileName,
                "effective_from": g.effectiveFrom,
                "rule_count": len(g.rules),
                "mapping_count": len(g.geographyMapping)
            }
            for g in registry.grids.values()
        ]
    }
