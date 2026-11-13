# Vaatun Insurance Rater Agent

Production-grade motor insurance policy brokerage commission resolver for the Vaatun Insurance Rater Agent Challenge.

The system extracts parameters from motor policy schedules using Google Gemini, executes deterministic grid resolution against authoritative insurer rate sheets (Go Digit, Reliance General, Tata AIG, HDFC ERGO), and provides comprehensive audit trails with exact cell and page citations.

---

## 1. Core Doctrines & Deterministic Assumptions

### A. Geography Keys & No Code-Prefix Guessing
- Geography keys may **only** be derived from:
  1. An authoritative in-grid mapping table (e.g. Go Digit `4W  RTO` sheet or Reliance `RTO List` sheet), or
  2. Exact printed location text on the policy matched by name to a grid label.
- **Zero code-prefix guessing:** RTO codes not explicitly matched halt deterministic resolution with `status: unsupported`.

### B. Tata AIG Base-Only COA Refusal
- Tata AIG private car rates are refused with `status: unsupported`.
- Cells `Pvtcar!F3` and `General Guidelines!C5` explicitly declare:
  > *"Below COA Rates would be Base Commission processed, Additionally GWP Based Rule will be Applicable"*
- Because broker portfolio Gross Written Premium (GWP) is an external dimension absent from individual policies, the final payable rate cannot be computed deterministically. Candidate base rates (e.g. 38.0% for Delhi CNG SATP renewal) are recorded in the trace.

### C. Grid Effective Date Caveat
- Reliance rater grid is titled `Reliance Broking Premier FEB 26 Grid.xlsx`. Policies with inception dates outside February 2026 receive an explicit audit caveat in their decision trace.

### D. Exact Slab Boundary Ambiguity
- HDFC ERGO rater defines slabs as `<10k` and `>10-50k`.
- Net OD premiums falling exactly on slab boundaries (₹10,000, ₹50,000, ₹100,000, ₹200,000) are mathematically undefined and halt deterministic resolution with `status: ambiguous`.

### E. Footnote H3 "<1000 CC" 5% Lesser Assumption
- Reliance grid Footnote H3 specifies: *"Payout for < 1000 CC, PO will be 5% lesser than the above Grid"*.
- The engine applies this as an additive reduction (e.g. `22.5% - 5.0% = 17.5%`) while documenting both additive and multiplicative (`22.5% × 0.95 = 21.375%`) interpretations in the decision trace.

### F. Missing Input vs Grid Gap (Ambiguity Doctrine)
- When a required fact is unprinted on a policy:
  - If all candidate rows in the grid yield the identical rate: resolves with lowered confidence noting the omission.
  - If candidate rows differ: halts deterministic resolution with `status: ambiguous`, listing all candidate rates.
  - **Example (Reliance):** Fuel is unprinted on the 15-page policy. In Delhi, candidate rates differ between Petrol (17.5%) and Diesel (5.0%), resulting in `status: ambiguous` when fuel is unextracted.

---

## 2. Storage, Durability & Persistence

- **Production Mode (`APP_ENV=production` on Vercel / Supabase):**
  - Persistence is powered by **PostgreSQL** (`DATABASE_URL=postgresql+asyncpg://...`) using Supabase's transaction pooler with `NullPool` and `statement_cache_size=0` to ensure no connection leakage across serverless invocations.
  - Policy PDFs are stored in private **S3-compatible Object Storage** (`S3_BUCKET_NAME`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`).
  - Production guard (`backend/app/config.py`) strictly enforces PostgreSQL and S3 configuration at startup; SQLite, `/tmp`, and local disk are completely disallowed in production.
  - All run states (`queued`, `extracting`, `resolving`, `saved`, `failed`) and timestamps (`created_at`, `updated_at`, `completed_at`) are written directly to PostgreSQL, surviving container recycling, serverless restarts, and redeployments.
  - Stale in-progress runs from aborted serverless executions are detected via `updated_at` timeout and can be recovered via `POST /api/runs/:id/rerun`.
- **Large Upload Architecture (Bypassing Vercel 4.5 MB Limit):**
  - Files over 4 MB bypass Vercel's 4.5 MB payload cap via Direct-to-Storage presigned URLs (`POST /api/uploads` -> browser `PUT` straight to S3/Supabase Storage -> `POST /api/runs` with `{ objectKey, fileName }`).
  - All pages of the policy are preserved and analyzed (no client-side page dropping).
  - Documents exceeding the 30-page ceiling are rejected server-side with a clear descriptive error.
  - *Supabase Storage CORS requirement:* The storage bucket must have CORS enabled for `GET, PUT, POST, HEAD` from your application domain.
- **Development Mode (`APP_ENV=dev`):**
  - Uses local SQLite and disk storage for offline testing and fast local CI runs.

---

## 3. Gemini API Processing Notice
- Uploaded policy PDFs are rendered at 150 DPI page images and sent to Google Gemini (`gemini-3.5-flash`, with `gemini-3.1-flash-lite`, `gemini-2.5-flash`, and `gemini-1.5-flash` fallbacks for 503 high-demand resilience) for multi-page visual extraction.
- The Gemini API key is managed exclusively on the backend and is never exposed to the client.

---

## 4. Running the Project

### Local Development
```powershell
# 1. Install backend requirements
pip install -r backend/requirements.txt

# 2. Run backend API & frontend server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to `http://localhost:8000`.

### Running Tests
```powershell
python -m pytest backend/tests -v --junitxml=pytest-report.xml
```
