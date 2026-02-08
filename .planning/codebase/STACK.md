# Technology Stack

**Analysis Date:** 2026-02-08

## Languages

**Primary:**
- Python 3.6+ - Web application, data analysis, time series algorithms
- HTML/Jinja2 - Server-side templating for web UI
- CSS - Styling for web interface
- JavaScript - Client-side interactivity in templates

**Secondary:**
- JSON - API request/response serialization

## Runtime

**Environment:**
- Python 3.13.0 (tested)
- Minimum: Python 3.6 (per README)

**Package Manager:**
- pip
- Lockfile: Not present (requirements.txt only)

## Frameworks

**Core:**
- Flask 2.0.3 - Web framework for HTTP routing and request handling
- Flask-Caching 1.10.1 - In-memory caching (SimpleCache)
- Jinja2 3.0.3 - Template rendering engine
- Werkzeug 2.1.2 - WSGI utilities for Flask

**Data Processing:**
- pandas 1.4.2 - DataFrame operations, CSV parsing, data manipulation
- numpy 1.21.6 - Numerical arrays and mathematical operations
- scipy 1.8.0 - Scientific computing functions
- scikit-learn 1.1.1 - Machine learning utilities
- numba 0.55.1 - JIT compilation for numerical code

**Time Series Analysis:**
- stumpy 1.11.1 - Matrix profile computation for motif detection
- ruptures 1.1.6 - Change point detection algorithms

**Visualization:**
- plotly 5.6.0 - Interactive charting library (Plotly JSON encoding for web)
- Pillow 9.0.1 - Image processing
- bokeh - Interactive visualization toolkit (referenced in `tseapy/view/visualizer.py`)

**Performance & Optimization:**
- joblib 1.1.0 - Parallel computing and serialization
- threadpoolctl 3.1.0 - Thread pool management

## Key Dependencies

**Critical:**
- plotly 5.6.0 - Generates interactive visualizations for time series analysis
- pandas 1.4.2 - Core data handling for time series datasets
- numpy 1.21.6 - Numerical computations for algorithms
- Flask 2.0.3 - Web framework for serving UI and API endpoints
- stumpy 1.11.1 - Matrix profile algorithms used in motif detection

**Infrastructure:**
- tornado 6.1 - Async web server (may be used alongside Flask)
- itsdangerous 2.1.2 - Secure session/data signing
- MarkupSafe 2.1.1 - Safe HTML escaping
- click 8.1.3 - CLI utilities
- colorama 0.4.4 - Terminal color output

**Development/Utilities:**
- python-dateutil 2.8.2 - Date/time parsing and manipulation
- pytz 2022.1 - Timezone support
- tenacity 8.0.1 - Retry logic for resilience
- six 1.16.0 - Python 2/3 compatibility utilities
- llvmlite 0.38.0 - LLVM bindings (dependency of numba)

## Configuration

**Environment:**
- Configured at runtime in `app.py`
- Cache config: SimpleCache with 3600 second default timeout
- Debug mode: Set to True in cache config (line 30 in `app.py`)
- Flask secret key: Generated dynamically via `secrets.token_hex()`

**Build:**
- No build configuration files detected
- Application runs directly: `python app.py`
- Uses Flask development server by default

## Platform Requirements

**Development:**
- Python 3.6 or higher
- pip package manager
- Virtual environment recommended (venv)
- No OS-specific dependencies detected

**Production:**
- Python 3.6+ runtime
- Web server (Flask dev server or production WSGI server like Gunicorn/uWSGI)
- Target: Local development/demonstration (no cloud deployment detected)

---

*Stack analysis: 2026-02-08*
