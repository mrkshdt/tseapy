# Technology Stack

**Project:** tseapy — Data Wizard / Upload Milestone
**Researched:** 2026-02-08
**Scope:** Additions/changes to existing Flask time series app for CSV upload, data wizard, and improved dashboard

---

## Existing Stack (Do Not Replace)

The following is the locked baseline. This milestone adds to it — it does not change the framework choice.

| Technology | Current Version | Status |
|------------|-----------------|--------|
| Python | 3.6+ (3.13 tested) | Keep — no changes needed |
| Flask | 2.0.3 | Upgrade to 3.0.x (security, maintenance mode) |
| Jinja2 | 3.0.3 | Keep (upgraded transitively with Flask 3.0) |
| Werkzeug | 2.1.2 | Upgrade transitively with Flask 3.0 |
| pandas | 1.4.2 | Upgrade to 2.2.x (performance, datetime handling improvements) |
| numpy | 1.21.6 | Upgrade to 1.26.x (Python 3.13 support, CVE fixes) |
| plotly | 5.6.0 | Keep — works fine, not blocking |
| stumpy | 1.11.1 | Keep — no need to change for this milestone |
| ruptures | 1.1.6 | Keep — no need to change for this milestone |
| scikit-learn | 1.1.1 | Upgrade to 1.4.x (Python 3.13 compatibility) |
| Flask-Caching | 1.10.1 | Keep — SimpleCache is fine for single-user local |
| Bootstrap | 5.1.3 (CDN) | Upgrade to 5.3.x (CDN) |

---

## Recommended Stack: New Additions

### Core File Upload

**No new library required.** Werkzeug (already a Flask dependency) provides `FileStorage` for handling multipart file uploads. Flask exposes this via `request.files`. This is the standard, well-documented Flask approach for file uploads.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Werkzeug FileStorage | (bundled with Flask) | Receive uploaded CSV from browser | Already a dependency; `request.files['file']` gives a stream; `werkzeug.utils.secure_filename` sanitizes filenames |

**Rationale:** Adding a separate upload library (e.g., Flask-Uploads, Flask-WTF) would be over-engineering. Werkzeug's `FileStorage` is the primitive that all Flask upload libraries wrap. For a single-file CSV upload, use it directly.

### CSV Parsing

**No new library required.** pandas `read_csv()` (already in the stack) handles the full pipeline: delimiter detection, encoding detection, type inference, datetime parsing. It already handles the edge cases listed in the requirements (missing values, wrong delimiters, non-numeric columns).

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pandas read_csv | (bundled) | Parse uploaded CSV into DataFrame | Already in stack; `pd.read_csv(file_stream, sep=None, engine='python')` auto-detects delimiter; handles malformed CSVs gracefully with error reporting |

**Key pandas read_csv flags to use:**
- `sep=None, engine='python'` — auto-detects delimiter (comma, semicolon, tab)
- `parse_dates=True` — attempt datetime parsing on candidate columns
- `on_bad_lines='skip'` (pandas 2.x) or `error_bad_lines=False` (pandas 1.x) — graceful handling of malformed rows

### Multi-Step Data Wizard UI

**No new JavaScript framework required.** Bootstrap 5 (already on CDN in layout.html) supports tab components and step-based UI patterns natively. A 3-step wizard (upload → select columns → confirm) can be built with Bootstrap `nav-tabs` or `stepper`-style cards with vanilla JS to control step progression.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Bootstrap 5.3.x | CDN | Wizard steps, form controls, table preview | Already in stack; upgrade from 5.1.3 to 5.3.x for bug fixes and improved form feedback classes |
| Vanilla JS + Fetch API | (browser native) | Step navigation, AJAX validation | Already the pattern used throughout the app (algo.html uses fetch); no need to add Alpine.js or React |

**Rationale:** The existing codebase uses Bootstrap + vanilla JS consistently. Adding Alpine.js, htmx, or any reactive framework would break this pattern and require rewriting other templates. Keep the existing approach.

### CSV Preview Table

**No new library required.** The wizard step 2 (column selection) needs to show the first N rows of the uploaded CSV. This is a simple HTML table rendered server-side via Jinja2 from the parsed DataFrame.

```python
# Server side: render first 5 rows as HTML
preview_html = df.head(5).to_html(classes='table table-sm table-bordered', index=False)
```

The DataFrame's `to_html()` method generates Bootstrap-compatible table markup directly. No client-side table library needed.

### File Validation

**No new library required.** Validation happens at two layers:

1. **Server-side (Python):** pandas will raise `pandas.errors.ParserError` or `pandas.errors.EmptyDataError` on unreadable files — catch these and return user-friendly error messages.
2. **Client-side (HTML5):** `<input type="file" accept=".csv">` restricts browser file picker to CSV files.

For file size limits, use Werkzeug's `MAX_CONTENT_LENGTH` Flask config (already supported).

---

## Dependency Upgrades Required

These upgrades are blocking for the milestone because the current versions have Python 3.13 compatibility issues or missing features needed for improved CSV handling.

| Package | Current | Target | Reason | Confidence |
|---------|---------|--------|--------|------------|
| Flask | 2.0.3 | 3.0.x | In maintenance mode; Flask 3.0 adds Python 3.13 support, patches security issues. Backward compatible except for removed deprecated APIs. | MEDIUM — verify exact version on PyPI |
| Werkzeug | 2.1.2 | 3.0.x | Upgraded as Flask 3.0 dependency | MEDIUM — transitive with Flask |
| Jinja2 | 3.0.3 | 3.1.x | Upgraded as Flask 3.0 dependency | MEDIUM — transitive with Flask |
| pandas | 1.4.2 | 2.2.x | `on_bad_lines` parameter (replaces `error_bad_lines`), better datetime handling, Copy-on-Write improvements, Python 3.13 support | MEDIUM — verify exact stable version |
| numpy | 1.21.6 | 1.26.x | Python 3.13 support (1.21 drops at Python 3.11), known CVEs patched in 1.24+. Prefer 1.26.x over 2.x for stability with stumpy/ruptures | MEDIUM — verify compatibility with stumpy |
| scikit-learn | 1.1.1 | 1.4.x | Python 3.13 compatibility; 1.1.1 has deprecated APIs removed in 1.4+ | MEDIUM — verify exact version |
| Bootstrap | 5.1.3 | 5.3.x | Bug fixes, improved form validation feedback, offcanvas improvements | HIGH — CDN swap is trivial |

**Note on numpy 2.x:** Avoid numpy 2.x for this milestone. stumpy 1.11.1 may not support numpy 2.x's API changes (NaN handling, copy semantics changed). Upgrade stumpy first if numpy 2.x is desired. For this milestone, numpy 1.26.4 is the safe choice.

---

## What NOT to Use

| Rejected Option | Why Rejected |
|-----------------|--------------|
| Flask-Uploads | Unmaintained (last release 2019). Adds no value over raw Werkzeug. |
| Flask-WTF / WTForms | Adds form validation framework overhead. The existing pattern uses manual HTML forms + query params. Adding WTForms would require rewriting parameter rendering across all algorithms. |
| htmx | Would require partial template refactoring. Not wrong, but introduces a new pattern when vanilla fetch() already works. |
| Alpine.js | Same rationale as htmx — consistent with existing approach. |
| React/Vue | Explicitly out of scope per PROJECT.md. Server-rendered HTML is the pattern. |
| Flask-SQLAlchemy / database | No persistence needed for v1. In-memory SimpleCache is fine. |
| Celery | No async processing needed. Analysis runs synchronously in Flask thread for single-user local use. |
| numpy 2.x | stumpy 1.11.1 API compatibility uncertain with numpy 2.x breaking changes. Use 1.26.x. |

---

## Installation

### Upgrade existing dependencies

```bash
pip install "Flask>=3.0,<4.0" "Werkzeug>=3.0,<4.0" "Jinja2>=3.1,<4.0"
pip install "pandas>=2.2,<3.0"
pip install "numpy>=1.26,<2.0"
pip install "scikit-learn>=1.4,<2.0"
```

### No new packages needed

The data wizard is implemented entirely with existing stack components:
- File upload: `request.files` (Werkzeug, Flask built-in)
- CSV parsing: `pandas.read_csv()` (already installed)
- Wizard UI: Bootstrap 5.3.x tabs + vanilla JS (already on CDN)
- Preview table: `DataFrame.to_html()` (pandas, already installed)
- Column selection: `<select>` HTML elements populated from `df.columns.tolist()`

### Bootstrap CDN Update

In `templates/layouts/layout.html`, update line 9-10:

```html
<!-- Old -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>

<!-- New -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
```

---

## Architecture Integration Point

The data wizard integrates at the single `TODO` comment in `app.py` line 94:

```python
# app.py — current
@app.route('/')
def index():
    # TODO create a menu + route for setting up data!
    data = get_air_quality_uci()[:1000]
    cache.set("data", data)
```

The wizard adds a `/upload` route and a `/setup` multi-step flow. After column selection is confirmed, it calls `cache.set("data", df)` and `session['feature_to_display'] = value_column` — the same two lines already used in the index route. No changes to any other routes, tasks, or backends are needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| File upload approach (Werkzeug) | HIGH | Core Flask feature, extensively documented, used by every Flask tutorial |
| pandas CSV parsing | HIGH | pandas.read_csv is very stable, well-known behavior |
| Bootstrap wizard UI (no new library) | HIGH | Bootstrap 5 tabs are a standard pattern |
| pandas DataFrame.to_html() for preview | HIGH | Core pandas method, works with Bootstrap classes |
| Version targets (Flask 3.0, pandas 2.2, numpy 1.26, sklearn 1.4) | MEDIUM | Training data to Jan 2025; verify exact versions on PyPI before pinning |
| numpy 1.26.x compatibility with stumpy 1.11.1 | MEDIUM | Likely fine but needs pip install test |
| Bootstrap 5.3.3 on CDN | MEDIUM | Version number needs verification against Bootstrap release page |

---

## Sources

- Werkzeug file upload documentation (https://werkzeug.palletsprojects.com/en/latest/datastructures/#werkzeug.datastructures.FileStorage) — HIGH confidence
- Flask file upload pattern (https://flask.palletsprojects.com/en/latest/patterns/fileuploads/) — HIGH confidence
- pandas read_csv documentation — HIGH confidence, core API stable since pandas 1.0
- Bootstrap 5 tabs documentation (https://getbootstrap.com/docs/5.3/components/navs-tabs/) — HIGH confidence
- Existing codebase analysis (`app.py`, `templates/layouts/layout.html`) — direct inspection
