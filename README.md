# Motor Insurance Brokerage Commission Resolver

A production-quality motor insurance commission resolver engine and web application built for the Vaatun Insurance Rater Agent Challenge. The system extracts policy facts from PDF motor policies, resolves exact OD (Own Damage) and TP (Third Party) brokerage commission rates against authoritative insurer commission grids, and provides fully auditable decision traces with cell and page citations.

---

## Architecture & Storage Overview

### 1. Persistence & Durability
- **Metadata & Decision Traces**: Stored in a relational database via SQLAlchemy / asyncpg / aiosqlite. In production, this runs against **PostgreSQL** (`DATABASE_URL=postgresql+asyncpg://...`). In local development and testing, it gracefully supports SQLite with write-ahead logging.
- **Raw Policy PDFs**: Stored in an **S3-compatible Object Store** (`STORAGE_BACKEND=s3`), targeting **AWS S3** or **Supabase Storage**. When running locally, MinIO or a persistent local disk directory fallback (`STORAGE_LOCAL_DIR`) is used. Policy files are never stored ephemerally; files are indexed with SHA-256 hashes and can be retrieved or audited at any time.

### 2. Gemini Extraction Pipeline
- **Model**: `gemini-3.5-flash` via the official Google GenAI SDK (`google-genai` v3.0.0+).
- **Interface**: Implemented behind an abstract `FactExtractor` interface (`backend/app/extraction/base.py`) allowing zero-overhead swapping with local OCR/regex fallbacks (such as Tesseract OCR included in `backend/Dockerfile`).
- **Structured JSON Schema**: Gemini receives PDF page images along with a strict Pydantic JSON response schema, with temperature set to `0.0` for deterministic extraction.
- **Privacy & Security**: Policy PDFs are transmitted over TLS to the Gemini API exclusively for extraction. No API keys are bundled in client assets or logged. `GEMINI_API_KEY` is loaded strictly from the backend server environment (`.env`).

---

## Assumptions & Doctrine

The engine operates strictly under the binding decisions established for the challenge:

1. **Geography Keys (Binding Decision 1)**:
   - A geography key (zone, cluster, or column) is mapped **strictly** from:
     - (a) An in-grid lookup table (e.g., Go Digit `4W  RTO` sheet, Reliance `RTO List` sheet), or
     - (b) A location explicitly printed on the policy (state or city) matched by string name to a grid column/label (e.g., HDFC ERGO `HARYANA` -> Zone-2; Tata AIG `New Delhi, DELHI` -> column `DELHI`).
   - Prefix guessing based on RTO license plate codes (e.g., guessing `HR-26` means Haryana, or `DL-9C` means Delhi) is strictly forbidden across all insurers. If only an RTO code exists without an in-grid mapping table, the lookup terminates with `ambiguous` or `unsupported`.

2. **GWP & Volume Rules**:
   - Tabulated per-policy rates are resolved deterministically.
   - Per-policy slab thresholds (such as HDFC ERGO Net OD ₹8,053 falling in `<10k`) resolve with volume caveats logged in the trace.
   - Refusal doctrine: A rate is marked `unsupported` when the grid itself explicitly states that the tabulated figure is merely a base or partial rate and that final payable rates depend on external, unstated agency-level GWP volumes or incremental payouts (e.g., Tata AIG `Pvtcar!F3` and `General Guidelines!C5`). In such cases, the candidate base rate (e.g. 38.0%) is preserved in the trace as `baseRatePercent` with exact cell citations (`Pvtcar!V511:V535`).

3. **Grid Effective Dates**:
   - A grid version mismatch is considered a hard failure only if the grid explicitly states a closed validity window that excludes the policy issuance/start date. Open-ended grids or month headers (such as Reliance `FEB 26` against a December 2025 policy) are resolved with an explicit date caveat and audit note.

4. **Exact Slab Boundaries**:
   - Ambiguous boundary values (e.g., exact ₹10,000 when slabs are `<10k` vs `>10-50k`) resolve to status `ambiguous`, identifying both candidate rows and the missing boundary rule.

5. **Footnote Application**:
   - Footnotes are evaluated deterministically with their mathematical interpretations recorded. For Reliance footnote H3 ("5% lesser" for vehicles < 1000 cc), the rule applies as percentage points (22.5% - 5.0% = 17.5%), with the alternative multiplicative interpretation (21.375%) logged in the decision trace. TP rates are marked `not published` citing footnote H2 (`payout will made on OD Premium`).

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+ (for building the frontend)
- (Optional) Docker & Docker Compose

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example ../rater/.env
# Edit rater/.env to add your GEMINI_API_KEY
```

To verify your Gemini setup:
```bash
python scripts/check_gemini.py
```

### 2. Frontend Setup & Build
```bash
cd frontend
npm install
npm run build
```
The production bundle is generated into `frontend/dist` and is automatically served by the FastAPI application.

### 3. Run the Application
```bash
cd backend
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Running Tests & Verifications

```bash
# Verify checksums of challenge assets
python scripts/verify_checksums.py

# Run golden policy resolver tests
python -m pytest backend/tests/golden/ -v

# Run API & integration tests
python -m pytest backend/tests/integration/ -v
```

---

## Output Benchmark Artifacts

The resolved outputs for the 4 benchmark policies are generated in `outputs/`:
- `outputs/hdfc-ergo.json`: Status `resolved` (OD: 15.0% in `<10k`, TP: 0.0% not covered).
- `outputs/reliance.json`: Status `resolved` (OD: 17.5% with 5% lesser deduction applied, TP: not published citing H2).
- `outputs/godigit.json`: Status `resolved` (OD: 20.0%, TP: 2.5% citing Non-CV TP).
- `outputs/tata-aig.json`: Status `unsupported` (TP unsupported citing `Pvtcar!F3` GWP incremental doctrine; candidate base 38.0% logged with citations `Pvtcar!V511:V535`).
