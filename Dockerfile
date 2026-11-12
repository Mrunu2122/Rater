# Multi-stage Docker build for Insurance Rater Agent
# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend with Tesseract OCR
FROM python:3.12-slim
WORKDIR /app

# System dependencies including Tesseract OCR for document inspection
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies directly
RUN pip install --no-cache-dir \
    fastapi==0.115.8 \
    uvicorn[standard]==0.34.0 \
    pydantic==2.10.6 \
    pydantic-settings==2.7.1 \
    sqlalchemy==2.0.38 \
    aiosqlite==0.21.0 \
    asyncpg==0.30.0 \
    psycopg2-binary==2.9.10 \
    boto3==1.36.21 \
    google-genai==1.2.0 \
    openpyxl==3.1.5 \
    pdfplumber==0.11.5 \
    pymupdf==1.25.3 \
    pytesseract==0.3.13 \
    pillow==11.1.0 \
    python-multipart==0.0.20 \
    httpx==0.28.1

# Copy backend application code and grid files
COPY backend/ /app/backend/
COPY raters/ /app/raters/
COPY data/raters/ /app/data/raters/

# Copy built frontend assets from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Set production environment defaults
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# Shell form CMD ensures $PORT provided by Render is dynamically bound
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
