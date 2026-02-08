# Architecture

**Analysis Date:** 2026-02-08

## Pattern Overview

**Overall:** Task-Backend Factory Pattern with Layered MVC (Model-View-Controller) for Web Application

**Key Characteristics:**
- Task abstraction layer that decouples analysis algorithms from the web interface
- Backend factory pattern allowing dynamic registration of multiple analysis algorithms per task
- Parameter abstraction system that maps algorithm parameters to HTML form controls
- Visualization layer using Plotly for interactive charts
- Flask-based HTTP routing with client-side JavaScript for interactivity

## Layers

**Presentation Layer:**
- Purpose: Render HTML templates and serve interactive Plotly visualizations
- Location: `app.py`, `/templates`, `/static`
- Contains: Flask routes, HTML templates, CSS styling, client-side JavaScript
- Depends on: Task and AnalysisBackend classes for metadata and parameter definitions
- Used by: Web browser clients

**Task Layer (Business Logic):**
- Purpose: Coordinate task execution by delegating to appropriate analysis backends
- Location: `tseapy/tasks/` subdirectories (`change_in_mean/`, `pattern_recognition/`, `motif_detection/`, `smoothing/`)
- Contains: Task subclasses (ChangeInMean, PatternRecognition, MotifDetection, Smoothing) that implement abstract Task methods
- Depends on: AnalysisBackend classes, parameters, visualization helpers (Plotly)
- Used by: Flask routes in `app.py`

**Backend Layer (Algorithm Implementation):**
- Purpose: Execute specific time series analysis algorithms with configurable parameters
- Location: `tseapy/tasks/*/` algorithm files (e.g., `pelt_l2.py`, `mass.py`, `matrixprofile.py`)
- Contains: Algorithm implementations using external libraries (stumpy, ruptures, sklearn)
- Depends on: Analysis backends, parameters, external scientific libraries
- Used by: Task layer via backend factory pattern

**Core Framework Layer:**
- Purpose: Provide base classes, parameter definitions, and utilities
- Location: `tseapy/core/`
- Contains: `Task`, `AnalysisBackend`, `TasksList`, `AnalysisBackendsList`, parameter classes, callback URL generation
- Depends on: External libraries (Plotly, pandas)
- Used by: All task and backend implementations

**Data Layer:**
- Purpose: Load and provide access to time series datasets
- Location: `tseapy/data/examples.py`
- Contains: Data loading utilities (currently: `get_air_quality_uci()`)
- Depends on: pandas
- Used by: Flask routes for initial data loading

## Data Flow

**Algorithm Discovery and Registration:**

1. `app.py` instantiates task objects (PatternRecognition, ChangeInMean, MotifDetection, Smoothing)
2. Each task creates an `AnalysisBackendsList` factory via `AnalysisBackendFactory` pattern
3. Concrete algorithm backends (Mass, PeltL2, Matrixprofile, MovingAverage) are registered with their parent task
4. All tasks are registered with global `TasksList`

**Request-Response Cycle:**

1. **Navigation** → User clicks task link
   - Route: `GET /<task>` → `display_task(task)`
   - Retrieves task metadata and available algorithms from TasksList
   - Renders `task.html` with algorithm options

2. **Algorithm Selection** → User selects specific algorithm
   - Route: `GET /<task>/<algo>` → `display_algo(task, algo)`
   - Calls `render_algo_template()` which:
     - Gets data visualization via `task.get_visualization_view()`
     - Gets parameter script via `task.get_parameter_script(algo)`
     - Gets interaction script (if any) via `task.get_interaction_script(algo)`
     - Gets interaction view (if any) via `task.get_interaction_view(algo)`
     - Renders `algo.html` with Plotly chart and parameter controls

3. **Analysis Execution** → User submits parameters
   - Route: `GET /<task>/<algo>/compute` → `perform_analysis(task, algo)`
   - Validates required parameters from request args
   - Calls `task.get_analysis_results(data, feature, algo, **request.args)`
   - Task delegates to backend: `backend.do_analysis(data, feature, **kwargs)`
   - Backend returns analysis results (change points, similar patterns, motifs, etc.)
   - Task creates Plotly figure with results overlaid on data
   - Returns JSON-serialized Plotly figure

4. **Feature Switching** → User selects different column to analyze
   - Route: `GET /<task>/<algo>/display-feature` → `display_feature(task, algo)`
   - Updates session with selected feature
   - Returns JSON with updated visualization for new feature

**State Management:**

- **Data**: Cached in Flask session/cache with key 'data'
- **Current Feature**: Stored in Flask session with key 'feature_to_display'
- **Parameters**: Passed via HTTP query string (state is ephemeral per request)
- **Algorithms/Tasks**: Registered in memory at startup; never change during runtime

## Key Abstractions

**Task (Abstract Base Class):**
- Purpose: Represents a time series analysis task (pattern-recognition, change-in-mean, etc.)
- Examples: `ChangeInMean`, `PatternRecognition`, `MotifDetection`, `Smoothing` in `tseapy/tasks/*/`
- Pattern: Each task subclass implements:
  - `get_analysis_results(data, feature, algo, **kwargs)` - Execute analysis via backend
  - `get_interaction_script(algo)` - JavaScript for interactive features (selection, etc.)
  - `get_interaction_view(algo)` - HTML for interaction visualization
  - `get_parameter_view(algo)` - Parameter form rendering (not fully implemented)
- Maintains: Internal `AnalysisBackendsList` factory for managing algorithm variants

**AnalysisBackend (Abstract Base Class):**
- Purpose: Represents a concrete algorithm implementation for a task
- Examples: `Mass`, `PeltL2`, `Matrixprofile`, `MovingAverage` in `tseapy/tasks/*/`
- Pattern: Each backend implements:
  - `do_analysis(data, feature, **kwargs)` - Run the algorithm, return results
- Stores: name, descriptions, callback_url (for frontend), parameters list

**AnalysisBackendParameter (and Subclasses):**
- Purpose: Define input parameters for algorithms with validation and HTML rendering
- Examples: `NumberParameter`, `BooleanParameter`, `RangeParameter`, `ListParameter` in `tseapy/core/parameters.py`
- Pattern: Each parameter type:
  - Validates constraints (min/max for NumberParameter, valid values for ListParameter)
  - Generates HTML form control via `get_view()` method
  - Can be disabled/enabled based on other parameter values

**AnalysisBackendsList & TasksList:**
- Purpose: Factory and registry pattern for dynamic algorithm/task lookup
- Pattern: Dictionary-based lookup by name with error handling for unknown items

## Entry Points

**Web Application Entry Point:**
- Location: `app.py` (lines 226-227)
- Triggers: `python app.py` command
- Responsibilities:
  - Create Flask app instance with caching
  - Register all tasks and algorithms
  - Initialize template context processors
  - Start development server on port 5000

**Flask Routes (HTTP Entry Points):**

1. `GET /` - Index/Home
   - Loads default dataset (Air Quality UCI)
   - Caches data and initializes feature selection
   - Displays task menu

2. `GET /<task>` - Task Display
   - Shows available algorithms for a task

3. `GET /<task>/<algo>` - Algorithm Interface
   - Displays visualization and parameter controls

4. `GET /<task>/<algo>/compute` - Execute Analysis
   - Performs computation with user-provided parameters
   - Returns results as JSON

5. `GET /<task>/<algo>/display-feature` - Switch Feature
   - Updates display for different data column

## Error Handling

**Strategy:** HTTP status codes with JSON error messages

**Patterns:**

- **400 Bad Request** - Missing data, unknown feature, missing parameters
  - Handler: `@app.errorhandler(400)` returns `{'error': description}`
  - Examples:
    - `abort(400, description='No dataset loaded. Please load data first.')` in `get_data_or_abort()`
    - `abort(400, description='Unknown feature column')` when feature not in data
    - `abort(400, description=f"Missing query parameter(s): {', '.join(missing)}")` for validation

- **ValueError** - Unknown task or algorithm
  - Raised by TasksList and AnalysisBackendsList when lookup fails
  - Propagates to HTTP 500 (unhandled)
  - Example: `tasks.get_tasks(task)` line 107 in app.py

- **Assertions** - Input validation
  - Pattern: `assert feature in data.columns` in task methods
  - Purpose: Fail fast on invalid input (would raise AssertionError)
  - Issue: Unhandled assertions become HTTP 500 errors

## Cross-Cutting Concerns

**Logging:** None - no logging framework configured; print() statements used in some code

**Validation:**
- HTTP query parameter validation in `perform_analysis()` via `_expected_params()`
- Pandas data column validation via assertions
- Parameter range validation in parameter classes (min/max constraints)

**Authentication:** None - no user authentication or authorization

**Caching:**
- Flask-Caching with SimpleCache backend
- Cached data stored with key 'data' (configured timeout: 3600 seconds)
- Manual cache.set() and cache.get() calls in routes

**Visualization:**
- Plotly Express for high-level charts (line, heatmap, scatter)
- Plotly Graph Objects for advanced customization (subplots, annotations)
- JSON serialization via `plotly.utils.PlotlyJSONEncoder` for HTTP response

---

*Architecture analysis: 2026-02-08*
