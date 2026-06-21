# Changelog

All notable changes to this project are documented in this file.

The format is inspired by Keep a Changelog.

## [Unreleased]

### Added
- Cross-validation backtesting backend (`forecasting/cross-validation-backtest`):
  rolling-origin (expanding or sliding window) evaluation of multiple forecasting
  methods, with a per-window error chart, forecasts overlaid on the series for each
  window, and a leaderboard report that ranks methods (mean MAE/RMSE/MAPE, win count)
  and auto-selects the recommended model.

### Changed
- Shared forecasting backend selection/run helpers extracted to
  `tseapy/tasks/forecasting/common.py` and reused by the comparison backend.

## [1.2.0a0] - 2026-02-09

### Added
- Python packaging metadata in `pyproject.toml`.
- CLI entrypoint (`tseapy`) and WSGI entrypoint (`wsgi.py`).
- Package-distributed templates and static assets.
- Docker runtime (`Dockerfile`, `docker-compose.yml`).
- CI workflow for tests, build, wheel smoke test, and Docker build.
- Trusted publishing workflows:
  - `publish-testpypi.yml`
  - `publish-pypi.yml`
- Release and maintenance documentation:
  - `RELEASE.md`
  - `CONTRIBUTING.md`
  - `TROUBLESHOOTING.md`
  - `VERSIONING.md`

### Changed
- App bootstrap moved to `create_app(...)` with environment-driven config.
- Debug behavior made explicit through CLI flags and env variables.
- Core abstractions (`Task`, `AnalysisBackend`) formalized as abstract bases.
- Route and packaging tests expanded.

### Fixed
- Export endpoint now returns explicit `501` message instead of unhandled exception.
- Plotly deprecation usage in affected tasks.
- Wheel/package install behavior and runtime path consistency.
