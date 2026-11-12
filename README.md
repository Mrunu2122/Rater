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

- **Production Mode (`APP_ENV=production`):**
  - Requires **PostgreSQL** (`DATABASE_URL`) and **S3** object storage credentials (`S3_BUCKET_NAME`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`).
  - The application strictly refuses to start on SQLite or local disk in production mode.
- **Development Mode (`APP_ENV=dev`):**
  - Uses SQLite (`data/rater.db`) and local disk storage (`data/storage/`).
- **Persistence Across Restarts:**
  - Policy PDFs are hashed via SHA-256 and stored in the object store.
  - All run states (`extracting`, `resolving`, `saved`, `failed`) are tracked in the database.
  - On application startup, a recovery hook recovers interrupted transient runs.

---

## 3. Gemini API Processing Notice
- Uploaded policy PDFs are ingested as 100 DPI page images and sent to Google Gemini (`gemini-3.5-flash`) for multi-page visual extraction.
- The Gemini API key is managed exclusively on the backend (`rater/.env` / environment) and is never exposed to the frontend.

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
