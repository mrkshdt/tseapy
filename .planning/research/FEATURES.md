# Feature Landscape: Data Wizard / CSV Upload for tseapy

**Domain:** Time series analysis web platform — data ingestion wizard
**Researched:** 2026-02-08
**Scope:** Subsequent milestone — adding data upload to existing Flask time series analysis app

---

## Table Stakes

Features users expect from any data upload workflow. Missing = product feels broken or unfinished.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| File picker / drag-and-drop upload | Every modern upload UI has this; clicking a button to browse is the minimum | Low | `<input type="file" accept=".csv">` is sufficient; drag-and-drop is additive |
| CSV parsing with delimiter auto-detection | Real-world CSVs use `,` `;` `\t` — hard-coding one delimiter breaks most files | Low-Med | pandas `sep=None, engine='python'` handles most cases; fallback: let user specify |
| Data preview (first N rows) | Users must confirm the file loaded correctly before proceeding | Low | Show first 5–10 rows in an HTML table |
| Column type inference display | User needs to know which columns are numeric vs text vs date | Low | Show inferred dtype per column alongside preview |
| Time/date index column selection | The app requires a datetime index; user must pick which column | Low | Dropdown of columns; parse attempts with `pd.to_datetime()` |
| Value column selection | User picks which numeric column to analyze | Low | Dropdown filtered to numeric columns only |
| Basic error feedback | "File couldn't be parsed" / "No numeric columns found" — not a blank screen | Low | Flash messages or inline error text |
| Confirmation before loading | User sees summary of choices (file name, index col, value col) and clicks "Analyze" | Low | Prevents accidental mis-selection silently corrupting analysis |
| Graceful handling of missing values | Time series with NaN rows shouldn't crash algorithms | Low-Med | `dropna()` or fill strategy; inform user how many rows were dropped |
| Non-CSV rejection | Uploading a PDF or image shows a clear error, not a Python traceback | Low | Validate MIME type and extension before parsing |

## Differentiators

Features that make the wizard better than basic. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Sample data option | Users can try the app without having a CSV ready; reduces drop-off | Low | "Use demo dataset" button that loads the existing Air Quality UCI data |
| Column preview chart (sparkline) | Seeing a mini-chart of each numeric column helps users pick the right one | Med | Small Plotly line chart per candidate column in the column selection step |
| Multiple delimiter support with user override | Auto-detect works for 90% of files; let users fix the 10% | Low | Radio buttons: auto / comma / semicolon / tab |
| Date format hint / override | Dates like `20230101` vs `2023-01-01` vs `01/01/23` need explicit format help | Low-Med | Show detected format string; let user override if wrong |
| File size limit with clear message | Prevents browser hang on 500MB files; sets expectations | Low | Server-side: reject >10MB with friendly message |
| Row count summary | "Loaded 1,247 rows spanning 2020-01-01 to 2023-06-30" builds confidence | Low | Derived from DataFrame after parsing |
| Multi-step wizard UI (stepper) | Upload → Preview → Select Columns → Confirm — keeps context clear | Med | Could be done with simple server-rendered page-per-step flow |
| Persist last-used column selections | If user re-uploads similar data, pre-fill previous column choices | Low | Flask session store; low risk |

## Anti-Features

Features to explicitly NOT build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Multi-file upload / dataset merging | Adds join/concat complexity, not needed for single-column analysis | One file at a time; document this limit |
| Excel (.xlsx) support | Requires `openpyxl`, adds dependency, CSV is sufficient for v1 | Instruct users to export to CSV first |
| Real-time streaming / WebSocket upload progress | Over-engineering for small files; adds async complexity | Simple POST form upload; show loading spinner |
| Auto-detect "best" column for analysis | Fragile heuristics frustrate users when wrong; creates false magic | Always let user explicitly choose columns |
| Data editing in browser | Users have their tools for cleaning data; don't rebuild Excel | Show data problems, tell user to fix upstream |
| Cloud storage integration (S3, Google Drive) | Out of scope for local tool | File system only |
| Data persistence across sessions | Hardcoded in-memory for v1; adds DB complexity | Re-upload next session; document this |
| Column type coercion / transformation UI | Can add later; not needed for minimum working version | Parse as-is; reject non-numeric value columns |
| Authentication / upload history | Single-user local tool | Not needed for v1 |
| CSV injection sanitization in upload feedback | Not a risk on local tool; needed only if export is added | Address when implementing export |

---

## Feature Dependencies

```
File upload (browser form POST)
  └─> Server receives file bytes
        └─> CSV parsing (pandas)
              └─> Delimiter detection
              └─> Data preview (first N rows)
              └─> Column type inference
                    └─> Time column selection (from all columns)
                    └─> Value column selection (filtered to numeric)
                          └─> Datetime parsing of selected time column
                          └─> Validation (monotonic index, no all-NaN column)
                                └─> Cache data in Flask session
                                └─> Redirect to task selection (existing flow)
```

Specific dependencies:
- **Column selection requires preview** — users cannot meaningfully pick columns without seeing the data
- **Value column selection requires column type inference** — filtering to numeric only requires knowing dtypes
- **Redirect to analysis requires successful cache write** — data must be in Flask cache before any task route works
- **Datetime index validation requires successful column selection** — `validate_dataframe()` (already exists in `tseapy/core/validation.py`) must be called after index is set
- **Sample data option bypasses upload entirely** — loads `get_air_quality_uci()` directly, skipping wizard steps

---

## MVP Recommendation

The minimum working wizard that unblocks real use of the app:

**Prioritize (must ship):**
1. File upload form (single POST endpoint, accept `.csv`)
2. CSV parsing with auto-delimiter detection
3. Data preview table (first 10 rows, all columns)
4. Column selection dropdowns (time index + value column)
5. Basic error feedback for parse failures and missing numeric columns
6. Cache loaded DataFrame, redirect to task selection

**Include as quick wins (low complexity, high value):**
7. Sample data / demo dataset option (loads existing Air Quality UCI data)
8. Row count and date range summary after successful load
9. File size limit with friendly message

**Defer:**
- Column preview sparklines (nice but adds Plotly complexity to wizard)
- Date format override UI (auto-detect covers most cases; add when users report problems)
- Multi-step stepper UI (a single page with sections is sufficient for v1)
- Persist last-used columns (session already exists; add after v1 shipped)

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Table stakes | HIGH | Standard web upload UX patterns; existing PROJECT.md requirements align exactly |
| Anti-features | HIGH | PROJECT.md explicitly scopes out several; remainder derived from codebase complexity analysis |
| Differentiators | MEDIUM | Standard patterns from similar tools (Jupyter, Observable, Streamlit upload widgets); verified against project constraints |
| Feature dependencies | HIGH | Derived directly from codebase reading (`validation.py`, `examples.py`, `app.py` cache flow) |

---

## Sources

- Codebase analysis: `/Users/mrkshdt/Documents/New project/tseapy/app.py` — existing data loading, cache, session patterns
- Codebase analysis: `/Users/mrkshdt/Documents/New project/tseapy/tseapy/data/examples.py` — existing CSV parsing approach
- Codebase analysis: `/Users/mrkshdt/Documents/New project/tseapy/tseapy/core/validation.py` — existing validation contract
- Project requirements: `/Users/mrkshdt/Documents/New project/tseapy/.planning/PROJECT.md` — active requirements and out-of-scope decisions
- Codebase concerns: `/Users/mrkshdt/Documents/New project/tseapy/.planning/codebase/CONCERNS.md` — tech debt and missing features audit
- Domain knowledge: Standard CSV upload wizard UX patterns (pandas documentation, web app data ingestion best practices)
