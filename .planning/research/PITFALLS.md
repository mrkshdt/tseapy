# Domain Pitfalls

**Domain:** Flask CSV upload + data wizard for time series analysis
**Researched:** 2026-02-08
**Confidence note:** All findings based on training knowledge (cutoff Jan 2025). External tools unavailable during this session. Confidence is MEDIUM for well-established Flask/pandas patterns, LOW for anything cutting-edge. Flag sections marked LOW for validation before implementation.

---

## Critical Pitfalls

Mistakes that cause security incidents, data corruption, or mandatory rewrites.

---

### Pitfall 1: Unrestricted File Upload Leading to Path Traversal / Arbitrary Write

**What goes wrong:** `request.files['file'].save(os.path.join(upload_dir, filename))` where `filename` comes directly from the client. An attacker (or accident) sends `filename = "../../app.py"` and overwrites application code. Even in local-only deployments, this can corrupt the app silently.

**Why it happens:** Developers trust `werkzeug`'s `FileStorage.filename` attribute without sanitizing it. The attribute reflects whatever the browser sent.

**Consequences:** Arbitrary file write anywhere the web process has permissions. In a no-database, in-memory-cache app, this is the primary persistence attack surface.

**Prevention:**
- Always pass filenames through `werkzeug.utils.secure_filename()` before any path join.
- Enforce an explicit allowlist of extensions: `.csv` only. Reject everything else with 400.
- Store uploads in a dedicated temp directory (e.g., `tempfile.mkdtemp()`) outside the application tree.
- Never serve uploaded files back via a static route without re-validating content type.

**Detection / Warning signs:**
- Any code that does `os.path.join(upload_dir, request.files[...].filename)` without `secure_filename` in between.
- Upload routes that accept `*` or no extension filter.

**Phase to address:** Upload implementation phase — before any other upload logic is written.

---

### Pitfall 2: Unbounded File Size Allows Memory Exhaustion (DoS)

**What goes wrong:** No `MAX_CONTENT_LENGTH` set on the Flask app. A user uploads a 2 GB CSV. Pandas reads it entirely into RAM. The Python process OOMs or swaps to death. Because there is no database and the app uses in-memory cache, there is no relief valve.

**Why it happens:** Flask's default `MAX_CONTENT_LENGTH` is `None` (unlimited). Developers test with small files and never hit the limit.

**Consequences:** Server crash or extreme latency for all users sharing the process. In local deployment, freezes the user's machine.

**Prevention:**
- Set `app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024` (10 MB, adjust to domain need) in the application factory.
- Catch `RequestEntityTooLarge` (413) and return a user-friendly message.
- For time series use cases, also enforce a row-count limit after initial parse (`df.shape[0] > 500_000` → reject with explanation).

**Detection / Warning signs:**
- `MAX_CONTENT_LENGTH` not present in `app.config` or config files.
- No error handler for 413.

**Phase to address:** Upload implementation phase, config setup step.

---

### Pitfall 3: Global In-Memory Cache Key Collision Across Users

**What goes wrong:** The existing codebase already has a global cache key shared across all users (stated in context). Adding CSV upload without per-session keys means User A's uploaded DataFrame overwrites User B's mid-wizard. Silent data corruption, not an error.

**Why it happens:** Convenience — `cache.set('dataframe', df)` is the obvious first implementation. Works perfectly in single-user local testing.

**Consequences:** Users see each other's data. Analysis runs on wrong dataset. Results are silently incorrect. In a local-only deployment this may only manifest when two browser tabs are open simultaneously, but it will happen.

**Prevention:**
- Generate a UUID per upload session: `session_id = str(uuid.uuid4())`.
- Key all cache entries with session ID: `cache.set(f'df_{session_id}', df)`.
- Store `session_id` in Flask `session` (cookie-based) so it persists across wizard steps.
- Set TTL on cached DataFrames (e.g., 30 minutes) to prevent unbounded memory growth.

**Detection / Warning signs:**
- Any `cache.set('dataframe', ...)` or similarly non-namespaced key.
- No reference to `session` or UUID in upload/wizard route handlers.

**Phase to address:** Cache architecture step — must be decided before wizard state management is built, not retrofitted.

---

### Pitfall 4: XSS via Column Names / CSV Content Rendered Without Escaping

**What goes wrong:** The existing codebase already has XSS risks in parameter rendering (stated in context). CSV files frequently contain user-controlled column names or cell values (e.g., `<script>alert(1)</script>` as a column header). If these are interpolated into HTML via Jinja2 without `|e` or rendered via JavaScript `innerHTML`, XSS fires.

**Why it happens:** Data preview tables are often built by iterating over `df.columns` and `df.values` and concatenating strings, especially in quick prototype code or JavaScript that builds table HTML dynamically.

**Consequences:** Stored XSS if any output is persisted. Reflected XSS on preview page. Even in local deployment, malicious CSV files could execute arbitrary JS if the app is accessed via a browser.

**Prevention:**
- Jinja2: always use `{{ value }}` (auto-escaped) never `{{ value | safe }}` for user-supplied data.
- JavaScript: use `textContent` never `innerHTML` when building table cells from CSV data.
- Sanitize column names before use as HTML `id` or `name` attributes (strip/replace non-alphanumeric).
- Run a CSP header: `Content-Security-Policy: default-src 'self'`.

**Detection / Warning signs:**
- Any `| safe` filter applied to data derived from uploaded files.
- JavaScript code using `.innerHTML =` with data from an API endpoint that returns CSV-derived content.
- Column names used directly as HTML element IDs.

**Phase to address:** Data preview UI phase. Also review existing parameter rendering at the same time as it's the same vulnerability class.

---

### Pitfall 5: Pandas CSV Parsing Silently Misreads Data

**What goes wrong:** `pd.read_csv(file)` with default parameters makes many assumptions: comma delimiter, UTF-8 encoding, first row is header, no quoting complexity. Real-world CSVs from Excel are often semicolon-delimited, ISO-8859-1 encoded, have BOM markers, or use locale-specific decimal separators (`,` instead of `.`). The wizard accepts the file, produces no error, but the time index parses as object dtype instead of datetime, and numeric columns contain strings.

**Why it happens:** Tests use clean synthetic CSVs. Users upload exports from Excel, LibreOffice, or instrument software.

**Consequences:** Silent analysis failures. `pd.to_datetime()` raises later. Numeric operations on string columns return NaN silently. Users blame the analysis, not the parse.

**Prevention:**
- Use `chardet` or `charset-normalizer` to detect encoding before parse.
- Expose delimiter detection (try `,`, `;`, `\t`) and let user confirm in the wizard.
- After parse, validate: confirm dtypes, report columns that failed numeric/datetime coercion.
- Never silently coerce — surface parse warnings to the user in the wizard UI.
- For datetime columns: require explicit format string selection or use `pd.to_datetime(..., infer_datetime_format=False, format=user_selected_format)`.

**Detection / Warning signs:**
- `pd.read_csv` call with no `encoding`, `sep`, or `dtype` arguments.
- No post-parse validation step in the wizard flow.
- Time index column dtype check missing before analysis is dispatched.

**Phase to address:** CSV parsing step of wizard, before column selection UI.

---

### Pitfall 6: Bare Exception Handlers Hide Parse and Processing Errors

**What goes wrong:** The existing codebase already has bare exception handlers (stated in context). Adding CSV upload with `except Exception: pass` or `except: return "Error"` means parse failures, memory errors, and encoding errors all look the same to the user and produce no diagnostic information for the developer.

**Why it happens:** Defensive coding under time pressure. Bare handlers prevent 500 errors in production.

**Consequences:** Silent failures. Users upload malformed CSV, get generic error, cannot diagnose. Developer cannot distinguish OOM from malformed CSV from pandas bug. Impossible to add monitoring later without rewriting all handlers.

**Prevention:**
- Catch specific exceptions: `pd.errors.ParserError`, `UnicodeDecodeError`, `MemoryError`, `ValueError`.
- Log at appropriate levels: `logger.exception(...)` for unexpected errors, `logger.warning(...)` for user input errors.
- Return structured error responses with error codes the frontend can map to user-friendly messages.
- Never catch `Exception` without re-raising or logging the full traceback.

**Detection / Warning signs:**
- `except Exception:` or bare `except:` anywhere in upload/parse routes.
- No logging imports in new route files.
- Frontend that shows only "An error occurred" with no detail.

**Phase to address:** Upload and parse phase. Establish logging pattern before any business logic is written.

---

## Moderate Pitfalls

---

### Pitfall 7: No Input Validation on Column Selection Parameters

**What goes wrong:** The existing codebase has no input validation (stated in context). The wizard sends `time_col=<user_value>` and `value_col=<user_value>` as form/query parameters. Code does `df[request.args.get('time_col')]` without verifying that the column name exists in the DataFrame. Causes KeyError in best case, potential injection in template rendering in worst case.

**Prevention:**
- Validate that submitted column names are in `df.columns` before use.
- Use an allowlist: the valid options ARE the column names from the parsed DataFrame, nothing else.
- Reject requests where column parameters reference columns not present in the session's DataFrame.

**Phase to address:** Column selection wizard step.

---

### Pitfall 8: Wizard State Not Validated at Each Step

**What goes wrong:** Multi-step wizard (upload → preview → column select → analyze) assumes state from previous steps is intact. User bookmarks step 3, returns next day, cache has expired, DataFrame is gone. Code crashes trying to load from empty cache.

**Prevention:**
- At the start of each wizard step, validate that required prior state exists in cache.
- Redirect to step 1 with a clear message ("Session expired, please re-upload") if state is missing.
- Never assume `cache.get(key)` returns a valid DataFrame — always check for `None`.

**Phase to address:** Wizard state management design.

---

### Pitfall 9: Outdated Dependencies Create Incompatibilities During Upload Feature Addition

**What goes wrong:** NumPy 1.21 and Flask 2.0 (stated in existing issues) have known incompatibilities with newer pandas versions. Adding CSV upload with a modern pandas will trigger `AttributeError` or behavioral changes (e.g., `pd.DataFrame.append` removed in pandas 2.0, copy-on-write behavior changed). Mixing old Flask 2.0 with newer Werkzeug also causes request handling issues.

**Prevention:**
- Upgrade NumPy and Flask as part of the milestone setup, before adding any new features.
- Pin all dependencies in `requirements.txt` with exact versions after upgrade.
- Run existing tests against upgraded stack before implementing new features.
- Check pandas changelog for breaking changes between current version and 2.0+.

**Detection / Warning signs:**
- `requirements.txt` shows `numpy==1.21`, `flask==2.0` without upgrade plan.
- New code using `pd.read_csv` alongside old code using deprecated pandas APIs.

**Phase to address:** Dependency upgrade — first task of the milestone, before any new code.

---

### Pitfall 10: Temporary Files Not Cleaned Up

**What goes wrong:** Each upload saves a file to a temp directory. No cleanup mechanism. Disk fills up over time, especially during development with repeated test uploads.

**Prevention:**
- Use `tempfile.NamedTemporaryFile(delete=True)` and parse within context, OR
- Explicitly delete the temp file after loading into DataFrame.
- Register a cleanup hook or use `try/finally` around file operations.

**Phase to address:** Upload implementation phase.

---

## Minor Pitfalls

---

### Pitfall 11: Large DataFrames Serialized Into Flask Session Cookie

**What goes wrong:** Developer stores DataFrame or its metadata in `session` (cookie). Flask session is stored client-side by default. Exceeds 4KB cookie limit. Silent cookie truncation causes `KeyError` on retrieval.

**Prevention:** Store only lightweight identifiers (session UUID) in the cookie. Keep all data in server-side cache. Never store DataFrame or column lists directly in `session`.

**Phase to address:** Session/cache design step.

---

### Pitfall 12: MIME Type Not Verified Server-Side

**What goes wrong:** Extension check passes (`secure_filename` gives `.csv`), but the file content is actually an HTML file or executable renamed to `.csv`. Content is passed to pandas, which may parse it in unexpected ways.

**Prevention:** Read the first 512 bytes and verify content is plausibly CSV (check for printable ASCII/UTF-8, presence of delimiter characters). Optionally use `python-magic` for MIME detection. Reject files that fail content validation.

**Phase to address:** Upload validation step.

---

### Pitfall 13: No Feedback on Wizard Progress

**What goes wrong:** Parsing a large CSV (even within size limits) takes 2-10 seconds. No loading indicator. User clicks submit twice, triggering two concurrent parse operations, doubling memory use.

**Prevention:** Disable submit button on first click. Show progress indicator. Consider returning an immediate 202 Accepted with a polling endpoint for large files, though this is likely overkill for local deployment.

**Phase to address:** Upload UX step.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Dependency upgrade | NumPy/Flask/pandas incompatibilities | Upgrade before new features; run existing tests |
| Upload route implementation | Path traversal, unbounded file size | `secure_filename` + `MAX_CONTENT_LENGTH` on day 1 |
| Cache/session design | Global key collision, cookie overflow | UUID-namespaced keys, server-side cache only |
| CSV parse logic | Silent misread, encoding errors | Encoding detection, delimiter negotiation, post-parse validation |
| Data preview UI | XSS via column names/values | `textContent` in JS, auto-escaped Jinja2, CSP header |
| Column selection | Unvalidated parameters | Allowlist from actual `df.columns` |
| Wizard state flow | Expired cache mid-wizard | Guard every step with cache existence check |
| Error handling | Bare exception handlers | Specific exception types, structured logging |

---

## Sources

**Confidence:** MEDIUM for Flask file handling, pandas parsing, and XSS patterns (well-documented, stable knowledge). LOW for anything version-specific to Flask 2.0+ or pandas 2.0+ interactions — verify against current changelogs before implementation.

- Flask documentation on file uploads: https://flask.palletsprojects.com/en/latest/patterns/fileuploads/
- Werkzeug `secure_filename`: https://werkzeug.palletsprojects.com/en/latest/utils/#werkzeug.utils.secure_filename
- Flask `MAX_CONTENT_LENGTH`: Flask config docs
- Pandas CSV parsing docs: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
- Pandas 2.0 migration guide (breaking changes): https://pandas.pydata.org/docs/whatsnew/v2.0.0.html
- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- OWASP XSS Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html

**Note:** All URLs above are based on training knowledge. Verify they resolve to current documentation before citing.
