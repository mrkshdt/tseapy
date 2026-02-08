# Requirements: tseapy

**Defined:** 2026-02-08
**Core Value:** Users can upload their own CSV data and immediately analyze any time series column using the built-in algorithms — no coding required.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Upload

- [ ] **UPLD-01**: User can upload a CSV file via a file picker form
- [ ] **UPLD-02**: App auto-detects CSV delimiter (comma, semicolon, tab)
- [ ] **UPLD-03**: App rejects non-CSV files with a clear error message
- [ ] **UPLD-04**: App enforces a file size limit and shows a friendly message when exceeded
- [ ] **UPLD-05**: User can load a demo dataset instead of uploading a file

### Data Preview

- [ ] **PREV-01**: User sees a preview table of the first 10 rows after upload
- [ ] **PREV-02**: User sees column type indicators (numeric, text, date) next to each column
- [ ] **PREV-03**: User sees a summary: row count and date range of the loaded data

### Column Selection

- [ ] **COLS-01**: User can select which column is the time/date index from a dropdown
- [ ] **COLS-02**: User can select which column contains values to analyze (filtered to numeric only)
- [ ] **COLS-03**: User sees a confirmation summary of their selections before proceeding

### Error Handling

- [ ] **ERRH-01**: App shows clear error messages for parse failures (encoding issues, malformed rows)
- [ ] **ERRH-02**: App handles missing values by dropping NaN rows and informing the user how many were removed
- [ ] **ERRH-03**: App validates the selected time column parses as datetime

### Pipeline Integration

- [ ] **PIPE-01**: After column selection, data is cached and the existing analysis pipeline works unchanged
- [ ] **PIPE-02**: The index page redirects to the upload wizard when no data is loaded
- [ ] **PIPE-03**: User can navigate from data upload through to analysis results end-to-end

### Infrastructure

- [ ] **INFR-01**: Dependencies upgraded (Flask 3.x, pandas 2.x, numpy 1.26.x, scikit-learn 1.4.x)
- [ ] **INFR-02**: Bootstrap CDN updated to 5.3.x
- [ ] **INFR-03**: Existing tests pass after dependency upgrade

### UI Consistency

- [ ] **UICN-01**: Upload and wizard pages use the same layout/styling as existing pages
- [ ] **UICN-02**: Navigation between wizard steps and analysis pages is intuitive

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Data Handling

- **EDAT-01**: User can upload Excel (.xlsx) files in addition to CSV
- **EDAT-02**: User can select multiple value columns for comparative analysis
- **EDAT-03**: User can override date format when auto-detection fails
- **EDAT-04**: App supports drag-and-drop file upload

### Analysis Enhancements

- **AENH-01**: User can run all algorithms on selected column and see dashboard overview
- **AENH-02**: User can export analysis results to CSV or PDF
- **AENH-03**: User can save analysis sessions for later review

### Multi-User

- **MULT-01**: User authentication with login/password
- **MULT-02**: Per-user data isolation in cache
- **MULT-03**: Persistent storage of uploaded datasets in database

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| React/Vue frontend | Flask + HTML is faster to build and consistent with existing code |
| Database persistence | In-memory cache sufficient for single-user local tool |
| Real-time streaming upload | Over-engineering for small CSV files |
| Auto-select "best" column | Fragile heuristics frustrate users; explicit selection is better |
| Data editing in browser | Users have their own tools for data cleaning |
| Cloud storage integration | Local-only tool for v1 |
| Mobile responsiveness | Desktop-first tool |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| UPLD-01 | TBD | Pending |
| UPLD-02 | TBD | Pending |
| UPLD-03 | TBD | Pending |
| UPLD-04 | TBD | Pending |
| UPLD-05 | TBD | Pending |
| PREV-01 | TBD | Pending |
| PREV-02 | TBD | Pending |
| PREV-03 | TBD | Pending |
| COLS-01 | TBD | Pending |
| COLS-02 | TBD | Pending |
| COLS-03 | TBD | Pending |
| ERRH-01 | TBD | Pending |
| ERRH-02 | TBD | Pending |
| ERRH-03 | TBD | Pending |
| PIPE-01 | TBD | Pending |
| PIPE-02 | TBD | Pending |
| PIPE-03 | TBD | Pending |
| INFR-01 | TBD | Pending |
| INFR-02 | TBD | Pending |
| INFR-03 | TBD | Pending |
| UICN-01 | TBD | Pending |
| UICN-02 | TBD | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 0
- Unmapped: 22

---
*Requirements defined: 2026-02-08*
*Last updated: 2026-02-08 after initial definition*
