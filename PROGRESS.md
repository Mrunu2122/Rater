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

## Completed Deliverables

- [x] **Item 1: Status Aggregation Doctrine & Component State `not_published`**:
  - Added `ComponentState.NOT_PUBLISHED` to `states.py` and frontend TypeScript interfaces (`client.ts`).
  - Added `backend/app/resolver/status_aggregation.py` to aggregate run status as the worst state among REQUIRED components, ignoring `not_applicable` and `not_published`.
  - Updated Reliance and HDFC ERGO resolvers to emit `not_published` for TP (strictly citing H2 / Table 1-2 headers).
  - Added 5 unit tests in `backend/tests/unit/test_status_aggregation.py` passing cleanly.
- [x] **Item 2: Missing Input != Grid Gap Doctrine**:
  - In `backend/app/resolver/resolver.py`: when required fact (fuel, cc, previous insurer) is missing/null, inspect candidate rules:
    - If candidate rows differ: return `ambiguous` with reason `"<fact> not extracted/printed on policy"`, listing candidate rates.
    - If all candidate rows agree: resolve with lowered confidence.
    - Never say "No matching rate rule" when cause is null input.
- [x] **Item 3: Business Type Rule**:
  - In `backend/app/extraction/gemini_extractor.py`: if `previousInsurer` is null or not printed, `businessType = "unknown"` (never rollover). Fixed UI display to show `unknown`.
- [x] **Item 4: Derived Vehicle Age**:
  - Implemented `backend/app/resolver/age_helper.py` computing `vehicleAgeYears = policyStartDateYear - (registrationYear or manufactureYear)`.
  - Displays calculation explanation (e.g. `2025 (policy start year) - 2020 (registration year) = 5 yrs`) instead of `null yrs`.
- [x] **Item 5: Reliance Extraction Analysis & Fuel Checking**:
  - Inspected Reliance sample PDF (`pvt-car-comprehensive-reliance.pdf` p.2). Fuel is **not printed** anywhere in the policy schedule.
  - Raw Gemini JSON extracts `fuel: null` / `lowConfidence: true`.
  - Reliance resolver follows Item 2: candidate Delhi rows differ between Petrol (17.5% with <1000cc) vs Diesel/EV (5.0%), deterministically resolving to `status: ambiguous`.
- [x] **Item 6: Duplicate PDF Handling & Auto-Re-Resolution**:
  - In `backend/app/services/analysis_service.py`: when duplicate PDF is uploaded, if stored `resolver_version` or `grid_checksum_sha256` differs from current rater grid, the system automatically re-resolves and marks `status = "re-resolved"`.
- [x] **Item 7: Live Benchmark Pipeline & Consistency**:
  - Benchmark cards now reflect the real pipeline results.
  - Live pipeline executed across all 4 samples, generating full comparison table.
- [x] **Item 8: Full Pytest Output**:
  - Ran `python -m pytest backend/tests/ -v`. All 27 tests passed cleanly (0 failures).

## Live Full-PDF Pipeline & Anti-Hardcoding Audit (Items 1-8 Complete)

- [x] **Item 1: Extraction Coverage (Whole PDF)**:
  - Upgraded `backend/app/extraction/gemini_extractor.py` to send up to 30 pages directly as 100 DPI page images to Gemini 3.5 Flash.
  - Successfully extracted all fields from the 12-page Tata AIG policy: Make `MARUTI`, Model `ZEN ESTILO`, Fuel `CNG`, RTO `DELHI` (found on Page 4), Previous Insurer `TATA AIG GENERAL INSURANCE CO.LTD.` (found on Page 11).
- [x] **Item 2: Strict Null Contract**:
  - Implemented sanitization ensuring missing facts are stored as Python/JSON `None` (null), with sentences moved to `uncertainty`.
  - Added schema validation tests in `backend/tests/unit/test_null_contract.py` (2/2 passing).
- [x] **Item 3: Status Aggregation**:
  - DB status, API response, and UI status badge strictly reflect the worst state among required components (`RunStatus.RESOLVED`, `RunStatus.UNSUPPORTED`, `RunStatus.AMBIGUOUS`), ignoring `not_applicable` and `not_published`.
- [x] **Item 4: Business Type**:
  - If `previousInsurer` is missing/null, `businessType = "unknown"` (never rollover). When previous insurer matches current insurer, sets `renewal`.
- [x] **Item 5: Derived Age & Non-Applicable Premiums**:
  - Derived `vehicleAgeYears` formatted as real years (e.g. `2026 - 2019 = 7 yrs`).
  - Formatted non-applicable premium rows (like OD premium on SATP) as `—` instead of `₹0`.
- [x] **Item 6: Anti-Hardcoding Audit**:
  - Verified and cleaned resolver logic: no reliance on filename strings, no fallback benchmark constants.
  - Added mutation tests in `backend/tests/unit/test_pure_resolver_mutations.py` proving the resolver is a pure function of `(facts, grid)`.
- [x] **Item 7: Duplicates & Live Benchmarks**:
  - Re-resolution on duplicate upload recomputes output if checksum/resolver version changed.
  - Benchmarks reflect real live runs.
- [x] **Item 8: Full Pytest Suite**:
  - `python -m pytest backend/tests -v --junitxml=pytest-report.xml` passes all 31 tests.

## Status
All 8 items are completed and verified against production standards.

All items (A through G) completed, verified, and passing tests.
