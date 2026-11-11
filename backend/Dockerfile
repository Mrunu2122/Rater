# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend with Tesseract OCR
FROM python:3.12-slim

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pydantic \
    pydantic-settings \
    sqlalchemy \
    aiosqlite \
    asyncpg \
    psycopg2-binary \
    boto3 \
    google-genai \
    openpyxl \
    pdfplumber \
    pymupdf \
    pytesseract \
    pillow \
    python-multipart \
    httpx

# Copy backend application and data
COPY backend/ /app/backend/
COPY data/ /app/data/

# Copy built frontend assets to FastAPI static mount location
COPY --from=frontend-builder /build/dist /app/frontend/dist

ENV ENVIRONMENT=production
ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
