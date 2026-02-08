# Codebase Structure

**Analysis Date:** 2026-02-08

## Directory Layout

```
tseapy/
├── app.py                          # Flask application entry point and HTTP routes
├── requirements.txt                # Python package dependencies
├── README.md                       # Project documentation
├── data/                           # Time series datasets and loaders
│   └── AirQualityUCI.csv          # Sample dataset
├── tseapy/                         # Main package
│   ├── __init__.py                # Package marker
│   ├── core/                       # Core framework classes
│   │   ├── __init__.py            # Exports create_callback_url
│   │   ├── tasks.py               # Task and TasksList base classes
│   │   ├── analysis_backends.py   # AnalysisBackend and AnalysisBackendsList classes
│   │   ├── parameters.py          # Parameter classes (NumberParameter, BooleanParameter, etc.)
│   │   ├── validation.py          # Validation utilities (if any)
│   │   └── export.py              # Export functionality (stub, not implemented)
│   ├── tasks/                      # Task implementations by category
│   │   ├── __init__.py
│   │   ├── change_in_mean/        # Changepoint detection task
│   │   │   ├── __init__.py        # ChangeInMean task class
│   │   │   ├── pelt_l2.py         # PELT algorithm backend
│   │   │   └── sliding_window_l2.py # Sliding window algorithm backend
│   │   ├── pattern_recognition/   # Similar pattern finding task
│   │   │   ├── __init__.py        # PatternRecognition task class
│   │   │   └── mass.py            # MASS algorithm backend
│   │   ├── motif_detection/       # Recurring motif detection task
│   │   │   ├── __init__.py        # MotifDetection task class
│   │   │   ├── matrixprofile.py   # Matrix Profile algorithm backend
│   │   │   └── pan_matrixprofile.py # Parallel Matrix Profile backend
│   │   └── smoothing/             # Noise reduction task
│   │       ├── __init__.py        # Smoothing task class
│   │       └── moving_average.py  # Moving Average algorithm backend
│   ├── data/                       # Data loading module
│   │   ├── __init__.py
│   │   └── examples.py            # Data loader functions (get_air_quality_uci)
│   └── view/                       # Visualization module
│       ├── __init__.py
│       └── visualizer.py          # Bokeh-based visualization class (unused)
├── templates/                      # Jinja2 HTML templates
│   ├── index.html                 # Homepage with task menu
│   ├── task.html                  # Task description with algorithm list
│   ├── algo.html                  # Algorithm interface with visualization and controls
│   ├── layouts/                   # Template components
│   │   └── base.html              # Base layout template
│   └── parameters/                # Parameter form templates
│       ├── number.html
│       ├── boolean.html
│       ├── range.html
│       └── list.html
├── static/                         # Static assets
│   └── css/                        # CSS stylesheets
│       └── style.css
└── tests/                          # Unit tests
    ├── __init__.py
    ├── test_tasks.py              # Task class tests
    ├── test_analysis_backends.py  # Backend factory tests
    ├── test_parameters.py         # Parameter class tests
    └── test_app_routes.py         # Flask route tests
```

## Directory Purposes

**Root Directory:**
- Purpose: Application entry point and configuration
- Contains: Flask application, package manifest, dataset sample
- Key files: `app.py`, `requirements.txt`, `README.md`

**tseapy/core/**
- Purpose: Framework foundation - base classes and utilities
- Contains: Task/AnalysisBackend abstractions, parameter system, utilities
- Key files: `tasks.py`, `analysis_backends.py`, `parameters.py`

**tseapy/tasks/**
- Purpose: Task implementations organized by analysis category
- Contains: One subdirectory per task type, each with task class and algorithm backends
- Naming: Subdirectory names match task identifiers (change-in-mean, pattern-recognition)

**tseapy/tasks/change_in_mean/**
- Purpose: Changepoint detection task implementation
- Task identifier: 'change-in-mean'
- Algorithms: 'pelt-l2' (PELT with L2 cost), 'sliding-window-l2' (Sliding window with L2 cost)

**tseapy/tasks/pattern_recognition/**
- Purpose: Similar pattern discovery task implementation
- Task identifier: 'pattern-recognition'
- Algorithms: 'mass' (MASS distance profile)
- Special: Requires user to select pattern region via box selection on visualization

**tseapy/tasks/motif_detection/**
- Purpose: Recurring motif discovery task implementation
- Task identifier: 'motif-detection'
- Algorithms: 'matrixprofile' (Standard Matrix Profile), 'pan-matrixprofile' (Parallel variant)

**tseapy/tasks/smoothing/**
- Purpose: Noise reduction task implementation
- Task identifier: 'smoothing'
- Algorithms: 'moving-average' (Moving average filter)

**tseapy/data/**
- Purpose: Time series data loading and management
- Contains: Data loader functions for external datasets
- Current: Only Air Quality UCI dataset implemented

**tseapy/view/**
- Purpose: Visualization utilities (legacy)
- Status: Bokeh-based visualizer exists but is unused; Plotly used in templates instead

**templates/**
- Purpose: Jinja2 HTML templates for rendering web interface
- Key templates: `index.html` (home), `task.html` (task selection), `algo.html` (algorithm interface)
- Parameter templates: Auto-generated via parameter.get_view() method (not read from files)

**static/css/**
- Purpose: CSS styling for web interface

**tests/**
- Purpose: Unit test suite

## Key File Locations

**Entry Points:**
- `app.py`: Flask application instance, route handlers, global task/algorithm registration
- `tseapy/core/__init__.py`: Exports `create_callback_url()` function

**Configuration:**
- `requirements.txt`: Python package dependencies
- Flask app configuration: Lines 25-34 in `app.py` (caching, secret key)

**Core Logic:**
- `tseapy/core/tasks.py`: Task abstract base class and TasksList registry
- `tseapy/core/analysis_backends.py`: AnalysisBackend abstract base class and AnalysisBackendsList registry
- `tseapy/core/parameters.py`: Parameter abstraction system

**Task Implementations:**
- `tseapy/tasks/<task_name>/__init__.py`: Concrete Task subclass per category
- `tseapy/tasks/<task_name>/<algo_name>.py`: Concrete AnalysisBackend subclass per algorithm

**Testing:**
- `tests/test_tasks.py`: Task behavior tests
- `tests/test_analysis_backends.py`: Backend factory and lookup tests
- `tests/test_parameters.py`: Parameter validation tests
- `tests/test_app_routes.py`: Flask route and integration tests

## Naming Conventions

**Files:**
- Task directories: Kebab-case matching task identifier (change_in_mean → task 'change-in-mean')
- Algorithm files: Snake_case matching algorithm identifier (pelt_l2.py → algo 'pelt-l2')
- Class names: PascalCase (Task, AnalysisBackend, Matrixprofile, PeltL2)
- HTML templates: Snake_case (index.html, algo.html, base.html)

**Directories:**
- Task categories: Snake_case with underscores (change_in_mean, pattern_recognition)
- Organizational modules: Snake_case (core, tasks, data, view, static, templates, tests)

**Identifiers (URLs/Registry Keys):**
- Task names: Kebab-case via 'task_name' parameter to Task.__init__()
  - Examples: 'change-in-mean', 'pattern-recognition', 'motif-detection', 'smoothing'
- Algorithm names: Kebab-case via 'name' parameter to AnalysisBackend.__init__()
  - Examples: 'pelt-l2', 'mass', 'matrixprofile', 'moving-average'

**Python Identifiers:**
- Variables: Snake_case (feature_to_display, data_view, analysis_backend_factory)
- Functions: Snake_case (get_data_or_abort, render_algo_template, perform_analysis)
- Constants: UPPER_SNAKE_CASE (rarely used)

## Where to Add New Code

**New Task (e.g., "Anomaly Detection"):**

1. Create directory: `tseapy/tasks/anomaly_detection/`
2. Create task class file: `tseapy/tasks/anomaly_detection/__init__.py`
   ```python
   from tseapy.core.tasks import Task
   class AnomalyDetection(Task):
       def __init__(self):
           super().__init__(
               'anomaly-detection',
               'Find anomalous data points',
               'Detailed description...'
           )
       # Implement abstract methods: get_analysis_results, get_interaction_script, etc.
   ```

3. Create algorithm backend file: `tseapy/tasks/anomaly_detection/isolation_forest.py`
   ```python
   from tseapy.core.analysis_backends import AnalysisBackend
   class IsolationForest(AnalysisBackend):
       def __init__(self):
           super().__init__(
               'isolation-forest',
               'Isolation Forest algorithm',
               'Uses sklearn implementation',
               create_callback_url('anomaly-detection', 'isolation-forest'),
               parameters=[...]
           )
       def do_analysis(self, data, feature, **kwargs):
           # Implementation
           pass
   ```

4. Register in `app.py`:
   ```python
   from tseapy.tasks.anomaly_detection import AnomalyDetection
   from tseapy.tasks.anomaly_detection.isolation_forest import IsolationForest

   anomaly_detection = AnomalyDetection()
   anomaly_detection.add_analysis_backend(IsolationForest())
   tasks.add_task(anomaly_detection)
   ```

5. Create HTML templates if needed: `templates/tasks/anomaly_detection.html` (optional)

**New Algorithm for Existing Task:**

1. Create algorithm file: `tseapy/tasks/<task>/<algo_name>.py`
2. Implement AnalysisBackend subclass (or task-specific backend base class)
3. Register in `app.py`:
   ```python
   from tseapy.tasks.<task>.<algo_name> import AlgoClassName
   <task_instance>.add_analysis_backend(AlgoClassName())
   ```

**New Parameter Type:**

1. Extend `AnalysisBackendParameter` in `tseapy/core/parameters.py`
2. Implement `get_view()` method to return HTML form control
3. Use in algorithm backends: `parameters=[NewParameterType(...)]`

**Utilities/Helpers:**

- Task-agnostic utilities: `tseapy/core/` (new files in core)
- Data loaders: `tseapy/data/examples.py` (add function)
- Visualization helpers: `tseapy/view/visualizer.py` (currently unused; could extend)

**Tests:**

- Task tests: `tests/test_tasks.py`
- Backend tests: `tests/test_analysis_backends.py`
- Parameter tests: `tests/test_parameters.py`
- Route tests: `tests/test_app_routes.py`

## Special Directories

**data/ (Root Level):**
- Purpose: Contains sample datasets
- Generated: No (committed data files)
- Committed: Yes
- Contents: AirQualityUCI.csv (sample time series data)
- Note: CSV file loaded at application startup in `index.html` route

**.git/**
- Purpose: Git version control metadata
- Generated: Yes (git init/clone)
- Committed: No (git internals)

**.idea/**
- Purpose: PyCharm IDE configuration
- Generated: Yes (PyCharm IDE)
- Committed: No (IDE-specific)

**.planning/ (.planning/codebase/)**
- Purpose: GSD codebase documentation (auto-generated)
- Generated: Yes (by GSD mapping tool)
- Committed: No (documentation only)
- Note: Consumed by GSD planning and execution tools

---

*Structure analysis: 2026-02-08*
