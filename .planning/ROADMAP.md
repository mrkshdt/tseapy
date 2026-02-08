# Roadmap: tseapy

## Overview

This roadmap delivers the Upload Milestone: a multi-step data wizard that lets users upload their own CSV files and immediately run the existing time series analysis algorithms. The project starts by upgrading the dependency stack to a stable baseline, then builds the wizard front-to-back (upload form, CSV parsing, data preview, column selection), adds error handling and robustness, wires the wizard into the existing analysis pipeline, and finishes with UI consistency polish.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Infrastructure Upgrade** - Upgrade all dependencies to current stable versions and verify the existing test suite passes
- [x] **Phase 2: Upload Form and File Validation** - Add the CSV file upload route with security hardening (file type whitelist, size limit, path sanitization)
- [x] **Phase 3: CSV Parsing Utility** - Build the delimiter-sniffing CSV parser with encoding detection and demo dataset support
- [x] **Phase 4: Data Preview UI** - Render first-10-rows preview table with column type indicators and dataset summary stats
- [x] **Phase 5: Column Selection UI** - Let user choose the time index and value columns with confirmation before proceeding
- [x] **Phase 6: Error Handling and Validation** - Add specific error messages for parse failures, missing values, and invalid datetime columns
- [x] **Phase 7: Pipeline Integration** - Wire wizard output into the existing analysis pipeline via the two-phase cache handoff
- [x] **Phase 8: UI Consistency** - Ensure all wizard pages match existing app styling and navigation feels intuitive end-to-end

## Phase Details

### Phase 1: Infrastructure Upgrade
**Goal**: The app runs on current stable dependencies with all existing functionality intact
**Depends on**: Nothing (first phase)
**Requirements**: INFR-01, INFR-02, INFR-03
**Success Criteria** (what must be TRUE):
  1. App starts and all four existing analysis tasks work after running `pip install -r requirements.txt`
  2. Bootstrap 5.3.x CDN link is active and all existing UI components render correctly
  3. Existing test suite passes with zero failures on the upgraded stack
  4. `requirements.txt` pins Flask 3.x, pandas 2.x, numpy 2.x, and scikit-learn 1.7.x (Python 3.13 compatible)
**Plans**: TBD

Plans:
- [x] 01-01: Audit current dependency versions and research exact stable pins (Flask, pandas, numpy, scikit-learn, stumpy compatibility)
- [x] 01-02: Update requirements.txt with pinned versions and update Bootstrap CDN link in base template
- [x] 01-03: Run existing tests against upgraded stack and fix any regressions

### Phase 2: Upload Form and File Validation
**Goal**: User can submit a CSV file through a form and the app safely stores it, rejecting invalid files before any parsing occurs
**Depends on**: Phase 1
**Requirements**: UPLD-01, UPLD-03, UPLD-04
**Success Criteria** (what must be TRUE):
  1. User sees a file picker that accepts only .csv files
  2. Uploading a non-CSV file returns a clear error message without crashing
  3. Uploading a file over the size limit returns a friendly "file too large" message
  4. A valid CSV upload is accepted and the app advances without security errors
**Plans**: TBD

Plans:
- [x] 02-01: Create upload route (POST /upload) with Werkzeug secure_filename, extension whitelist, and MAX_CONTENT_LENGTH enforcement
- [x] 02-02: Create upload.html template with file picker form, error display area, and Bootstrap styling
- [x] 02-03: Add 413 RequestEntityTooLarge handler and non-CSV rejection response

### Phase 3: CSV Parsing Utility
**Goal**: Uploaded CSV files are reliably parsed regardless of delimiter or encoding, and the original demo dataset remains accessible
**Depends on**: Phase 2
**Requirements**: UPLD-02, UPLD-05
**Success Criteria** (what must be TRUE):
  1. A CSV with comma, semicolon, or tab delimiters is parsed correctly without user intervention
  2. User can click "Use demo dataset" and proceed without uploading a file
  3. Parsed DataFrame is stored in cache and available for preview
**Plans**: TBD

Plans:
- [x] 03-01: Build tseapy/data/upload.py — thin pandas read_csv wrapper with sep=None/engine='python', encoding detection via charset-normalizer, and on_bad_lines='skip'
- [x] 03-02: Add demo dataset route/button that loads existing Air Quality UCI data into cache['raw_data']
- [x] 03-03: Wire upload route to call CSV parser and store result in cache['raw_data'], then redirect to preview

### Phase 4: Data Preview UI
**Goal**: After upload, user can see their data and understand its shape before selecting columns
**Depends on**: Phase 3
**Requirements**: PREV-01, PREV-02, PREV-03
**Success Criteria** (what must be TRUE):
  1. User sees a table showing the first 10 rows of their uploaded data
  2. Each column shows a type indicator (numeric, text, or date)
  3. User sees a summary line showing total row count and detected date range
**Plans**: TBD

Plans:
- [x] 04-01: Create GET /upload/preview route that reads cache['raw_data'] and renders preview
- [x] 04-02: Build upload_preview.html template with DataFrame.to_html() table and Bootstrap table classes
- [x] 04-03: Add column type inference logic (numeric/date/text) and render type badges next to column headers
- [x] 04-04: Add summary bar showing row count and date range below the preview table

### Phase 5: Column Selection UI
**Goal**: User can explicitly choose which column is the time index and which column contains the values to analyze
**Depends on**: Phase 4
**Requirements**: COLS-01, COLS-02, COLS-03
**Success Criteria** (what must be TRUE):
  1. User sees a dropdown populated with all column names for the time/date index selection
  2. User sees a separate dropdown showing only numeric columns for value selection
  3. User sees a confirmation summary of their selections (column names + detected types) before clicking Proceed
**Plans**: TBD

Plans:
- [x] 05-01: Add time index column dropdown to preview/configure template, populated from DataFrame columns
- [x] 05-02: Add value column dropdown filtered to numeric columns only
- [x] 05-03: Add confirmation summary section that displays selections and requires explicit confirmation

### Phase 6: Error Handling and Validation
**Goal**: Common CSV problems surface as actionable error messages rather than crashes or silent bad data
**Depends on**: Phase 5
**Requirements**: ERRH-01, ERRH-02, ERRH-03
**Success Criteria** (what must be TRUE):
  1. Uploading a malformed CSV (bad encoding, unparseable rows) shows a specific error message explaining the problem
  2. A CSV with missing values is accepted and user sees a notice "X rows removed due to missing values"
  3. Selecting a non-datetime column as the time index shows a validation error before the data reaches the pipeline
**Plans**: TBD

Plans:
- [x] 06-01: Add specific exception handlers for pandas ParserError, UnicodeDecodeError, and MemoryError with user-friendly messages
- [x] 06-02: Implement NaN row dropping in the configure step and surface the removed-row count to the user
- [x] 06-03: Add datetime parse validation for the selected time index column with clear error on failure

### Phase 7: Pipeline Integration
**Goal**: After column selection, the existing analysis pipeline works with user-uploaded data exactly as it did with the hardcoded demo
**Depends on**: Phase 6
**Requirements**: PIPE-01, PIPE-02, PIPE-03
**Success Criteria** (what must be TRUE):
  1. After confirming column selections, all four existing analysis tasks (change-in-mean, pattern-recognition, motif-detection, smoothing) run on the uploaded data
  2. Visiting the app with no data loaded redirects to the upload wizard instead of crashing or showing the old demo
  3. User can navigate from upload through column selection through any analysis task to results in a single session
**Plans**: TBD

Plans:
- [x] 07-01: Create POST /upload/configure route that re-indexes DataFrame with datetime index and writes to cache['data'] and session['feature_to_display']
- [x] 07-02: Modify GET / index route to check cache.get('data') and redirect to /upload when no data is present
- [x] 07-03: Test full end-to-end flow: upload CSV -> preview -> configure -> run each analysis task -> view results

### Phase 8: UI Consistency
**Goal**: The wizard pages feel like part of the same app as the existing analysis pages — no jarring style shifts
**Depends on**: Phase 7
**Requirements**: UICN-01, UICN-02
**Success Criteria** (what must be TRUE):
  1. Upload and wizard pages use the same base template, navigation bar, and Bootstrap classes as existing analysis pages
  2. User can move between wizard steps and back to analysis pages without confusion about where they are in the flow
**Plans**: TBD

Plans:
- [x] 08-01: Audit upload/preview/configure templates against existing templates for layout, nav, and CSS class consistency
- [x] 08-02: Add breadcrumb or step indicator showing wizard progress (Upload -> Preview -> Configure -> Analysis)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure Upgrade | 3/3 | Complete | 2026-02-08 |
| 2. Upload Form and File Validation | 3/3 | Complete | 2026-02-08 |
| 3. CSV Parsing Utility | 3/3 | Complete | 2026-02-08 |
| 4. Data Preview UI | 4/4 | Complete | 2026-02-08 |
| 5. Column Selection UI | 3/3 | Complete | 2026-02-08 |
| 6. Error Handling and Validation | 3/3 | Complete | 2026-02-08 |
| 7. Pipeline Integration | 3/3 | Complete | 2026-02-08 |
| 8. UI Consistency | 2/2 | Complete | 2026-02-08 |
