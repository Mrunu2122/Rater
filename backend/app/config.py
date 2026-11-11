import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    # Environment: 'production', 'staging', or 'dev'/'development'
    APP_ENV: str = "dev"
    
    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_FALLBACK_MODEL: str = ""
    
    # Database
    DATABASE_URL: str = ""
    DATABASE_URL_SYNC: str = ""
    
    # Object Storage (S3 / Supabase Storage / MinIO)
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "us-east-1"
    
    PORT: int = 8000
    HOST: str = "0.0.0.0"

settings = Settings()

# Validation rule: With APP_ENV=production, app MUST refuse to start unless DATABASE_URL (Postgres) and S3_* are present.
if settings.APP_ENV == "production":
    errors = []
    if not settings.DATABASE_URL or not ("postgres" in settings.DATABASE_URL or "postgresql" in settings.DATABASE_URL):
        errors.append("DATABASE_URL must be set to a valid PostgreSQL connection string in production.")
    if not settings.S3_ACCESS_KEY or not settings.S3_SECRET_KEY or not settings.S3_BUCKET_NAME:
        errors.append("S3_ACCESS_KEY, S3_SECRET_KEY, and S3_BUCKET_NAME must all be set in production.")
    if errors:
        raise RuntimeError(f"PRODUCTION CONFIGURATION ERROR:\n" + "\n".join(f"- {e}" for e in errors))
