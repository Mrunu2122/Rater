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

# Install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

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
