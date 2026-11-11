# Progress Tracking - Vaatun Insurance Rater Agent Challenge

Last Updated: 2026-11-11T22:46:00+05:30

## Completed Deliverables

- [x] **Item A (Golden Policies & Regression Check)**:
  - Output files in `outputs/*.json` and `backend/tests/golden/test_golden_policies.py` verified:
    - Go Digit: OD `not_applicable`, TP 29.5% (`4W SATP!B293:E293`)
    - HDFC ERGO: OD 15.0% (`<10k` slab), TP `unsupported` (not published)
    - Reliance: OD 17.5% (`<1000cc` footnote H3 applied), TP `unsupported` (not published per H2)
    - Tata AIG: OD `not_applicable`, TP `unsupported` (GWP increment doctrine `Pvtcar!F3`, uncertified base 38.0% logged)
  - Golden pytest suite passes 5/5 tests.
- [x] **Item B (Storage & Durability Enforcements)**:
  - `backend/app/config.py`: Enforces `APP_ENV=production` hard failure if `DATABASE_URL` (Postgres) or `S3_*` credentials/bucket are missing. Local fallback restricted strictly to `APP_ENV=dev`.
  - `backend/app/api/meta.py`: `/api/health` reports active database backend and storage backend.
  - `backend/tests/integration/test_persistence.py`: Added persistence-across-restart test passing with new DB session.
- [x] **Item C (Endpoints & Pipeline)**:
  - `GET /api/runs`: Supports `status` filter, `search`, `page`, and `limit` pagination (sorted newest first).
  - `GET /api/runs/:id/pdf`: Streams policy PDF from object store with `inline` disposition.
  - `GET /api/runs/:id/export`: Downloads full run JSON as an attachment.
  - `POST /api/runs/:id/rerun`: Re-queues run and restarts background analysis.
  - Duplicate PDF detection using SHA-256 hash.
  - Async state machine (`queued` -> `extracting` -> `resolving` -> `saved` / `failed`) with server startup recovery for interrupted runs.
  - Metadata persistence: grid checksum, resolver version, model ID, raw extraction JSON.
  - `backend/tests/integration/test_api.py` passes 4/4 integration tests.
- [x] **Item D (Frontend UI Views)**:
  - App split into modular pages in `frontend/src/pages/`:
    - `AnalyzePage.tsx`: Drag & drop upload, polling status, and benchmark shortcuts.
    - `RunDetailPage.tsx`: OD/TP separate cards (handling `not_applicable` and `unsupported`), facts table with page badges and low-confidence flags, decision trace timeline with citations, PDF viewer, JSON export, and Re-run action.
    - `HistoryPage.tsx`: DB-backed audit table with search, status filters, and one-click reopening.
    - `GridsPage.tsx`: Displays metadata, rules count, and RTO mappings for all 4 rater grids.
    - `ArchitecturePage.tsx`: Durability, persistence, and deterministic resolution architecture.
  - Responsive light/dark theme toggle with design palette (`#f2ecdf` cream, `#1b1a22` dark ink, `#3b2fd1` indigo, Fraunces + JetBrains Mono).
  - Production bundle built cleanly to `frontend/dist`.
- [x] **Item E (Unit Test Suites)**:
  - `backend/tests/unit/test_resolver_rules.py`: Unit tests for rule types (TP-only OD `not_applicable`, slab boundary ambiguous, CC footnote deduction, Reliance H2 TP not published, Tata GWP refusal, missing geography mapping).
  - `backend/tests/unit/test_parser_coordinates.py`: Parser tests verifying coordinate citations across all 4 grids.
  - `backend/tests/unit/test_extraction_validation.py`: Extraction validation with mocked Gemini client.
  - All 11 unit tests pass in `pytest backend/tests/unit/`.
- [x] **Item F (Extraction & Live Outputs)**:
  - `scripts/generate_outputs.py --live`: Live extraction script with env check.
  - `README.md` provenance notice: Explains current `outputs/` are generated from verified ground truth facts and deterministic grid resolution.
- [x] **Item G (Grid Tabulation Inspection)**:
  - HDFC ERGO: PDF rater publishes flat percentages on OD premium without broker-level GWP incremental tiers (Page 1, Table 1-2 headers).
  - Reliance General: Base rates apply per policy slab with footnote adjustments (Cell H2, H3), no incremental broker GWP tier requirement.
  - Go Digit: SATP grid publishes final Max CD2 percentage payouts per cluster/age band (`4W SATP!B293:E293`), with no post-policy GWP increments required.

## Status

All items (A through G) completed, verified, and passing tests.
