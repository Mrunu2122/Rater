import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

from pydantic import ConfigDict, model_validator

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

    @model_validator(mode="after")
    def validate_production_env(self):
        if self.APP_ENV == "production":
            if not self.DATABASE_URL:
                raise ValueError("DATABASE_URL is required in production.")
            if not ("postgres" in self.DATABASE_URL or "postgresql" in self.DATABASE_URL):
                raise ValueError("PostgreSQL is required in production; SQLite/local disk only permitted in dev.")
            if not self.S3_BUCKET_NAME:
                raise ValueError("S3_BUCKET_NAME is required in production.")
            if not self.S3_ACCESS_KEY or not self.S3_SECRET_KEY:
                raise ValueError("S3_ACCESS_KEY and S3_SECRET_KEY are required in production.")
        return self

settings = Settings()
