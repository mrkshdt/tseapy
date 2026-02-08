# Architecture Patterns

**Domain:** Time series analysis web platform — data upload wizard integration
**Researched:** 2026-02-08

## Context

tseapy has a well-established Task-Backend Factory pattern. The existing pipeline expects a pandas DataFrame in Flask-Caching under the key `'data'`. Currently the index route (`/`) hardcodes `get_air_quality_uci()` to populate that cache entry. The upload wizard must replace that single call site. Everything downstream (task routes, algo routes, compute routes) already consumes `cache.get('data')` through the `get_data_or_abort()` helper — so they need no changes if the wizard writes to the same cache key.

## Recommended Architecture

```
Browser
   |
   |  POST /upload (multipart/form-data)
   v
[Upload Route] ── validates file ──> [CSV Parser] ── pandas.read_csv ──> raw DataFrame
   |                                                                              |
   |  stores raw_data in cache                                                   |
   v                                                                             |
[Preview Route GET /upload/preview] <── reads raw_data from cache <─────────────┘
   |
   |  renders preview.html (first N rows, column list, delimiter detection)
   v
Browser (user selects index_col and value_col)
   |
   |  POST /upload/configure (form: index_col, value_col, delimiter)
   v
[Configure Route] ── re-parses / re-indexes DataFrame ──> validated DataFrame
   |  stores final 'data' in cache (same key existing pipeline expects)
   |  sets session['feature_to_display'] = value_col
   v
[Redirect] → / (index page, which now finds 'data' in cache and shows task menu)
```

The wizard is entirely additive. It writes to the same cache keys the existing pipeline reads. No existing route needs modification.

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **Upload Route** (`POST /upload`) | Receive multipart file, validate extension and size, parse CSV to raw DataFrame, store in cache as `'raw_data'` | Flask cache (write), redirect to preview |
| **Preview Route** (`GET /upload/preview`) | Read `'raw_data'` from cache, render first 10 rows as HTML table, populate column selector dropdowns | Flask cache (read), Jinja2 template |
| **Configure Route** (`POST /upload/configure`) | Apply user column selections (index_col, value_col), re-index DataFrame, store as `'data'` in cache, set session `feature_to_display` | Flask cache (read+write), Flask session (write), redirect to `/` |
| **CSV Parser utility** (`tseapy/data/upload.py`) | Thin wrapper around `pandas.read_csv` with delimiter sniffing, encoding handling, numeric-column filtering | pandas |
| **Validation utility** (`tseapy/core/validation.py`) | Validate that selected columns exist, index is parseable as datetime or numeric, value column is numeric | pandas DataFrame |
| **Existing pipeline** (all `/<task>/...` routes) | Unchanged — reads `'data'` from cache via `get_data_or_abort()` | Flask cache (read only) |

## Data Flow

```
1. File arrives as werkzeug FileStorage in request.files['file']

2. Upload Route:
   - Check allowed extension (csv, txt)
   - Read into memory: pd.read_csv(file.stream, ...)
   - Store raw DataFrame → cache.set('raw_data', df)
   - Redirect → GET /upload/preview

3. Preview Route:
   - Read raw_data from cache
   - Detect potential datetime columns (object dtype or explicit datetime)
   - Detect numeric columns
   - Render HTML table (first 10 rows)
   - Render two <select> elements: index_col and value_col

4. Configure Route:
   - Read raw_data from cache
   - Apply: df.set_index(index_col), parse index as datetime
   - Filter: keep only value_col (or keep all numeric, set session to value_col)
   - Store → cache.set('data', configured_df)
   - Set → session['feature_to_display'] = value_col
   - Redirect → /

5. Index Route (existing, unchanged):
   - Removes hardcoded get_air_quality_uci() call
   - Uses get_data_or_abort() — if no data yet, show upload prompt instead of error
   - Renders task menu when data exists
```

## Patterns to Follow

### Pattern 1: Two-Phase Cache (raw_data then data)

**What:** Store the as-uploaded DataFrame under `'raw_data'` for preview; only write to `'data'` after user confirms column selections.

**When:** Any time user needs to inspect and configure data before it enters the analysis pipeline. Prevents partial/wrong data from reaching analysis routes.

**Why:** Keeps the existing `get_data_or_abort()` contract intact. `'data'` only ever contains a properly indexed, column-validated DataFrame.

```python
# upload route
cache.set('raw_data', pd.read_csv(file.stream, ...))
return redirect(url_for('upload_preview'))

# configure route
raw = cache.get('raw_data')
df = raw.set_index(index_col)
df.index = pd.to_datetime(df.index)
cache.set('data', df)
session['feature_to_display'] = value_col
return redirect(url_for('index'))
```

### Pattern 2: Additive Routes Only

**What:** Add `/upload`, `/upload/preview`, `/upload/configure` as new route handlers. Touch zero existing routes except removing the hardcoded data-load from `GET /`.

**When:** Integrating features into an existing working system.

**Why:** Minimizes regression risk. The existing pipeline's contracts (cache key `'data'`, session key `'feature_to_display'`) are already well-defined and tested.

### Pattern 3: Delegate CSV Complexity to a Utility Module

**What:** Create `tseapy/data/upload.py` with a `parse_csv(stream, **kwargs) -> pd.DataFrame` function. Keep route handlers thin.

**When:** File parsing logic involves sniffing delimiters, handling encoding errors, detecting date columns. This logic belongs in the data layer, not the route layer.

**Why:** Matches the existing `tseapy/data/examples.py` pattern (data loading utilities separate from routes). Testable without Flask context.

```python
# tseapy/data/upload.py
def parse_csv(stream, sep=None, encoding='utf-8-sig') -> pd.DataFrame:
    if sep is None:
        # sniff delimiter
        sample = stream.read(4096)
        stream.seek(0)
        sep = csv.Sniffer().sniff(sample.decode(encoding, errors='replace')).delimiter
    return pd.read_csv(stream, sep=sep, encoding=encoding)
```

### Pattern 4: Graceful Index Route for Missing Data

**What:** Modify `GET /` to check if `'data'` is in cache. If not, render a "load data" prompt or redirect to `/upload`. If yes, render the task menu.

**When:** Users arrive at `/` without data loaded (fresh start, cache expired).

**Why:** Currently `get_data_or_abort()` returns HTTP 400 if called with no data. But `/` doesn't call it — it just hardcodes data loading. After removing the hardcoded load, `/` should gracefully handle the no-data state.

```python
@app.route('/')
def index():
    data = cache.get('data')
    if data is None:
        return redirect(url_for('upload'))
    return render_template('index.html',
        tasks=[(t.name, t.short_description) for t in tasks._tasks.values()])
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Storing DataFrame in Flask Session

**What:** Serializing the full DataFrame into the Flask session cookie.

**Why bad:** Session cookies are limited to ~4KB. A DataFrame with even 1000 rows will exceed this and silently fail or raise a `ValueError`. The existing architecture already uses Flask-Caching for this reason.

**Instead:** Always use `cache.set('data', df)` and `cache.get('data')`. Session stores only lightweight scalar state (`feature_to_display` column name).

### Anti-Pattern 2: Re-using `'data'` Cache Key During Preview

**What:** Writing the raw uploaded DataFrame directly to `'data'` before user column selection.

**Why bad:** Any analysis route accessed after upload but before configure would run against an improperly indexed DataFrame, causing pandas errors or silent wrong results.

**Instead:** Use `'raw_data'` staging key until configure is complete.

### Anti-Pattern 3: Parsing CSV Inside the Route Handler

**What:** Putting `pd.read_csv(request.files['file'].stream, sep=',', ...)` inline in the route.

**Why bad:** Delimiter detection, encoding handling, and column type inference belong in the data layer. Route handlers should be thin (receive → validate → delegate → respond). Mixing I/O logic with HTTP logic makes both harder to test.

**Instead:** Call `parse_csv(stream)` from `tseapy/data/upload.py`.

### Anti-Pattern 4: Accepting Any File Type

**What:** Not validating file extension or MIME type before passing to pandas.

**Why bad:** Malformed files cause uninformative pandas exceptions that bubble to HTTP 500. Large files (e.g., multi-GB uploads) will exhaust server memory.

**Instead:** Whitelist extensions (`csv`, `txt`), enforce a max content-length on Flask app config (`MAX_CONTENT_LENGTH`), and wrap `read_csv` in try/except to return user-friendly 400 errors.

## New Component: Jinja2 Templates

Three new templates needed:

| Template | Purpose | Data Passed |
|----------|---------|-------------|
| `templates/upload.html` | File upload form with `<input type="file">` | None (static form) |
| `templates/upload_preview.html` | HTML table of first 10 rows + column selector dropdowns | `columns`, `preview_rows`, `dtypes` |
| (reuse `index.html`) | Task menu after successful configure | `tasks` list |

All templates extend `layouts/layout_without_sidebar.html` (matching the index page pattern, since sidebar requires data context).

## Build Order (Dependencies)

Build in this order because each step unblocks the next:

1. **`tseapy/data/upload.py`** — CSV parsing utility. No Flask dependency. Testable immediately. All later components depend on this.

2. **`POST /upload` route + `templates/upload.html`** — File ingestion endpoint. Depends on `parse_csv`. Stores `'raw_data'`.

3. **`GET /upload/preview` route + `templates/upload_preview.html`** — Preview display. Depends on `'raw_data'` being in cache. No analysis code changes.

4. **`POST /upload/configure` route** — Column selection and indexing. Depends on `'raw_data'` and writes final `'data'`. This is the integration point with the existing pipeline.

5. **Modify `GET /` index route** — Remove hardcoded `get_air_quality_uci()`, add data-present check. Last because it changes existing behavior; all wizard components must work first.

6. **Error handling in upload routes** — 400 responses for bad files, oversized uploads, missing columns. Can be added incrementally alongside each route.

## Integration Point Summary

The single integration point between wizard and existing pipeline is:

```
cache.set('data', configured_df)          # wizard writes
cache.get('data')  via get_data_or_abort() # pipeline reads (unchanged)
```

Everything else in the existing codebase is already correct. The data wizard is a front-door addition.

## Scalability Considerations

This is a local, single-user tool. Scalability is not a concern for v1. However:

| Concern | At current scale (local) | If it ever went multi-user |
|---------|--------------------------|---------------------------|
| Cache key collisions | Not an issue (single user) | Prefix keys with session ID |
| Large CSV memory | Pandas in-memory is fine for typical datasets (<100MB) | Stream/chunk processing |
| Cache expiry | 3600s default is fine | Keep as-is |

## Sources

- Codebase analysis of `app.py`, `tseapy/core/tasks.py`, `tseapy/core/analysis_backends.py`, `tseapy/data/examples.py` — HIGH confidence (direct code reading)
- Existing `.planning/codebase/ARCHITECTURE.md` — HIGH confidence (previously audited)
- Flask documentation patterns for `request.files`, `werkzeug.FileStorage`, `MAX_CONTENT_LENGTH` — MEDIUM confidence (well-established Flask patterns, confirmed against existing app structure)
- pandas `read_csv` sniffing patterns — MEDIUM confidence (standard library usage)
