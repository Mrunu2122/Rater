# Deployment Guide for Rater

This guide provides click-by-click instructions to deploy Rater into production using **Supabase** (PostgreSQL + S3-compatible Storage) and **Render** (Docker Web Service).

---

## Step 1: Set Up Supabase (Database & Object Storage)

1. Sign in to [Supabase](https://supabase.com/).
2. Create a new project named `rater-db`. Choose a strong database password.
3. Under **Project Settings -> Database**:
   * Copy the **Connection String** (URI mode, `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`).
   * Set `DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
   * Set `DATABASE_URL_SYNC=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
4. Under **Storage**:
   * Create a new bucket named `policies`. Set it to **Private**.
5. Under **Project Settings -> Storage -> S3 Credentials**:
   * Generate an **S3 Access Key** and **Secret Key**.
   * Note the S3 endpoint URL (e.g. `https://[ref].supabase.co/storage/v1/s3`).

---

## Step 2: Deploy Web Service to Render

1. Sign in to [Render](https://render.com/).
2. Click **New + -> Web Service**.
3. Connect your GitHub repository containing the `rater` code.
4. Select **Docker** environment. Render will automatically detect `backend/Dockerfile`.
5. Set the following **Environment Variables**:
   * `ENVIRONMENT`: `production`
   * `PORT`: `8000`
   * `GEMINI_API_KEY`: Your Google AI Studio API key (`AIza...`)
   * `GEMINI_MODEL`: `gemini-3.5-flash`
   * `DATABASE_URL`: Your Supabase async connection string (`postgresql+asyncpg://...`)
   * `DATABASE_URL_SYNC`: Your Supabase sync connection string (`postgresql://...`)
   * `S3_ENDPOINT_URL`: Your Supabase Storage S3 endpoint URL (`https://[ref].supabase.co/storage/v1/s3`)
   * `S3_ACCESS_KEY`: Your Supabase S3 Access Key ID
   * `S3_SECRET_KEY`: Your Supabase S3 Secret Access Key
   * `S3_BUCKET_NAME`: `policies`
   * `S3_REGION`: `us-east-1` (or your project's region)
6. Click **Create Web Service**. Render will build the multi-stage Docker container (compiling React frontend and launching FastAPI + Tesseract) and assign a public URL (e.g. `https://rater-app.onrender.com`).

---

## Step 3: Verification on Live URL

1. Open `https://your-app.onrender.com/api/health` to confirm database, storage, and all 4 grids are loaded.
2. In the browser, upload a motor policy PDF that is **NOT** part of the 4 samples.
3. Verify that the run resolves with full trace and cell/page citations.
4. Refresh the page and open the **History** tab to verify that the run persists across browser reloads.
5. In Render dashboard, trigger a manual deploy / restart and confirm that the run history remains completely intact.
