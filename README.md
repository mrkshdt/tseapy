# tseapy: Time Series Explorative Analysis Python

**tseapy** is an open-source web app for interactive time series analysis. Users can upload CSV data and run built-in algorithms (change detection, pattern recognition, motif detection, smoothing, forecasting, decomposition, frequency analysis) in the browser.

## Quick Start (from source)

Prerequisites:
- Python 3.10+
- pip

```bash
git clone https://github.com/mrkshdt/tseapy.git
cd tseapy
make install
make run
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

If you do not want `make`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install setuptools wheel
python -m pip install --no-build-isolation .
tseapy --host 127.0.0.1 --port 5000 --no-debug
```

For editable installs, use:

```bash
make install-editable
```

## Test and Packaging Commands

Run tests:

```bash
make test
```

Build source and wheel artifacts:

```bash
make build
```

Smoke-test the built wheel in a clean virtual environment:

```bash
make wheel-smoke
```

Offline smoke test (verifies wheel install and CLI entrypoint without downloading dependencies):

```bash
make wheel-smoke-offline
```

Manual equivalents:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m build --no-isolation
python3 -m venv /tmp/tseapy-wheel-test
/tmp/tseapy-wheel-test/bin/pip install dist/*.whl
/tmp/tseapy-wheel-test/bin/tseapy --help
```

## Docker

Build and run:

```bash
docker build -t tseapy:local .
docker run --rm -p 5000:5000 -e TSEAPY_SECRET_KEY=dev-secret tseapy:local
```

Or with compose:

```bash
docker compose up --build
```

Health check endpoint:

```bash
curl http://127.0.0.1:5000/healthz
```

## CLI and WSGI

CLI:

```bash
tseapy --host 0.0.0.0 --port 8000 --debug
```

WSGI:

```bash
gunicorn wsgi:app
```

## Project Structure

- `app.py`: Flask app and routes.
- `tseapy/`: core package code (tasks, data, core abstractions, templates, static assets).
- `tests/`: unit and integration tests.
- `pyproject.toml`: package metadata and build configuration.
- `Dockerfile`: container build for reproducible runtime.
- `RELEASE.md`: release definition-of-done and checklist.
