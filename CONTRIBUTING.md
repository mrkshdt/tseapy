# Contributing to tseapy

## Local Setup

```bash
make install
```

This creates `.venv`, upgrades pip, and installs the project as a regular package (the most reliable mode for Python 3.13 CLI entrypoints).

If you specifically need editable mode during development:

```bash
make install-editable
```

## Test Commands

Run unit/integration tests:

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

If your environment cannot reach PyPI:

```bash
make wheel-smoke-offline
```

## Run the App Locally

```bash
make run
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Docker Runtime

Build and run the container:

```bash
docker build -t tseapy:local .
docker run --rm -p 5000:5000 -e TSEAPY_SECRET_KEY=dev-secret tseapy:local
```

Health check endpoint:

```bash
curl http://127.0.0.1:5000/healthz
```
