# Production Deployment Guide: Supabase + Render

This guide outlines step-by-step instructions for deploying the **Vaatun Insurance Rater Agent** to production with PostgreSQL persistence and S3 object storage.

---

## 1. Prerequisites
- A **Render.com** account
- A **Supabase.com** account (or AWS account for Postgres & S3)
- A **Google AI Studio** Gemini API Key

---

## 2. Supabase Setup (Postgres + S3-Compatible Storage)

### Step 1: Create a PostgreSQL Database
1. Create a new project in Supabase.
2. In **Project Settings** > **Database**, locate your connection string (URI mode):
   ```text
   postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
3. Set `DATABASE_URL` with the async driver:
   ```text
   postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

### Step 2: Create Storage Bucket
1. Go to **Storage** > **New Bucket**.
2. Name the bucket `policies`.
3. Set access to **Private** (authenticated via S3 credentials).

### Step 3: Generate S3 Credentials
1. Go to **Project Settings** > **Storage** > **S3 Access Keys**.
2. Click **Create new access key**.
3. Copy:
   - `S3_ENDPOINT_URL`: `https://[REF].supabase.co/storage/v1/s3`
   - `S3_ACCESS_KEY`: Access Key ID
   - `S3_SECRET_KEY`: Secret Access Key
   - `S3_BUCKET_NAME`: `policies`

---

## 3. Render Deployment

### Step 1: Deploy with Web Service
1. Connect your GitHub repository to Render.
2. Select **Web Service** > **Build and deploy from a Dockerfile**.
3. Choose plan (`Starter` or higher recommended for 512MB+ RAM).

### Step 2: Configure Environment Variables
Set the following environment variables in Render:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `APP_ENV` | Must be `production` | `production` |
| `GEMINI_API_KEY` | Google AI Studio Key | `your_gemini_api_key_here` |
| `GEMINI_MODEL` | Default extraction model | `gemini-3.5-flash` |
| `DATABASE_URL` | Async PostgreSQL URL | `postgresql+asyncpg://postgres:...` |
| `DATABASE_URL_SYNC` | Sync PostgreSQL URL for migrations | `postgresql://postgres:...` |
| `S3_ENDPOINT_URL` | Supabase / AWS S3 Endpoint | `https://[REF].supabase.co/storage/v1/s3` |
| `S3_ACCESS_KEY` | S3 Access Key ID | `[KEY_ID]` |
| `S3_SECRET_KEY` | S3 Secret Access Key | `[SECRET]` |
| `S3_BUCKET_NAME` | Storage Bucket Name | `policies` |
| `S3_REGION` | S3 Region | `us-east-1` |

### Step 3: Health Verification
Once deployed, check:
```bash
curl https://your-service.onrender.com/api/health
```
Expected response:
```json
{
  "status": "healthy",
  "app_env": "production",
  "database": {
    "backend": "postgresql",
    "url_configured": true
  },
  "storage": {
    "backend": "s3",
    "bucket": "policies"
  },
  "gemini": {
    "model": "gemini-3.5-flash",
    "api_key_configured": true
  }
}
```
