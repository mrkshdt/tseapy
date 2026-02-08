# Coding Conventions

**Analysis Date:** 2026-02-08

## Naming Patterns

**Files:**
- Lowercase with underscores: `analysis_backends.py`, `moving_average.py`, `test_app_routes.py`
- Task/backend implementations use class name, filename derives from it: `class PeltL2` in `pelt_l2.py`
- Test files prefixed with `test_`: `test_app_routes.py`, `test_tasks.py`, `test_parameters.py`

**Functions:**
- snake_case throughout: `get_data_or_abort()`, `get_visualization_view()`, `validate_dataframe()`
- Private helper functions prefixed with underscore: `_expected_params()`, `_disabled_attr()`
- Task-specific methods follow convention: `do_analysis()`, `get_interaction_script()`, `get_parameter_script()`

**Variables:**
- snake_case: `analysis_backend_factory`, `feature_to_display`, `changepoints`
- Single letters for loops: `a` for analysis backend, `t` for task, `e` for element
- Local imports use abbreviated names for brevity: `import ruptures as rpt`, `from plotly import express as px`

**Types:**
- PascalCase for classes: `Task`, `AnalysisBackend`, `AnalysisBackendsList`, `NumberParameter`
- Abstract base classes use `AnalysisBackendParameter` naming pattern
- Backend implementations: `PeltL2`, `SlidingWindowL2`, `MovingAverage`, `Matrixprofile`, `Mass`

**Constants:**
- HTML strings stored in methods as multiline strings
- Configuration values as instance attributes (not CONSTANT_CASE)

## Code Style

**Formatting:**
- No explicit formatter configured (no `.prettierrc`, `.black`, `.flake8` detected)
- Standard Python spacing: 4 spaces for indentation (implicit, following PEP 8)
- Line continuation in function definitions uses parentheses

**Linting:**
- No linting config detected (no `.pylintrc`, `.eslintrc`, `.flake8` found)
- Code follows implicit PEP 8 conventions

**Docstrings:**
- Single-line docstrings for simple methods: `"""Retrieve cached data or abort with HTTP 400."""`
- Multi-line docstrings with Parameters/Returns sections shown in `tseapy/data/examples.py`:
  ```python
  def validate_dataframe(df: pd.DataFrame):
      """
      Performs a series of checks on the DataFrame df

      Parameters
      ----------
      df : the pandas.DataFrame to be checked

      Returns
      -------

      """
  ```
- Abstract method docstrings often minimal or empty

## Import Organization

**Order:**
1. Standard library imports: `import abc`, `import json`, `import secrets`
2. Third-party imports: `import pandas as pd`, `import plotly.express as px`, `from flask import ...`
3. Local/relative imports: `from tseapy.core.tasks import Task`, `from tseapy.core import create_callback_url`

**Path Aliases:**
- Plotly imported with aliases: `from plotly import express as px`, `import plotly.graph_objects as go`
- Ruptures abbreviated: `import ruptures as rpt`
- Pandas abbreviated: `import pandas as pd`

**Local Imports:**
- Some imports inside function bodies to avoid hard dependencies: `from plotly import express as px` inside `get_visualization_view()` method in `tseapy/core/tasks.py`

## Error Handling

**Patterns:**
- Flask route handlers use `abort()` for error responses: `abort(400, description='No dataset loaded. Please load data first.')`
- Custom error messages descriptive and user-facing: `'Unknown feature column'`, `'Missing query parameter(s): ...'`
- ValueError raised for invalid lookups with formatted strings: `raise ValueError(f'Task "{task}" is unknown')`
- Assertions used for validation in constructors: `assert isinstance(minimum, (int, float, complex)) and not isinstance(minimum, bool)`

**Error Types Used:**
- `ValueError`: For invalid task/algorithm names or lookups
- `TypeError`: For type validation (shown in `tseapy/core/tasks.py`)
- Flask `abort()`: For HTTP error responses with descriptive messages

**Try-Except:**
- Used in error translation: `try: return self.analysis_backend_factory.get_analysis_backend(algo)` catches ValueError and re-raises with task context in `tseapy/core/tasks.py` line 72-75

## Logging

**Framework:** No explicit logging detected

**Patterns:**
- Uses Flask debug mode and print-like behavior via test assertions
- TODO comments indicate incomplete features: `# TODO create a menu + route for setting up data!` in `app.py` line 94

## Comments

**When to Comment:**
- Used sparingly for non-obvious code
- Inline comments explain parsing logic: `# save start and end`, `# gather selected data`, `# Very unprecise solution`
- TODO comments for incomplete features: `# TODO` in `app.py`

**JSDoc/TSDoc:**
- Not used (Python codebase, but some docstrings follow structured format)
- Docstrings document public methods and modules

## Function Design

**Size:** Functions generally 20-50 lines

**Parameters:**
- Explicit parameter lists with type hints where critical: `def get_data_or_abort() -> pd.DataFrame:`
- Default parameters used in class constructors: `onclick: str = ''`, `disabled: bool = False`
- **kwargs used for flexible parameter passing: `def do_analysis(self, data, feature, **kwargs):`

**Return Values:**
- Explicit return types in hints: `-> pd.DataFrame`, `-> str`
- Single return statements per function
- None returns implicit for void functions

## Module Design

**Exports:**
- No explicit `__all__` declarations detected
- Barrel files use standard pattern: `__init__.py` in each package directory imports and re-exports from submodules

**Barrel Files:**
- Found in `tseapy/core/__init__.py` (exports `create_callback_url`)
- Found in `tseapy/tasks/__init__.py` (minimal)
- Task-specific `__init__.py` files contain Task implementations: `tseapy/tasks/change_in_mean/__init__.py` contains `class ChangeInMean(Task)`

**Class Hierarchy:**
- Explicit inheritance from abstract base classes: `class PeltL2(ChangeInMeanBackend):`, `class Matrixprofile(MotifDetectionBackend):`
- Abstract methods marked with `@abc.abstractmethod` decorator
- Backend implementations inherit from `AnalysisBackend` or task-specific backends

## Type Hints

**Usage:**
- Function parameters use type hints selectively: `def get_data_or_abort() -> pd.DataFrame:`
- Constructor parameters use type hints: `def __init__(self, task_name, short_description, long_description):`
- List parameters: `from typing import List`, used as `parameters: List[AnalysisBackendParameter]`

**Enforcement:**
- Not globally enforced (no mypy config detected)
- Used for clarity on critical functions and public APIs

---

*Convention analysis: 2026-02-08*
