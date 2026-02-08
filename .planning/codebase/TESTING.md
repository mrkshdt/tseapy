# Testing Patterns

**Analysis Date:** 2026-02-08

## Test Framework

**Runner:**
- Python `unittest` (built-in framework)
- No pytest.ini or setup.cfg configuration files
- Tests are discovered and run via standard unittest discovery or direct invocation

**Assertion Library:**
- Built-in `unittest` assertions: `self.assertEqual()`, `self.assertListEqual()`, `self.assertIsInstance()`, `self.assertRaises()`

**Run Commands:**
```bash
python -m unittest discover tests/                    # Run all tests
python -m unittest tests.test_app_routes              # Run specific test module
python -m unittest tests.test_app_routes.test_compute_without_data  # Run specific test
```

## Test File Organization

**Location:**
- Separate directory structure: `/tests/` at project root
- Mirrors package structure: tests for `tseapy/` components in `tests/` directory
- Flask app tests in `tests/test_app_routes.py`, core logic tests in `tests/test_*.py`

**Naming:**
- Test files prefixed with `test_`: `test_app_routes.py`, `test_analysis_backends.py`, `test_tasks.py`, `test_parameters.py`
- Test classes inherit from `unittest.TestCase`
- Test methods prefixed with `test_`: `test_register()`, `test_get_backend()`, `test_compute_without_data()`

**Structure:**
```
tests/
├── __init__.py
├── test_app_routes.py           # Flask route testing
├── test_analysis_backends.py     # Core analysis backend logic
├── test_parameters.py            # Parameter class testing
└── test_tasks.py                 # Task container and logic testing
```

## Test Structure

**Suite Organization:**
```python
from unittest import TestCase

class TestAnalysisBackendsList(TestCase):
    def test_register_creator(self):
        factory = AnalysisBackendsList()
        factory.add_analysis_backend(
            AnalysisBackend(
                'sliding-l2', 'short description', 'long description', 'url', [...]
            )
        )
        self.assertListEqual(
            sorted(list(factory._backends.keys())),
            sorted(['sliding-l1', 'sliding-l2', 'sliding-zscore', 'isolation-forest', 'matrix-profile'])
        )
```

**Patterns:**
- Test class per component: `TestAnalysisBackendsList`, `TestTask`, `TestTasksList`
- Test method per behavior: `test_register()`, `test_get_backend()`, `test_create_callback_url()`
- Setup: Create fresh instances in each test method (no setUp() used)
- Teardown: Implicit; tests are isolated (no tearDown() used)
- Assertion pattern: Direct unittest assertions without helpers

## Mocking

**Framework:** unittest.mock or manual mocking

**Patterns - Flask Route Testing:**
```python
def test_compute_without_data():
    with app.test_client() as client:
        cache.delete('data')
        resp = client.get('/change-in-mean/pelt-l2/compute?penalty=1&min_size=10&jump=5')
        assert resp.status_code == 400
        assert b'No dataset loaded' in resp.data
```

**Patterns - Cache Management:**
```python
def test_compute_missing_params():
    with app.test_client() as client:
        cache.set('data', pd.DataFrame({'f': [1, 2, 3]}, index=pd.date_range('2020', periods=3)))
        resp = client.get('/change-in-mean/pelt-l2/compute?penalty=1&min_size=10')
        assert resp.status_code == 400
```

**What to Mock:**
- Flask request context: Use `app.test_client()` to simulate HTTP requests
- Shared state (cache): Manually set/delete cache entries using `cache.set()` and `cache.delete()`
- External data: Create minimal pandas DataFrames as test fixtures

**What NOT to Mock:**
- Core business logic: `AnalysisBackendsList`, `Task` classes tested directly
- Parameter validation: Tests verify assertion behavior by constructing with invalid inputs
- Query parameter parsing: Flask's `request.args` tested through integration testing

## Fixtures and Factories

**Test Data:**

Flask route tests create minimal DataFrames inline:
```python
cache.set('data', pd.DataFrame({'f': [1, 2, 3]}, index=pd.date_range('2020', periods=3)))
```

Backend tests create parameter objects inline:
```python
AnalysisBackend(
    'sliding-l2', 'short description', 'long description', 'url', [
        RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="", disabled=False)
    ]
)
```

**Location:**
- No separate fixtures module
- Fixtures created locally within test methods for simplicity
- Parameters and objects constructed as needed (no factory or builder patterns)

## Coverage

**Requirements:** No coverage enforcement detected

**View Coverage:**
- No coverage tool configured in project
- No `.coveragerc` or coverage settings in `setup.cfg`/`pyproject.toml`

## Test Types

**Unit Tests:**
- Scope: Individual components in isolation
- Approach: Test class functionality with minimal dependencies
- Examples: `test_register()` in `test_analysis_backends.py` tests `AnalysisBackendsList.add_analysis_backend()` directly
- Coverage:
  - `TestAnalysisBackendsList` (4 tests): `test_register_creator()`, `test_get_backend()`, `test_create_callback_url()`
  - `TestTask` (1 test): `test_get_parameter_script()` validates JavaScript generation
  - `TestTasksList` (2 tests): `test_register()`, `test_get_backend()`
  - `TestAnalysisBackendParameter` (2 tests): `test_range_parameter()`, `test_list_parameter()` verify HTML output

**Integration Tests:**
- Scope: Flask routes with realistic data and cache state
- Approach: Use `app.test_client()` to simulate HTTP requests
- Examples: `test_compute_without_data()` tests error handling when cache is empty
- Coverage:
  - Route error handling: missing data, missing parameters, invalid feature names
  - Cache interaction: verify cache state affects route behavior
  - Parameter validation: routes reject missing required query parameters
  - Feature validation: routes validate feature column names against DataFrame

**E2E Tests:**
- Not used in current codebase
- Manual testing appears to be the approach for full workflows

## Common Patterns

**Async Testing:**
- Not applicable (synchronous Flask app, no async code)

**Error Testing:**

Testing ValueError exceptions:
```python
with self.assertRaises(ValueError) as e:
    factory.get_analysis_backend('sliding-foobar')
    self.assertEquals(str(e), 'Algo "sliding-foobar" is unknown')
```

Testing HTTP errors with assertion library:
```python
def test_compute_without_data():
    with app.test_client() as client:
        cache.delete('data')
        resp = client.get('/change-in-mean/pelt-l2/compute?penalty=1&min_size=10&jump=5')
        assert resp.status_code == 400
        assert b'No dataset loaded' in resp.data
```

**State Management in Tests:**
- Flask `cache` manually manipulated before each test
- No global state carries between tests (each test method creates fresh instances)
- Cache operations: `cache.delete('data')`, `cache.set('data', dataframe)`

## Test Data Patterns

**Minimal DataFrame Construction:**
```python
pd.DataFrame(
    {'f': [1, 2, 3]},
    index=pd.date_range('2020', periods=3)
)
```

**Parameter Construction:**
```python
RangeParameter(
    name='p',
    description='desc',
    minimum=0,
    maximum=10,
    step=1,
    onclick="",
    disabled=False
)
```

**JavaScript Output Validation:**
Tests verify exact string output of JavaScript generation (multiline string comparison):
```python
expected_javascript = """
function doAnalysis() {
    var url = '/task/algo/compute?param1='+param1+'&param2='+param2;
    ...
}
"""
actual_javascript = task.get_parameter_script('algo')
self.assertEqual(expected_javascript, actual_javascript)
```

## Coverage Status

**Current Test Summary:**
- 11 total test methods across 4 test files
- Unit tests: 8 tests (core logic, parameter generation, container management)
- Integration tests: 4 tests (Flask route error handling)
- No E2E tests

**Tested Components:**
- `AnalysisBackendsList`: Registration, retrieval, callback URL generation
- `Task`: Parameter script generation
- `TasksList`: Registration, retrieval
- `AnalysisBackendParameter` subclasses: HTML view generation
- Flask routes: Error handling for missing data, parameters, and invalid features

**Untested/Low Coverage Areas:**
- Actual algorithm execution (`do_analysis()` methods)
- Data processing and analysis results validation
- Visualization generation (Plotly figures)
- Session/feature display persistence
- Export functionality (route not implemented, `raise NotImplementedError()`)

---

*Testing analysis: 2026-02-08*
