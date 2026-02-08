# Project Research Summary

**Project:** tseapy — Data Wizard / Upload Milestone
**Domain:** Flask time series analysis web platform — CSV data ingestion wizard
**Researched:** 2026-02-08
**Confidence:** MEDIUM

## Executive Summary

tseapy is an existing Flask-based time series analysis tool that currently hardcodes a single UCI Air Quality dataset. The core problem is that the app is analytically capable but practically useless to anyone without their own data. The Upload Milestone adds a multi-step data wizard (upload CSV, preview data, select columns) that replaces the hardcoded data loading with user-driven data ingestion. Experts build this type of feature as an entirely additive front-door to an existing pipeline: the wizard writes to the same cache keys the rest of the app already consumes, requiring zero changes to any analysis route.

The recommended approach is to build the wizard using only what is already in the stack — Werkzeug file handling, pandas CSV parsing, Bootstrap tabs, vanilla JS Fetch, and Jinja2 server-rendered templates. No new libraries are needed. Six existing dependencies need version upgrades (Flask 2 to 3, pandas 1.4 to 2.2, numpy 1.21 to 1.26, scikit-learn 1.1 to 1.4, Werkzeug 2 to 3, Bootstrap 5.1 to 5.3) primarily for Python 3.13 compatibility and access to improved CSV handling APIs. These upgrades must happen before new feature code is written.

The key risks are security and correctness: unrestricted file uploads enable path traversal, unbounded file sizes exhaust memory, and pandas silently misreads non-standard CSV encodings/delimiters in ways that produce wrong analysis results without any error. All three are preventable with standard hardening patterns applied during the upload route and CSV parsing steps. The wizard's architecture is clean — a two-phase cache pattern (raw_data staging key then final data key) keeps unvalidated data out of the analysis pipeline until the user confirms column selections.

## Key Findings

### Recommended Stack

The entire wizard is built from already-installed dependencies. Werkzeug's `FileStorage` handles the multipart upload via `request.files`. pandas `read_csv(sep=None, engine='python')` handles delimiter auto-detection, encoding, and type inference. Bootstrap 5 `nav-tabs` with vanilla JS drives the multi-step UI, consistent with the existing codebase pattern. `DataFrame.to_html(classes='table table-sm table-bordered')` renders the data preview table. The only changes are version upgrades to existing packages.

**Core technologies:**
- **Werkzeug FileStorage:** Receive and sanitize uploaded CSV — already a Flask dependency, zero new installs
- **pandas read_csv:** Parse CSV with auto-delimiter detection — already installed, use `sep=None, engine='python'` and `on_bad_lines='skip'` (pandas 2.x API)
- **Bootstrap 5.3.x (CDN):** Wizard step UI and preview table styling — CDN swap from 5.1.3
- **Vanilla JS + Fetch API:** Step navigation and AJAX validation — matches existing codebase pattern throughout
- **Flask-Caching (SimpleCache):** Stage raw DataFrame and store final configured DataFrame — already in use

**Version upgrades required before new code:**
- Flask 2.0.3 -> 3.0.x (maintenance mode, Python 3.13 support)
- pandas 1.4.2 -> 2.2.x (on_bad_lines API, datetime improvements, Python 3.13)
- numpy 1.21.6 -> 1.26.x (Python 3.13, CVE fixes; avoid 2.x for stumpy compatibility)
- scikit-learn 1.1.1 -> 1.4.x (Python 3.13 compatibility)

### Expected Features

**Must have (table stakes):**
- File picker upload form (accept=".csv") — minimum expected upload UI
- CSV parsing with auto-delimiter detection (comma, semicolon, tab) — real-world files vary
- Data preview table (first 10 rows) — users must confirm data loaded correctly before proceeding
- Column type inference display (numeric vs date vs text per column) — enables informed column selection
- Time/date index column selection dropdown — app requires datetime index
- Value column selection dropdown (numeric columns only) — app requires numeric target
- Basic error feedback for parse failures and missing column types — prevents silent failures
- Confirmation step before analysis begins — prevents accidental mis-selection
- Graceful handling of missing values (NaN rows) with row-drop count shown to user
- Non-CSV file rejection with clear error message

**Should have (differentiators):**
- Sample data / demo dataset option ("Use Air Quality UCI data") — reduces drop-off, already loaded in codebase
- Row count and date range summary after successful load ("1,247 rows, 2020-01-01 to 2023-06-30")
- File size limit with friendly message (10 MB cap)
- Multiple delimiter support with user override radio buttons (for the 10% auto-detect fails)

**Defer (v2+):**
- Column preview sparklines (Plotly per-column mini-charts in wizard)
- Date format hint/override UI
- Multi-step stepper UI with animated progress (single-page sections sufficient for v1)
- Persist last-used column selections across sessions
- Excel (.xlsx) support (requires openpyxl)
- Multi-file upload / dataset merging

### Architecture Approach

The wizard is an entirely additive front-door to the existing pipeline. Three new routes (`POST /upload`, `GET /upload/preview`, `POST /upload/configure`) plus one CSV parsing utility module (`tseapy/data/upload.py`) compose the full feature. The wizard stores an intermediate "raw_data" DataFrame in cache during preview/selection, then writes the final configured DataFrame to the existing "data" cache key after column confirmation. The single change to existing code is removing the hardcoded `get_air_quality_uci()` call from `GET /` and replacing it with a redirect to `/upload` when no data is present.

**Major components:**
1. **Upload Route** (`POST /upload`) — receives FileStorage, validates extension/size, parses CSV to raw DataFrame, stores in `cache['raw_data']`, redirects to preview
2. **Preview Route** (`GET /upload/preview`) — reads `cache['raw_data']`, renders HTML table of first 10 rows plus column selector dropdowns
3. **Configure Route** (`POST /upload/configure`) — applies user column selections, re-indexes DataFrame as datetime, writes final `cache['data']` and `session['feature_to_display']`, redirects to index
4. **CSV Parser utility** (`tseapy/data/upload.py`) — thin wrapper around `pandas.read_csv` with delimiter sniffing and encoding handling, testable without Flask context
5. **Modified Index Route** (`GET /`) — checks `cache.get('data')` exists; if not, redirects to `/upload` instead of hardcoding data load

### Critical Pitfalls

1. **Unrestricted file upload (path traversal)** — always call `werkzeug.utils.secure_filename()` before any path join; whitelist `.csv` extension only; enforce `MAX_CONTENT_LENGTH = 10MB`; catch `RequestEntityTooLarge` (413). Address in upload route before any other logic.

2. **Unbounded file size (memory exhaustion)** — set `app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024` in app factory; also enforce post-parse row count limit (500k rows max). Address during upload config setup.

3. **pandas silently misreading CSV data** — real-world Excel exports use semicolons, BOM markers, ISO-8859-1 encoding. Use `chardet`/`charset-normalizer` for encoding detection; expose delimiter override to user; validate dtypes after parse and surface warnings. Address in CSV parsing step.

4. **XSS via CSV column names/values in preview table** — use Jinja2 auto-escaped `{{ value }}` (never `| safe`); use `textContent` not `innerHTML` in JS; sanitize column names used as HTML element IDs; add CSP header. Address in data preview UI.

5. **Wizard state not validated at each step** — always check `cache.get('raw_data') is not None` at preview route entry; redirect to step 1 with "session expired, please re-upload" message if missing. Address in wizard state flow design.

## Implications for Roadmap

Based on combined research, the wizard implementation has clear sequential dependencies that define the phase order. Each phase unblocks the next and isolates a distinct failure mode.

### Phase 1: Dependency Upgrades and Project Setup
**Rationale:** PITFALLS.md explicitly calls out dependency incompatibilities as a blocking concern. New pandas 2.x APIs (`on_bad_lines`) are required for correct CSV handling. Running existing tests against upgraded packages before adding new code reduces risk of hidden regressions. STACK.md identifies these as blocking upgrades.
**Delivers:** Upgraded Flask 3.0, pandas 2.2, numpy 1.26, scikit-learn 1.4, Bootstrap 5.3. Green test suite on upgraded stack.
**Addresses:** Pitfall 9 (dependency incompatibilities)
**Avoids:** Writing new code against deprecated APIs that will need immediate rewrite

### Phase 2: Upload Route and CSV Parsing Utility
**Rationale:** All wizard functionality depends on reliable file ingestion and parsing. ARCHITECTURE.md establishes the build order: `tseapy/data/upload.py` first (no Flask dependency, immediately testable), then the upload route. Security hardening (secure_filename, MAX_CONTENT_LENGTH, extension whitelist) must be established here before any other upload logic.
**Delivers:** `POST /upload` endpoint, `tseapy/data/upload.py` with delimiter sniffing, `templates/upload.html` form, `cache['raw_data']` populated with parsed DataFrame
**Implements:** Upload Route and CSV Parser utility components
**Avoids:** Pitfalls 1 (path traversal), 2 (memory exhaustion), 5 (silent CSV misread), 6 (bare exception handlers)

### Phase 3: Data Preview and Column Selection UI
**Rationale:** Preview is the user's only opportunity to catch parsing errors before they corrupt analysis. Column selection depends on seeing the data. FEATURES.md dependency graph shows this chain: preview -> column type inference -> column selection.
**Delivers:** `GET /upload/preview` route, `templates/upload_preview.html` with HTML table + dropdown selectors, column dtype display
**Uses:** `DataFrame.to_html()` with Bootstrap classes, Jinja2 auto-escaping
**Implements:** Preview Route component
**Avoids:** Pitfall 4 (XSS in preview), Pitfall 7 (unvalidated column parameters), Pitfall 8 (missing wizard state guards)

### Phase 4: Column Configuration and Pipeline Integration
**Rationale:** This is the integration point where the wizard hands off to the existing analysis pipeline. The two-phase cache pattern (raw_data -> data) is the core architectural decision. Only after this route works does the existing app become usable with user data.
**Delivers:** `POST /upload/configure` route, datetime index parsing, `cache['data']` written in format existing pipeline expects, `session['feature_to_display']` set, modified `GET /` index route with data presence check
**Implements:** Configure Route, integration with existing `get_data_or_abort()` pipeline
**Avoids:** Pitfall 3 (global cache key collision), Pitfall 11 (DataFrame in session cookie)

### Phase 5: Error Handling, Validation, and Quick Wins
**Rationale:** Structured error handling cuts across all phases but is cleanest to formalize after the happy path works. Quick wins (sample data button, row count summary, file size UI) add user-facing polish without new architectural decisions.
**Delivers:** Specific exception handlers for `ParserError`, `UnicodeDecodeError`, `MemoryError`, user-friendly error messages, sample data option, row count/date range summary display
**Addresses:** Table stakes (error feedback, graceful NaN handling, non-CSV rejection); differentiators (sample data, row summary)
**Avoids:** Pitfall 6 (bare exception handlers), Pitfall 12 (MIME type not verified)

### Phase Ordering Rationale

- Dependency upgrades first because new pandas 2.x API is required and incompatibilities between old numpy/Flask and new pandas will cause confusing failures during development.
- Upload + parsing before preview because preview reads from cache that upload populates — preview has nothing to show without it.
- Preview before configure because configure reads column selections that preview rendered — configure has no valid inputs without it.
- Configure last (before polish) because it mutates the "data" cache key that existing analysis routes read — modifying the existing index route should come after the full wizard is functional to minimize time with broken app state.
- Error handling and quick wins last because they layer onto working routes without restructuring them.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Dependency Upgrades):** Verify exact PyPI versions for Flask 3.0.x, pandas 2.2.x, numpy 1.26.x, scikit-learn 1.4.x before pinning. Check stumpy 1.11.1 compatibility with numpy 1.26 specifically.
- **Phase 2 (Upload/Parsing):** Validate `charset-normalizer` vs `chardet` recommendation for encoding detection (both are well-known, either works; pick one and pin it).

Phases with standard patterns (skip research-phase):
- **Phase 3 (Preview UI):** Jinja2 `DataFrame.to_html()` + Bootstrap table is a completely documented pattern.
- **Phase 4 (Pipeline Integration):** Cache key handoff is direct code surgery, no external research needed.
- **Phase 5 (Error Handling):** Flask exception handler pattern is well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Core approach (Werkzeug + pandas + Bootstrap) is HIGH confidence. Version target numbers (3.0.x, 2.2.x, 1.26.x) need PyPI verification before pinning. |
| Features | HIGH | Table stakes derived from direct codebase reading and PROJECT.md requirements. Anti-features explicitly called out in PROJECT.md scope. Feature dependency chain verified against actual code (validation.py, examples.py, app.py). |
| Architecture | HIGH | Based on direct codebase analysis. Two-phase cache pattern derived from existing `get_data_or_abort()` contract. Build order has clear sequential dependencies. |
| Pitfalls | MEDIUM | Flask file upload, pandas CSV, and XSS patterns are stable, well-documented knowledge. Specific version-interaction pitfalls (numpy/stumpy compatibility) are inferred, need pip install verification. |

**Overall confidence:** MEDIUM — strong architectural clarity, version numbers need PyPI verification before pinning in requirements.txt.

### Gaps to Address

- **Exact version pins:** Flask 3.0.x, pandas 2.2.x, numpy 1.26.x, scikit-learn 1.4.x, Bootstrap 5.3.x — look up current stable releases on PyPI and Bootstrap CDN before writing requirements.txt.
- **stumpy 1.11.1 + numpy 1.26 compatibility:** Likely fine but must run `pip install` test to confirm before committing to numpy 1.26 target.
- **chardet vs charset-normalizer:** Both detect encoding. charset-normalizer is the requests library default and has no C extension dependency. Either works; decide once and document the choice.
- **Existing test coverage:** PITFALLS.md recommends running existing tests against upgraded stack before new code. The extent of existing test coverage is unknown and may limit confidence that the upgrade is safe.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `app.py`, `tseapy/core/tasks.py`, `tseapy/core/analysis_backends.py`, `tseapy/data/examples.py`, `tseapy/core/validation.py` — direct code reading
- `.planning/PROJECT.md` — active requirements and out-of-scope decisions
- `.planning/codebase/CONCERNS.md` — tech debt and missing features audit

### Secondary (MEDIUM confidence)
- Flask file upload pattern documentation (https://flask.palletsprojects.com/en/latest/patterns/fileuploads/)
- Werkzeug secure_filename documentation (https://werkzeug.palletsprojects.com/en/latest/utils/)
- pandas read_csv documentation — core API stable since 1.0
- Bootstrap 5 tabs/components documentation (https://getbootstrap.com/docs/5.3/)
- OWASP File Upload Cheat Sheet (https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- OWASP XSS Prevention Cheat Sheet

### Tertiary (LOW confidence — verify before use)
- Exact PyPI version numbers (Flask 3.0.x, pandas 2.2.x, etc.) — training knowledge cutoff Jan 2025, verify on PyPI
- Bootstrap 5.3.3 CDN availability — verify at cdn.jsdelivr.net
- stumpy 1.11.1 numpy 1.26.x compatibility — inference, needs pip test

---
*Research completed: 2026-02-08*
*Ready for roadmap: yes*
