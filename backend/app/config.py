import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_FALLBACK_MODEL: str = ""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rater"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/rater"
    
    # Object Storage (S3 / Supabase Storage / MinIO)
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "policies"
    S3_REGION: str = "us-east-1"
    
    # Environment
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
