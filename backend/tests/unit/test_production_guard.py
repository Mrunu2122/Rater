import pytest
from backend.app.config import Settings

def test_production_guard_fails_without_postgres():
    with pytest.raises(ValueError, match="DATABASE_URL is required in production"):
        Settings(
            APP_ENV="production",
            DATABASE_URL="", # Missing Postgres
            S3_BUCKET_NAME="bucket",
            S3_ACCESS_KEY="key",
            S3_SECRET_KEY="secret",
            GEMINI_API_KEY="dummy"
        )

def test_production_guard_fails_with_sqlite():
    with pytest.raises(ValueError, match="PostgreSQL is required in production"):
        Settings(
            APP_ENV="production",
            DATABASE_URL="sqlite+aiosqlite:///data/rater.db", # SQLite disallowed
            S3_BUCKET_NAME="bucket",
            S3_ACCESS_KEY="key",
            S3_SECRET_KEY="secret",
            GEMINI_API_KEY="dummy"
        )

def test_production_guard_fails_without_s3():
    with pytest.raises(ValueError, match="S3_BUCKET_NAME is required in production"):
        Settings(
            APP_ENV="production",
            DATABASE_URL="postgresql+asyncpg://user:pass@host/db",
            S3_BUCKET_NAME="", # Missing S3
            GEMINI_API_KEY="dummy"
        )
