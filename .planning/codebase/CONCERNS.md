# Codebase Concerns

**Analysis Date:** 2026-02-08

## Tech Debt

**Unimplemented Export Functionality:**
- Issue: `export()` endpoint in `app.py` is a stub raising `NotImplementedError()` with TODO comments for multiple steps (get data, task name, backend name, results). Export feature is blocked.
- Files: `app.py` (lines 195-208)
- Impact: Users cannot export analysis results. The entire export pipeline is non-functional and blocks data exfiltration/persistence workflows.
- Fix approach: Implement the 4 marked TODO steps in sequential order - gather data, resolve task metadata, collect backend metadata with library/version/parameters, format and serialize results.

**Data Loading Hardcoded to Index Route:**
- Issue: Data is always loaded from a hardcoded UCI dataset on the index route (`app.py` line 95), with inline TODO comment `# TODO create a menu + route for setting up data!`. No user control over dataset selection or upload.
- Files: `app.py` (lines 92-102)
- Impact: System is locked to single demo dataset. Cannot analyze custom time series data. Multi-dataset support is entirely missing.
- Fix approach: Create dedicated data upload/selection route. Build file upload form (CSV parsing) and dataset selection menu. Store uploaded datasets in session or temp storage.

**Missing Parameter View Implementation:**
- Issue: Abstract method `get_parameter_view()` is defined in `Task` base class but declared as `@abc.abstractmethod` and never implemented in concrete task classes (`PatternRecognition`, `ChangeInMean`, `MotifDetection`, `Smoothing`). Method referenced but not implemented.
- Files: `tseapy/core/tasks.py` (line 43), `tseapy/tasks/pattern_recognition/__init__.py`, `tseapy/tasks/change_in_mean/__init__.py`, `tseapy/tasks/motif_detection/__init__.py`, `tseapy/tasks/smoothing/__init__.py`
- Impact: Parameter visualization UI is incomplete. Parameter methods exist but render pipeline is broken for all task subclasses.
- Fix approach: Implement `get_parameter_view()` in each task subclass to render parameter HTML views using the parameter objects' `get_view()` methods.

**Incomplete Module - Visualizer Class Unused:**
- Issue: `tseapy/view/visualizer.py` is a 100-line Bokeh visualization class that is never imported or used anywhere in the codebase. Dead code with incomplete methods.
- Files: `tseapy/view/visualizer.py`
- Impact: Dead code increases maintenance burden. Bokeh dependency may be unused. Visualization architecture is unclear (Flask uses Plotly, not Bokeh).
- Fix approach: Either integrate Bokeh visualizer into analysis workflow or remove entirely. Clarify visualization architecture (Plotly vs Bokeh).

**Empty Export Module:**
- Issue: `tseapy/core/export.py` is effectively empty (single line). No export utilities despite export endpoint attempting to use export logic.
- Files: `tseapy/core/export.py`
- Impact: Export functionality has no backing implementation. File serves no purpose and creates confusion about export architecture.
- Fix approach: Either implement export utilities or remove file. Consolidate export logic into a clear module if needed.

**Unused Import in App:**
- Issue: `from tseapy.tasks import motif_detection` is imported at line 12 of `app.py` but never used (line 18 imports `MotifDetection` class instead).
- Files: `app.py` (line 12)
- Impact: Code cleanliness issue. Dead imports increase mental load when reading code.
- Fix approach: Remove unused import statement.

**Unclear Validation Strategy:**
- Issue: `tseapy/core/validation.py` contains validation logic for DataFrame (checking datetime index, monotonic order) but is never called anywhere in the codebase. Validation is effectively unused.
- Files: `tseapy/core/validation.py`, entire codebase
- Impact: Data validation is bypassed. No guarantee that input DataFrames meet requirements. Errors will occur downstream in algorithms.
- Fix approach: Call `validate_dataframe()` in `get_data_or_abort()` or at entry point to ensure data quality contract.

---

## Known Bugs

**Bare Exception Handlers:**
- Symptoms: Silent failures when exceptions occur. Errors are caught and suppressed without logging or propagation.
- Files: `tseapy/view/visualizer.py` (lines 33, 58), `tseapy/tasks/motif_detection/matrixprofile.py` (lines 72, 80)
- Trigger: Any exception during visualization coloring or motif detection slicing triggers silent catch
- Workaround: Add `print()` statements to debug (currently exists in visualizer line 34 but not in matrixprofile). Exception type is lost.
- Specific Issues:
  - Line 33 in visualizer: `except Exception as some:` catches all exceptions and only prints, no re-raise or logging
  - Lines 72, 80 in matrixprofile: bare `except:` catches all exceptions including `KeyboardInterrupt`, `SystemExit` etc.

**Array Indexing Edge Case in Motif Detection:**
- Symptoms: Exception handling in matrixprofile.py indicates array bounds issues when slicing with window size near end of array. Exception caught but resolution unclear.
- Files: `tseapy/tasks/motif_detection/matrixprofile.py` (lines 68-74, 76-82)
- Trigger: When j+width exceeds array length, iloc slicing raises IndexError which is caught
- Workaround: Code attempts to slice from j: to end of array instead (line 73: `iloc[j:]`), but intent is unclear
- Impact: Motif pattern assignment may be truncated or incorrect at array boundaries. Silent exception means bug is hidden.

**Session Key Collision Risk:**
- Symptoms: Single shared cache key `'data'` for all users. Session data stored in simple dictionary without isolation.
- Files: `app.py` (lines 58, 96)
- Trigger: Multiple concurrent users accessing system
- Impact: One user's data overwrites another's in cache. Multi-user isolation is broken. Feature selection (`feature_to_display`) is per-session but data cache is global.
- Severity: High in production, low for single-user demo

**HTML XSS Vulnerability in Parameter Rendering:**
- Symptoms: User input (parameter values from query strings) may be reflected in HTML without escaping
- Files: `tseapy/core/tasks.py` (line 49-65 builds JavaScript with unescaped user input), `tseapy/core/parameters.py` (lines 38-41, 64-67, 88-92 build HTML with unescaped values)
- Trigger: Crafted URL with malicious JavaScript in parameter values
- Example: `/?feature=<img src=x onerror=alert('xss')>`
- Impact: Stored XSS via crafted URLs. Sensitive data theft, session hijacking possible.
- Current Severity: Medium (Flask auto-escapes in templates, but manual HTML building in Python bypasses this)

**Weak Secret Key Generation:**
- Symptoms: Flask secret key generated fresh on every app restart with `secrets.token_hex()` (line 33 of app.py)
- Files: `app.py` (line 33)
- Trigger: Application restart or deployment
- Impact: Session cookies become invalid after restart. Users logged out unexpectedly. More critically, if secret key is logged/exposed, old sessions become vulnerable.
- Fix approach: Generate secret key once at initialization, store in environment variable

---

## Security Considerations

**User Input Validation Missing:**
- Risk: Query parameters from `request.args` are cast directly to types without validation (float, int, string). No range checking, type validation, or safe parsing.
- Files: `app.py` (lines 143-162), `tseapy/tasks/` all task modules
- Current mitigation: Implicit validation via algorithm library (e.g., STUMPY may reject invalid parameters internally)
- Recommendations:
  1. Add whitelist validation for all query parameters before passing to algorithms
  2. Implement parameter bounds checking against AnalysisBackendParameter definitions
  3. Reject unknown parameters early
  4. Use Flask request parsing library (e.g., Flask-RESTful's reqparse)

**Unsafe Float/Int Casting:**
- Risk: Lines like `float(kwargs['penalty'])` and `int(kwargs['width'])` will raise unhandled exceptions with non-numeric input, leaking stack traces to client
- Files: `tseapy/tasks/motif_detection/matrixprofile.py` (lines 50-51), similar patterns in all backends
- Current mitigation: Flask error handler catches 500 errors
- Recommendations: Wrap casting in try-except with informative error messages returned as 400 Bad Request

**Data Path Traversal Risk:**
- Risk: `get_air_quality_uci()` loads CSV from hardcoded relative path `'data/AirQualityUCI.csv'` (line 10 of examples.py). In future if path is parameterized, no validation of path traversal.
- Files: `tseapy/data/examples.py` (line 9)
- Current mitigation: Hardcoded path eliminates current risk
- Recommendations: Validate file paths with `os.path.abspath()` and ensure within whitelisted directory

**CSV Injection in Export:**
- Risk: If export is implemented, exporting data columns with special characters (=, +, @, -) to CSV could trigger formula injection in Excel
- Files: `app.py` (lines 195-208, currently unimplemented)
- Recommendations: When implementing export, sanitize CSV values and use proper CSV library (not string concatenation)

**Dependency Vulnerability:**
- Risk: `requirements.txt` contains several old/vulnerable package versions (see Tech Stack section). No dependency scanning in place.
- Files: `requirements.txt`
- Examples:
  - `numpy==1.21.6` is 1+ years old (current is 2.x), known vulnerabilities may exist
  - `scikit-learn==1.1.1` is outdated (current is 1.5+)
  - `Flask==2.0.3` is 2+ versions old
- Recommendations: Run `pip-audit` in CI/CD, upgrade to latest patch versions, add dependency scanning tool

---

## Performance Bottlenecks

**Inefficient Motif Profile Construction:**
- Problem: Creating NaN DataFrame and then iterating to fill values is inefficient. Double assignment (lines 63-64) and inefficient slicing (iloc with bounds checking via try-except).
- Files: `tseapy/tasks/motif_detection/matrixprofile.py` (lines 59-82)
- Cause: Building DataFrame column-by-column with loop iteration instead of vectorized operations
- Data complexity: O(n*m) where n = array length, m = window width
- Improvement path:
  1. Pre-allocate full arrays before DataFrame creation
  2. Use vectorized NumPy operations (numpy.where, numpy.put) instead of loops
  3. Build DataFrame once at end instead of modifying in place
  4. Example: `result['motif'] = [data[feature].iloc[i:i+width] if motifs[i] else np.nan for i in range(...)]` → use vectorized assignment

**Caching Strategy Limited:**
- Problem: SimpleCache (in-memory) is not suitable for production. All data fits in single cache entry with no expiration strategy for large datasets.
- Files: `app.py` (lines 25-31)
- Cause: CACHE_TYPE = "SimpleCache" is development-only. No Redis/Memcached backend.
- Improvement path:
  1. For production: switch to Redis cache backend
  2. Add per-user cache namespacing (currently global key 'data')
  3. Implement TTL-based expiration
  4. Monitor cache hit rates

**Large DataFrame Memory Footprint:**
- Problem: Entire dataset loaded into memory. No streaming or chunked processing. Air quality dataset is only 1000 rows, but production datasets could be much larger.
- Files: `app.py` (line 95), `tseapy/data/examples.py`
- Cause: All data loaded synchronously into session cache
- Improvement path:
  1. Implement lazy loading / on-demand computation for visualization
  2. Add max dataset size validation
  3. For large datasets, use incremental processing (chunk-based analysis)

**No Query Optimization:**
- Problem: Feature display fetch (line 166-192) reconstructs entire plot data for single feature, even if only time index or single column changed.
- Files: `app.py` (lines 165-192)
- Cause: No delta updates or intelligent caching
- Improvement path: Cache feature plots separately, reuse when possible

---

## Fragile Areas

**Task/Backend Lookup with String Keys:**
- Files: `tseapy/core/tasks.py` (lines 71-75, 89-93), `tseapy/core/analysis_backends.py` (lines 39-42)
- Why fragile: String-based dictionary lookups with ValueError exceptions. If someone changes task name or algo name, routing breaks silently until specific route is hit.
- Safe modification:
  1. Add unit tests for all task/backend name combinations used in routes
  2. Generate task/algo name whitelist at startup
  3. Add validation middleware that checks route parameters against registered tasks
- Test coverage: Tests exist for lookup but not for route integration (no test_app_routes tests task lookup)

**Abstract Method Contract Not Enforced:**
- Files: `tseapy/core/tasks.py` (lines 30-44), task subclasses in `tseapy/tasks/`
- Why fragile: Task base class declares 4 abstract methods but concrete subclasses implement only some. Python allows class instantiation even if abstract methods aren't implemented (unless ABC base class is used correctly). If abstract method is called on incomplete subclass, AttributeError occurs.
- Example: `get_parameter_view()` declared abstract but never implemented in any subclass
- Safe modification:
  1. Inherit from `abc.ABC` instead of just using `@abc.abstractmethod`
  2. Add runtime check in base class `__init__` to verify all methods are overridden
  3. Add integration tests that instantiate all task/backend combinations and call all methods

**Validation Never Called:**
- Files: `tseapy/core/validation.py` (function defined but never called)
- Why fragile: Contract-breaking data (non-datetime index, unsorted times) will silently pass through and fail in algorithm code with unclear errors
- Safe modification:
  1. Call `validate_dataframe(data)` in `get_data_or_abort()` before returning
  2. Add try-except to convert validation errors to 400 Bad Request
  3. Add test for validation enforcement at route level

**Global Variable State in Visualizer:**
- Files: `tseapy/view/visualizer.py` (lines 11-19, 65-90)
- Why fragile: Class attributes `input_global`, `result`, `t_source` are shared mutable state across all instances. Modifying one instance affects all others.
- Safe modification:
  1. Move to instance attributes in `__init__()`
  2. Add unit tests instantiating multiple Visualizer instances concurrently

---

## Scaling Limits

**Single-threaded Flask Development Server:**
- Current capacity: ~1-2 concurrent users with moderate data (1000 rows), ~100ms analysis time
- Limit: Development server blocks on long computations. Analysis endpoints with large datasets will timeout. No async processing.
- Files: `app.py` (line 227, `app.run(debug=True)`)
- Scaling path:
  1. Switch to production WSGI server (Gunicorn with 4-8 workers)
  2. Implement async task queue (Celery + Redis) for long-running analyses
  3. Add background job progress tracking
  4. Set 30s timeout for analysis routes, reject requests exceeding this

**In-memory Cache Unbounded:**
- Current capacity: Entire dataset + visualization cache in RAM. 1000-row dataset = ~1MB, acceptable
- Limit: 10,000-row dataset = ~10MB, 100,000 rows = ~100MB per user. Cache eviction not implemented.
- Scaling path:
  1. Implement LRU cache eviction (cache 5 most recent datasets only)
  2. Add cache size limits per user
  3. Monitor cache memory usage in production

**No Database Persistence:**
- Current capacity: Single session per browser. Loses all state on tab close.
- Limit: Cannot persist user progress, historical analysis, or shared results
- Scaling path:
  1. Add PostgreSQL for user sessions and analysis history
  2. Implement result export to database
  3. Add sharing functionality (public links to results)

---

## Dependencies at Risk

**NumPy 1.21.6 - Critical Upgrade Needed:**
- Risk: 2+ years old, multiple known CVEs and performance regressions fixed in 1.24+. API breaking changes between 1.21 and 2.0 series.
- Impact: Security vulnerabilities in numerical code. Performance degradation. Will break on Python 3.13+ (NumPy 1.21 drops support at Python 3.11).
- Migration plan:
  1. Test upgrade to `numpy>=1.24,<2.0` (stable 1.x series)
  2. Run full test suite to check for API breaking changes
  3. If blocking, upgrade to `numpy>=2.0` and fix breaking changes (minimal expected)

**Scikit-learn 1.1.1 - Outdated:**
- Risk: Current version is 1.5+. 1.1.1 (released Aug 2023) has deprecated APIs removed in 1.4+.
- Impact: Algorithm implementations may use deprecated APIs. May not install on Python 3.13+.
- Migration plan: Upgrade to `scikit-learn>=1.4,<1.6`, test algorithm correctness

**Flask 2.0.3 - Maintenance Mode:**
- Risk: Flask 3.0+ released, 2.0 in maintenance mode. Known vulnerabilities may not be patched.
- Impact: Potential security vulnerabilities in request handling, blueprints.
- Migration plan: Upgrade to `Flask>=3.0` (mostly backward compatible, review migration guide)

**STUMPY 1.11.1 - Unmaintained:**
- Risk: Matrix profile library may have stale dependencies or compatibility issues.
- Impact: Motif detection algorithms depend entirely on this. Any incompatibility in dependencies (NumPy, SciPy) breaks functionality.
- Migration plan: Evaluate alternative libraries (STUMPY fork maintained version, or implement matrix profile from scratch using modern SciPy)

**Duplicate Package Definition:**
- Issue: `requirements.txt` has both `scikit-learn==1.1.1` (line 18) and `sklearn==0.0` (line 21, invalid).
- Impact: `sklearn==0.0` is not a real package and will fail to install. This line should be removed.
- Fix: Remove line 21

---

## Missing Critical Features

**No User Authentication:**
- Problem: No login system, all users share same data cache. No access control, no session isolation beyond browser.
- Blocks: Multi-user deployments, private data analysis, compliance with data privacy regulations
- Impact: System unsafe for shared hosting or cloud deployment

**No Result Persistence:**
- Problem: All analysis results exist only in browser memory. Closing tab loses all work.
- Blocks: Reproducibility, sharing results, audit trails
- Impact: Users cannot save or compare analyses across sessions

**No Data Upload:**
- Problem: Hardcoded to single demo dataset. Cannot analyze custom time series.
- Blocks: Real-world use. Entire system is demo-only.
- Impact: Severely limits applicability

**No Algorithm Parameter Presets:**
- Problem: Users must manually configure parameters each time. No save/load presets.
- Blocks: Workflow efficiency, best practice sharing
- Impact: High friction for iterative analysis

---

## Test Coverage Gaps

**No Flask Route Integration Tests:**
- What's not tested: Full request/response cycle for `/`, `/<task>/<algo>`, `/<task>/<algo>/compute`, `/<task>/<algo>/display-feature`. Error handling at route level.
- Files: `app.py` (entire module), `tests/test_app_routes.py` (34 lines, mostly empty)
- Risk: Routes can be broken by refactoring without test failure. Edge cases like missing query params, invalid feature names not caught until runtime.
- Priority: High (routes are critical path)

**No End-to-End Analysis Tests:**
- What's not tested: Running analysis on actual data with realistic parameters, verifying output structure and values
- Files: All task modules, all backend modules
- Risk: Algorithms may produce incorrect results undetected. Silent failures in analysis chain.
- Priority: High

**No Validation Tests:**
- What's not tested: `validate_dataframe()` function and its integration into data loading pipeline
- Files: `tseapy/core/validation.py`
- Risk: Invalid data passes through validation (it's never called). Hard to detect data quality issues.
- Priority: Medium (would be High if validation were actually used)

**Limited Motif Detection Tests:**
- What's not tested: Edge cases in matrixprofile algorithm (small arrays, window larger than data, NaN handling). Exception handling paths.
- Files: `tseapy/tasks/motif_detection/matrixprofile.py`
- Risk: Algorithm failures with edge case data. Silent exceptions hidden by bare except blocks.
- Priority: Medium

**No Visualizer Tests:**
- What's not tested: Visualizer class methods (unused code, but if activated, no test coverage)
- Files: `tseapy/view/visualizer.py`
- Risk: Code works in development, breaks in production when visualization is invoked
- Priority: Low (code is unused currently)

**Parameter Type Validation Tests Missing:**
- What's not tested: RangeParameter, ListParameter, BooleanParameter initialization with invalid values (min >= max, invalid default, etc.)
- Files: `tseapy/core/parameters.py`, `tests/test_parameters.py` (27 lines, very minimal)
- Risk: Invalid parameter definitions accepted, fail at rendering time in UI
- Priority: Medium

---

## Code Quality Issues

**Unclear Variable Naming:**
- `some` in except clause (visualizer.py:33) - meaningless name obscures what exception occurred
- `tmp` used for temporary swaps (pattern_recognition/__init__.py:90-93, matrixprofile.py:60) - should be more descriptive
- `a`, `t` for task/backend in app.py and task modules - single letter variables reduce readability
- Impact: Code harder to understand and maintain

**Missing Docstrings:**
- Class docstrings are often empty (e.g., `Task` class, `AnalysisBackend` class)
- Function docstrings missing on critical functions (e.g., `perform_analysis()`, `do_analysis()` implementations)
- Impact: API unclear. Developers must read code instead of documentation.

**Inconsistent Error Handling:**
- Some functions raise exceptions (Task.get_visualization_view, AnalysisBackendsList.get_analysis_backend)
- Others use assertions (multiple task.get_analysis_results methods)
- Assertions disable in Python with -O flag, making validation unreliable
- Impact: Unpredictable error handling. Production deployments with -O flag bypass validation.

**SQL-like String Interpolation Pattern:**
- JavaScript generation in `get_parameter_script()` builds strings with manual concatenation prone to injection
- Better: Use template system (Jinja2) for all HTML/JS generation instead of Python f-strings
- Files: `app.py` (line 49-65)

---

## Recommendations Priority

**Critical (Blocks Production):**
1. Fix export endpoint (currently NotImplementedError)
2. Add data upload feature (currently hardcoded single dataset)
3. Implement user authentication and session isolation
4. Fix bare except clauses and add error logging
5. Upgrade NumPy, Flask, scikit-learn to current versions

**High (Significant Issues):**
1. Add parameter validation at routes (security)
2. Implement get_parameter_view() in all task subclasses
3. Call validate_dataframe() in data loading pipeline
4. Add Flask route integration tests
5. Add end-to-end analysis tests
6. Fix XSS vulnerabilities in parameter rendering

**Medium (Technical Debt):**
1. Remove unused Visualizer class or integrate it
2. Refactor motif detection to use vectorized operations
3. Migrate to production WSGI server (Gunicorn)
4. Implement caching with Redis backend
5. Add comprehensive error logging
6. Improve variable naming and docstrings

**Low (Code Quality):**
1. Remove unused imports
2. Use ABC properly for abstract base classes
3. Add type hints throughout
4. Consolidate duplicate package dependencies in requirements.txt

---

*Concerns audit: 2026-02-08*
